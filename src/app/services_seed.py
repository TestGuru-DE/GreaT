"""
services_seed.py – G.R.E.A.T. Business-Logic fuer Seed-Management (REQ-6009).

Seed-Satz CRUD, CSV-Import, Validierung, Generierung mit Seeds, Lueckenschluss.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import time
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from combinatorics.coverage import calculate_coverage
from combinatorics.seed_generation import (
    seed_generation,
    validate_seeds,
    fill_partial_seeds,
)
from combinatorics.gap_fill import gap_fill
from combinatorics.seed_report import create_seed_report, create_gap_fill_report, SeedReport
from combinatorics.utils import compute_cartesian_size
from core.rules.rule_engine import RuleEngine

logger = logging.getLogger("great.services.seed")

# REQ-6009: Max 10.000 Seeds pro Satz
MAX_SEEDS = 10000


# ---------------------------------------------------------------------------
# Seed-Satz CRUD
# ---------------------------------------------------------------------------

def create_seed_set(
    db: Session,
    project_id: int,
    name: str,
    seeds: List[Dict[str, Optional[str]]],
    rule_engine: Optional[RuleEngine] = None,
) -> Tuple[models.SeedSet, List[str]]:
    """REQ-6009: Seed-Satz anlegen.

    Returns:
        (seed_set, warnings)
    """
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    if len(seeds) > MAX_SEEDS:
        raise HTTPException(
            status_code=422,
            detail=f"Maximal {MAX_SEEDS} Seeds pro Satz erlaubt.",
        )

    # Duplikat-Pruefung: Name muss pro Projekt eindeutig sein
    existing = (
        db.query(models.SeedSet)
        .filter(
            models.SeedSet.project_id == project_id,
            models.SeedSet.name == name,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Seed-Satz '{name}' existiert bereits in diesem Projekt.",
        )

    # Kategorien fuer Validierung laden
    categories = {}
    for cat in db.query(models.Category).filter(models.Category.project_id == project_id).all():
        values = [v.value for v in db.query(models.Value).filter(models.Value.category_id == cat.id).all()]
        categories[cat.name] = values

    # Validieren
    normalized, warnings = validate_seeds(seeds, categories, rule_engine)

    seed_set = models.SeedSet(
        project_id=project_id,
        name=name,
    )
    db.add(seed_set)
    db.flush()

    for i, seed in enumerate(normalized):
        sc = models.SeedCase(
            seed_set_id=seed_set.id,
            assignment_json=json.dumps(seed, ensure_ascii=False),
            order_index=i,
        )
        db.add(sc)

    db.commit()
    db.refresh(seed_set)
    return seed_set, warnings


def list_seed_sets(db: Session, project_id: int) -> List[models.SeedSet]:
    """REQ-6009: Seed-Saetze eines Projekts auflisten."""
    return (
        db.query(models.SeedSet)
        .filter(models.SeedSet.project_id == project_id)
        .order_by(models.SeedSet.name)
        .all()
    )


def get_seed_set(db: Session, seed_set_id: int, project_id: int) -> models.SeedSet:
    """REQ-6009: Seed-Satz laden (nur wenn zum Projekt gehoerig)."""
    seed_set = (
        db.query(models.SeedSet)
        .filter(
            models.SeedSet.id == seed_set_id,
            models.SeedSet.project_id == project_id,
        )
        .first()
    )
    if not seed_set:
        raise HTTPException(status_code=404, detail="Seed-Satz nicht gefunden")
    return seed_set


def update_seed_set(
    db: Session,
    seed_set_id: int,
    project_id: int,
    name: Optional[str],
    seeds: Optional[List[Dict[str, Optional[str]]]],
    rule_engine: Optional[RuleEngine] = None,
) -> Tuple[models.SeedSet, List[str]]:
    """REQ-6009: Seed-Satz aktualisieren.

    Returns:
        (seed_set, warnings)
    """
    seed_set = get_seed_set(db, seed_set_id, project_id)

    if name is not None:
        # Duplikat-Pruefung
        existing = (
            db.query(models.SeedSet)
            .filter(
                models.SeedSet.project_id == project_id,
                models.SeedSet.name == name,
                models.SeedSet.id != seed_set_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Seed-Satz '{name}' existiert bereits.",
            )
        seed_set.name = name

    if seeds is not None:
        if len(seeds) > MAX_SEEDS:
            raise HTTPException(
                status_code=422,
                detail=f"Maximal {MAX_SEEDS} Seeds pro Satz erlaubt.",
            )

        # Kategorien fuer Validierung laden
        categories = {}
        for cat in db.query(models.Category).filter(models.Category.project_id == project_id).all():
            values = [v.value for v in db.query(models.Value).filter(models.Value.category_id == cat.id).all()]
            categories[cat.name] = values

        # Validieren
        normalized, warnings = validate_seeds(seeds, categories, rule_engine)

        # Alle alten SeedCases loeschen und neue anlegen
        db.query(models.SeedCase).filter(
            models.SeedCase.seed_set_id == seed_set_id
        ).delete(synchronize_session=False)

        for i, seed in enumerate(normalized):
            sc = models.SeedCase(
                seed_set_id=seed_set.id,
                assignment_json=json.dumps(seed, ensure_ascii=False),
                order_index=i,
            )
            db.add(sc)
    else:
        warnings = []

    db.commit()
    db.refresh(seed_set)
    return seed_set, warnings


def delete_seed_set(db: Session, seed_set_id: int, project_id: int) -> None:
    """REQ-6009: Seed-Satz loeschen."""
    seed_set = get_seed_set(db, seed_set_id, project_id)
    db.delete(seed_set)
    db.commit()


# ---------------------------------------------------------------------------
# CSV-Import
# ---------------------------------------------------------------------------

def parse_csv_seeds(
    csv_text: str,
    categories: Dict[str, List[str]],
) -> Tuple[List[Dict[str, Optional[str]]], List[str]]:
    """REQ-6009: CSV-Text parsen und Seeds validieren.

    Returns:
        (seeds, warnings)
    """
    warnings: List[str] = []

    if not csv_text.strip():
        return [], warnings

    # BOM entfernen
    if csv_text.startswith("\ufeff"):
        csv_text = csv_text[1:]

    # Trennzeichen erkennen (Komma oder Semikolon)
    first_line = csv_text.split("\n")[0]
    delimiter = ";" if ";" in first_line else ","

    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    if not reader.fieldnames:
        return [], warnings

    # Unbekannte Spalten melden
    unknown_cols = [c for c in reader.fieldnames if c not in categories]
    for col in unknown_cols:
        warnings.append(f"Unbekannte Spalte '{col}' ignoriert.")

    seeds: List[Dict[str, Optional[str]]] = []
    for row_num, row in enumerate(reader, start=2):
        seed: Dict[str, Optional[str]] = {}
        for cat_name in categories:
            val = row.get(cat_name)
            if val is None or val.strip() == "":
                seed[cat_name] = None
            else:
                seed[cat_name] = val.strip()

        # Unbekannte Werte melden
        for cat_name, val in seed.items():
            if val is not None and val not in categories[cat_name]:
                warnings.append(
                    f"Zeile {row_num}: Wert '{val}' nicht in Kategorie '{cat_name}'."
                )

        seeds.append(seed)

    return seeds, warnings


def import_csv_seeds(
    db: Session,
    project_id: int,
    name: str,
    csv_text: str,
    rule_engine: Optional[RuleEngine] = None,
) -> Tuple[models.SeedSet, List[str]]:
    """REQ-6009: CSV-Import und Seed-Satz anlegen.

    Returns:
        (seed_set, warnings)
    """
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    categories = {}
    for cat in db.query(models.Category).filter(models.Category.project_id == project_id).all():
        values = [v.value for v in db.query(models.Value).filter(models.Value.category_id == cat.id).all()]
        categories[cat.name] = values

    if not categories:
        raise HTTPException(status_code=400, detail="Projekt hat keine Kategorien.")

    # Restbefund 9c: Auch der CSV-Import lehnt doppelte Satznamen ab (wie das Anlegen)
    if db.query(models.SeedSet).filter(models.SeedSet.project_id == project_id,
                                        models.SeedSet.name == name).first():
        raise HTTPException(
            status_code=409,
            detail=f"Seed-Satz '{name}' existiert bereits in diesem Projekt.",
        )

    seeds, warnings = parse_csv_seeds(csv_text, categories)

    if len(seeds) > MAX_SEEDS:
        raise HTTPException(
            status_code=422,
            detail=f"Maximal {MAX_SEEDS} Seeds pro Satz erlaubt. CSV hat {len(seeds)} Zeilen.",
        )

    # Duplikate entfernen
    seen = set()
    unique_seeds = []
    for s in seeds:
        key = tuple(sorted(s.items()))
        if key not in seen:
            seen.add(key)
            unique_seeds.append(s)
    if len(unique_seeds) < len(seeds):
        warnings.append(f"{len(seeds) - len(unique_seeds)} duplizierte Zeile(n) entfernt.")

    seed_set = models.SeedSet(
        project_id=project_id,
        name=name,
    )
    db.add(seed_set)
    db.flush()

    for i, seed in enumerate(unique_seeds):
        sc = models.SeedCase(
            seed_set_id=seed_set.id,
            assignment_json=json.dumps(seed, ensure_ascii=False),
            order_index=i,
        )
        db.add(sc)

    db.commit()
    db.refresh(seed_set)
    return seed_set, warnings


# ---------------------------------------------------------------------------
# Seed-Generierung
# ---------------------------------------------------------------------------

def generate_with_seeds(
    db: Session,
    project_id: int,
    seed_set_id: Optional[int],
    seeds: Optional[List[Dict[str, Optional[str]]]],
    strategy: str,
    t_strength: int = 2,
    rule_engine: Optional[RuleEngine] = None,
    deadline: Optional[float] = None,
) -> Tuple[List[Dict[str, str]], SeedReport, List[str]]:
    """REQ-6009: Generierung mit Seeds.

    Args:
        db: Database session
        project_id: Projekt-ID
        seed_set_id: Optional Seed-Satz-ID aus DB
        seeds: Optional inline-Seed-Liste (wenn keine seed_set_id)
        strategy: Generierungsstrategie
        t_strength: t-Staerke
        rule_engine: Optional RuleEngine
        deadline: Optional Timeout

    Returns:
        (testcases, SeedReport, warnings)
    """
    from .services import load_categories_values, load_categories_values_weighted, load_result_categories, load_error_values, sort_testcases_error_last
    from combinatorics.risk_based import sort_by_risk_descending

    catmap = load_categories_values(db, project_id)
    if not catmap or any(len(v) == 0 for v in catmap.values()):
        raise HTTPException(status_code=400, detail="Projekt muss Kategorien und Werte enthalten.")

    result_categories = load_result_categories(db, project_id)
    result_cat_names = [c.name for c in result_categories]

    # Seeds aus DB oder inline
    seeds_raw: List[Dict[str, Optional[str]]] = []
    if seed_set_id:
        seed_set = db.query(models.SeedSet).filter(
            models.SeedSet.id == seed_set_id,
            models.SeedSet.project_id == project_id,
        ).first()
        if not seed_set:
            raise HTTPException(status_code=404, detail="Seed-Satz nicht gefunden")

        seed_cases = (
            db.query(models.SeedCase)
            .filter(models.SeedCase.seed_set_id == seed_set_id)
            .order_by(models.SeedCase.order_index)
            .all()
        )
        import json as json_mod
        for sc in seed_cases:
            seeds_raw.append(json_mod.loads(sc.assignment_json))
    elif seeds:
        seeds_raw = seeds
    else:
        raise HTTPException(status_code=400, detail="Entweder seed_set_id oder seeds erforderlich.")

    # Validieren
    normalized_seeds, validation_warnings = validate_seeds(seeds_raw, catmap, rule_engine)

    # BUG K-12: Seeds mit Werten, die es im Modell nicht gibt, gelangen nicht in die
    # Generierung (die Warnung aus validate_seeds nennt den Wert).
    usable_seeds = []
    for idx, seed in enumerate(normalized_seeds, start=1):
        unknown = [f"{c}={v}" for c, v in seed.items() if v is not None and v not in catmap.get(c, [])]
        if unknown:
            validation_warnings.append(
                f"Seed {idx} wurde nicht uebernommen: unbekannte Werte ({', '.join(unknown)}).")
        else:
            usable_seeds.append(seed)
    normalized_seeds = usable_seeds

    # Auffuellen
    filled_seeds, filled_fields = fill_partial_seeds(normalized_seeds, catmap, rule_engine)

    # Generieren
    all_tcs, _ = seed_generation(
        filled_seeds,
        catmap,
        strategy,
        t_strength=t_strength,
        rule_engine=rule_engine,
        deadline=deadline,
        result_category_names=result_cat_names,
    )

    # Sortieren (Risiko + Fehlerwert)
    category_risk_map = load_categories_values_weighted(db, project_id)
    all_tcs = sort_by_risk_descending(all_tcs, category_risk_map)

    error_values = load_error_values(db, project_id)
    all_tcs = sort_testcases_error_last(all_tcs, error_values)

    # Report
    report = create_seed_report(
        all_tcs,
        catmap,
        strategy=strategy,
        t_strength=t_strength,
        rule_engine=rule_engine,
        result_category_names=result_cat_names,
        filled_fields=filled_fields,
        warnings=validation_warnings,
    )

    return all_tcs, report, validation_warnings


# ---------------------------------------------------------------------------
# Lueckenschluss
# ---------------------------------------------------------------------------

def gap_fill_generation(
    db: Session,
    project_id: int,
    generation_id: int,
    strategy: str = "pairwise",
    t_strength: int = 2,
    rule_engine: Optional[RuleEngine] = None,
) -> Tuple[List[Dict[str, str]], SeedReport, List[str]]:
    """REQ-6009: Lueckenschluss einer bestehenden Generierung.

    Erzeugt eine NEUE Generierung = alte TCs + Ergaenzung.
    Die alte Generation bleibt unveraendert (Immutable History).

    Returns:
        (new_testcases, SeedReport, warnings)
    """
    from .services import load_categories_values, load_result_categories

    gen = db.get(models.Generation, generation_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")
    if gen.project_id != project_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Generierung")

    catmap = load_categories_values(db, project_id)
    if not catmap or any(len(v) == 0 for v in catmap.values()):
        raise HTTPException(status_code=400, detail="Projekt muss Kategorien und Werte enthalten.")

    result_categories = load_result_categories(db, project_id)
    result_cat_names = [c.name for c in result_categories]

    # Bestehende TCs laden
    testcases = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == generation_id)
        .order_by(models.TestCase.id)
        .all()
    )

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    name_by_id = {c.id: c.name for c in categories}

    existing_assignments: List[Dict[str, str]] = []
    for tc in testcases:
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .all()
        )
        assignment = {}
        for v in vals:
            cat_name = name_by_id.get(v.category_id)
            if cat_name is None and v.category_name:
                cat_name = v.category_name
            elif cat_name is None:
                cat_name = f"cat#{v.category_id}"
            assignment[cat_name] = v.value
        existing_assignments.append(assignment)

    timeout = 60
    deadline = time.time() + timeout

    new_tcs, gap_warnings = gap_fill(
        existing_assignments,
        catmap,
        strategy=strategy,
        t_strength=t_strength,
        rule_engine=rule_engine,
        deadline=deadline,
        result_category_names=result_cat_names,
    )

    if time.time() > deadline:
        raise HTTPException(
            status_code=408,
            detail=f"Lueckenschluss hat Timeout von {timeout}s ueberschritten.",
        )

    # Report
    report = create_gap_fill_report(
        new_tcs,
        existing_assignments,
        catmap,
        strategy=strategy,
        t_strength=t_strength,
        rule_engine=rule_engine,
        result_category_names=result_cat_names,
        warnings=gap_warnings,
    )

    return new_tcs, report, gap_warnings


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def seed_set_to_read(seed_set: models.SeedSet) -> schemas.SeedSetRead:
    """SeedSet-Objekt zu Read-Schema serialisieren."""
    import json as json_mod

    seed_cases = []
    for sc in seed_set.seed_cases:
        seed_cases.append(schemas.SeedCaseRead(
            id=sc.id,
            seed_set_id=sc.seed_set_id,
            assignment=json_mod.loads(sc.assignment_json),
            order_index=sc.order_index,
        ))

    return schemas.SeedSetRead(
        id=seed_set.id,
        project_id=seed_set.project_id,
        name=seed_set.name,
        created_at=seed_set.created_at.isoformat() if seed_set.created_at else "",
        updated_at=seed_set.updated_at.isoformat() if seed_set.updated_at else "",
        seed_cases=seed_cases,
        seed_count=len(seed_cases),
    )


def seed_set_to_list_read(seed_set: models.SeedSet) -> schemas.SeedSetListRead:
    """SeedSet-Objekt zu Kurzinfo-Read-Schema serialisieren."""
    return schemas.SeedSetListRead(
        id=seed_set.id,
        name=seed_set.name,
        seed_count=len(seed_set.seed_cases),
        created_at=seed_set.created_at.isoformat() if seed_set.created_at else "",
    )