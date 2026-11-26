"""
REQ-6008: API-Endpoints fuer Abdeckungsanzeige (Coverage/Heatmap).

Endpoints:
  GET /api/generations/{gid}/coverage          - t-wise Coverage + Heatmap-Uebersicht
  GET /api/generations/{gid}/coverage/pair     - Detail-Heatmap fuer zwei Kategorien
  GET /api/generations/{gid}/coverage/missing  - Unabgedeckte Tupel (JSON/CSV)
"""
from __future__ import annotations

import csv
import io
import json
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from itertools import combinations

from ..database import get_db
from ..auth_deps import require_api_capable
from .. import models, schemas
from combinatorics.coverage import calculate_coverage, compute_heatmap

router = APIRouter(tags=["API"], dependencies=[Depends(require_api_capable)])

# Version des Cache-Formats in Generation.coverage_meta (bei Aenderung der Berechnung erhoehen)
_CACHE_VERSION = 2


# ---------------------------------------------------------------------------
# BUG K-08: Dauerhafter Cache mit Fingerabdruck des Modells
# ---------------------------------------------------------------------------

def project_fingerprint(db: Session, pid: int) -> str:
    """Fingerabdruck aller Eingaben der Abdeckungsberechnung eines Projekts.

    Aendert sich eine Kategorie, ein Wert, eine Regel oder ein Constraint, aendert
    sich der Fingerabdruck und gespeicherte Abdeckungen werden neu berechnet.
    """
    import hashlib
    cats = db.query(models.Category.id, models.Category.name, models.Category.is_result)         .filter(models.Category.project_id == pid).order_by(models.Category.id).all()
    cat_ids = [c.id for c in cats]
    vals = db.query(models.Value.id, models.Value.category_id, models.Value.value)         .filter(models.Value.category_id.in_(cat_ids)).order_by(models.Value.id).all() if cat_ids else []
    rules = db.query(models.Rule.id, models.Rule.type, models.Rule.if_category_id, models.Rule.if_value,
                     models.Rule.then_category_id, models.Rule.then_value, models.Rule.then_values_json)         .filter(models.Rule.project_id == pid).order_by(models.Rule.id).all()
    cons = db.query(models.Constraint.id, models.Constraint.is_valid, models.Constraint.expression_json)         .filter(models.Constraint.project_id == pid).order_by(models.Constraint.id).all()
    payload = json.dumps([_CACHE_VERSION, [list(r) for r in cats], [list(r) for r in vals],
                          [list(r) for r in rules], [list(r) for r in cons]], default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_cached_coverage(gen: models.Generation, fingerprint: str) -> Optional[dict]:
    """Gespeicherte Abdeckung, wenn sie zum aktuellen Modell passt."""
    if not gen.coverage_meta:
        return None
    try:
        meta = json.loads(gen.coverage_meta)
    except ValueError:
        return None
    if not isinstance(meta, dict) or meta.get("fingerprint") != fingerprint:
        return None
    return meta.get("result")


def _store_coverage(db: Session, gen: models.Generation, fingerprint: str, result: dict) -> None:
    gen.coverage_meta = json.dumps({"fingerprint": fingerprint, "result": result}, ensure_ascii=False)
    db.commit()


def _engine_and_checker(db: Session, pid: int, catmap: Dict[str, List[str]]):
    """Gemeinsame Regel-Engine (wie bei der Generierung) und Machbarkeitspruefung."""
    from .api_generate import build_rule_engine_with_report
    from combinatorics.feasibility import FeasibilityChecker
    engine, _ = build_rule_engine_with_report(db, pid)
    has_rules = any(getattr(engine, a) for a in ("_combine_rules", "_forbidden_rules",
                                                  "_dependency_rules", "_constraint_rules"))
    if not has_rules:
        return None, None
    return engine, FeasibilityChecker(catmap, engine)


# ---------------------------------------------------------------------------
# Helper: Testcases + Kategorien aus DB laden
# ---------------------------------------------------------------------------

def _load_generation_data(db: Session, gen_id: int):
    """Laedt Generierung, Testfaelle und Kategorien."""
    gen = db.get(models.Generation, gen_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )

    # Ergebnis-Kategorien identifizieren
    result_category_names = [c.name for c in categories if c.is_result]

    # Kategorien-Map (ohne Ergebnis-Kategorien)
    catmap: Dict[str, List[str]] = {}
    name_by_id = {c.id: c.name for c in categories}

    all_values = (
        db.query(models.Value)
        .join(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .all()
    )
    for v in all_values:
        cat_name = name_by_id.get(v.category_id)
        if cat_name and cat_name not in result_category_names:
            if cat_name not in catmap:
                catmap[cat_name] = []
            if v.value not in catmap[cat_name]:
                catmap[cat_name].append(v.value)

    # Testcases als Liste von {category_name: value}
    testcases_db = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )

    # Leistung: alle Werte der Generierung in einer Abfrage (frueher eine je Testfall)
    values_by_tc: Dict[int, list] = {}
    for v in (
        db.query(models.TestCaseValue)
        .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCaseValue.id)
    ):
        values_by_tc.setdefault(v.testcase_id, []).append(v)

    testcases: List[Dict[str, str]] = []
    for tc in testcases_db:
        assignment: Dict[str, str] = {}
        for v in values_by_tc.get(tc.id, []):
            cat_name = name_by_id.get(v.category_id)
            if cat_name is None and v.category_name:
                cat_name = v.category_name
            elif cat_name is None:
                cat_name = f"cat#{v.category_id}"
            if cat_name and cat_name not in result_category_names:
                assignment[cat_name] = v.value
        testcases.append(assignment)

    return gen, categories, catmap, testcases, result_category_names, name_by_id, testcases_db


# ---------------------------------------------------------------------------
# GET /api/generations/{gid}/coverage
# ---------------------------------------------------------------------------

def _coverage_dict(c) -> dict:
    return {
        "t": c.t,
        "covered": c.covered,
        "possible": c.possible,
        "percentage": c.percentage,
        "excluded_by_rules": c.excluded_by_rules,
    }


def _tuples_out(tuples) -> list:
    out = []
    for tup in tuples:
        items = sorted(tup)
        out.append({"categories": [i[0] for i in items], "values": [i[1] for i in items]})
    return out


@router.get("/generations/{gid}/coverage")
def get_coverage(
    gid: int,
    t: int = Query(2, ge=1, le=3, description="t-wise Strength (1, 2 oder 3)"),
    db: Session = Depends(get_db),
):
    """REQ-6008: t-wise Coverage fuer eine Generierung berechnen und zurueckgeben.

    Standard: 1-wise und 2-wise. Bei ?t=3 auch 3-wise.
    BUG K-08: Ergebnis wird in der Generierung gespeichert und nur wiederverwendet,
    solange sich Kategorien, Werte, Regeln und Constraints nicht geaendert haben.
    """
    gen = db.get(models.Generation, gid)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")
    fingerprint = project_fingerprint(db, gen.project_id)
    cached = read_cached_coverage(gen, fingerprint)
    if cached is not None and (t < 3 or "coverage_3wise" in cached):
        return {**cached, "cached": True}

    gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)
    rule_engine, checker = _engine_and_checker(db, gen.project_id, catmap)

    if cached is not None:
        result = dict(cached)
    else:
        c1 = calculate_coverage(testcases, catmap, 1, rule_engine, result_names, feasibility=checker)
        c2 = calculate_coverage(testcases, catmap, 2, rule_engine, result_names, feasibility=checker)

        # Heatmap-Uebersicht aller Kategorienpaare
        cat_names = sorted(catmap.keys())
        pairs = []
        for cat_a, cat_b in combinations(cat_names, 2):
            hm = compute_heatmap(cat_a, cat_b, testcases, catmap, rule_engine, feasibility=checker)
            covered_cells = sum(1 for cell in hm.cells.values() if cell.status == "covered")
            excluded_cells = sum(1 for cell in hm.cells.values() if cell.status == "excluded")
            possible = len(hm.rows) * len(hm.cols) - excluded_cells
            pct = round((covered_cells / possible) * 100, 2) if possible > 0 else 0.0
            pairs.append({
                "cat_a": cat_a,
                "cat_b": cat_b,
                "coverage_pct": pct,
                "covered": covered_cells,
                "possible": possible,
            })

        result = {
            "generation_id": gid,
            "coverage_1wise": _coverage_dict(c1),
            "coverage_2wise": _coverage_dict(c2),
            "heatmap": {"categories": cat_names, "pairs": pairs},
            "uncovered_tuples_2wise": _tuples_out(c2.uncovered_tuples),
            "excluded_tuples_2wise": _tuples_out(c2.excluded_tuples),
        }

    if t == 3:
        try:
            result["coverage_3wise"] = _coverage_dict(
                calculate_coverage(testcases, catmap, 3, rule_engine, result_names, feasibility=checker))
        except ValueError as e:  # Groessenpruefung (K-04)
            result["coverage_3wise"] = None
            result["coverage_3wise_error"] = str(e)

    _store_coverage(db, gen, fingerprint, result)
    return {**result, "cached": False}


# ---------------------------------------------------------------------------
# GET /api/generations/{gid}/coverage/pair
# ---------------------------------------------------------------------------

@router.get("/generations/{gid}/coverage/pair")
def get_heatmap_pair(
    gid: int,
    a: str = Query(..., description="Zeilen-Kategorie (cat_a)"),
    b: str = Query(..., description="Spalten-Kategorie (cat_b)"),
    db: Session = Depends(get_db),
):
    """REQ-6008: Detail-Heatmap fuer zwei Kategorien.

    Jede Zelle zeigt die Anzahl der Testfaelle mit diesem Paar,
    den Status (covered/uncovered/excluded) und die TC-IDs.
    """
    gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)

    if a not in catmap:
        raise HTTPException(status_code=400, detail=f"Unbekannte Kategorie: {a}")
    if b not in catmap:
        raise HTTPException(status_code=400, detail=f"Unbekannte Kategorie: {b}")

    rule_engine, checker = _engine_and_checker(db, gen.project_id, catmap)
    hm = compute_heatmap(a, b, testcases, catmap, rule_engine, feasibility=checker)

    # Testfall-IDs je Paar in einem Durchlauf sammeln
    ids_by_pair: Dict[tuple, List[int]] = {}
    for tc, tc_db in zip(testcases, testcases_db):
        ids_by_pair.setdefault((tc.get(a), tc.get(b)), []).append(tc_db.id)

    cells: Dict[str, dict] = {}
    for (row_val, col_val), cell_data in hm.cells.items():
        cells[f"{row_val}-{col_val}"] = {
            "count": cell_data.count,
            "status": cell_data.status,
            "testcase_ids": ids_by_pair.get((row_val, col_val), []),
        }

    return {
        "cat_a": a,
        "cat_b": b,
        "rows": hm.rows,
        "cols": hm.cols,
        "cells": cells,
    }


# ---------------------------------------------------------------------------
# GET /api/generations/{gid}/coverage/missing
# ---------------------------------------------------------------------------

@router.get("/generations/{gid}/coverage/missing")
def get_uncovered_tuples(
    gid: int,
    strength: int = Query(2, ge=1, le=3, alias="t"),
    format: str = Query("json", description="json oder csv"),
    db: Session = Depends(get_db),
):
    """REQ-6008: Liste unabgedeckter Tupel (sortiert, filterbar, exportierbar).

    Bei format=csv: CSV-Download mit Content-Disposition.
    BUG K-04: Zu grosse 3-wise-Anfragen liefern 422 mit Hinweis statt 500.
    """
    if format not in ("json", "csv"):
        raise HTTPException(status_code=422, detail="format muss json oder csv sein")
    gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)
    rule_engine, checker = _engine_and_checker(db, gen.project_id, catmap)

    try:
        c = calculate_coverage(testcases, catmap, strength, rule_engine, result_names, feasibility=checker)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"code": "too_many_combinations", "detail": str(e)})

    tuples_out = _tuples_out(c.uncovered_tuples)

    if format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(["Kategorien", "Werte"])
        for row in tuples_out:
            writer.writerow([", ".join(row["categories"]), ", ".join(row["values"])])
        return Response(
            content=output.getvalue().encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="uncovered_tuples_{gid}.csv"',
            },
        )

    return {
        "generation_id": gid,
        "t": strength,
        "tuples": tuples_out,
        "total": len(tuples_out),
    }
