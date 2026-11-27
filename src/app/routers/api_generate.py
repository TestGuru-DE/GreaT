"""
routers/api_generate.py – G.R.E.A.T. REST-API für Testfall-Generierung und Export.
"""
from __future__ import annotations

import io
import csv
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer, require_scope
from ..api_types import DbId
from .. import models, schemas
from ..config import get_max_testcases, get_max_combinations, get_generation_timeout, get_max_tuples  # REQ-4018: konfigurierbare Obergrenze
from ..export_utils import escape_spreadsheet_value  # B-05: Formel-Injection verhindern
from combinatorics.utils import compute_cartesian_size
from ..services import (
    load_categories_values,
    load_categories_values_weighted,
    load_result_categories,  # REQ-4016
    generate_cases,
    assignment_from_testcase,
    status_for_assignment,
    load_error_values,
    sort_testcases_error_last,
    calculate_generation_risk_summary,
    apply_business_rules,  # B-20/B-21
)
from combinatorics.risk_based import sort_by_risk_descending
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule, ConstraintRule

# REQ-6005 Slice 3: Uebersetzte Spaltenkoepfe fuer Exporte
_EXPORT_HEADERS = {
    "de": {
        "testCaseId": "TC-ID",
        "generationId": "Generierungs-ID",
        "strategy": "Strategie",
        "errorValue": "Fehlerwert",
        "yes": "JA",
        "no": "NEIN",
    },
    "en": {
        "testCaseId": "TC-ID",
        "generationId": "Generation ID",
        "strategy": "Strategy",
        "errorValue": "Error Value",
        "yes": "YES",
        "no": "NO",
    },
}

def _get_export_headers(lang: str = "de") -> dict:
    """Returns translated export column headers for the given language."""
    return _EXPORT_HEADERS.get(lang, _EXPORT_HEADERS["de"])

router = APIRouter(tags=["API"], dependencies=[Depends(require_api_capable)])



def build_rule_engine_with_report(db: Session, pid: int) -> tuple[RuleEngine, list[str]]:
    """REQ-3005/REQ-3040/REQ-6001: Regel-Engine aus Projektregeln + Constraints aufbauen.

    BUG R-05: Liefert zusaetzlich Warnungen fuer Constraints, die NICHT angewendet
    werden (als ungueltig markiert oder nicht auswertbar), statt sie nur zu loggen.
    """
    import logging
    log = logging.getLogger("great.api")

    db_rules = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    categories = db.query(models.Category).filter(models.Category.project_id == pid).all()
    cat_name_by_id = {c.id: c.name for c in categories}
    all_values = db.query(models.Value).filter(
        models.Value.category_id.in_(cat_name_by_id.keys())
    ).all()

    engine_rules = []
    skipped: list[str] = []
    for r in db_rules:
        ic = cat_name_by_id.get(r.if_category_id, "")
        tc_name = cat_name_by_id.get(r.then_category_id, "")
        if r.type == "exclude":
            engine_rules.append(ForbiddenRule(ic, r.if_value, tc_name, r.then_value))
        elif r.type == "dependency":
            engine_rules.append(DependencyRule(ic, r.if_value, tc_name, r.then_value))
        elif r.type == "combine":
            allowed = json.loads(r.then_values_json or "[]")
            engine_rules.append(CombineRule(ic, r.if_value, tc_name, allowed))

    # REQ-6001: Constraints als ConstraintRule
    cat_map: dict[str, int] = {name: cid for cid, name in cat_name_by_id.items()}
    val_map: dict[tuple[int, str], int] = {(v.category_id, v.value): v.id for v in all_values}
    from ..constraints.references import invalid_references
    for c in (db.query(models.Constraint)
              .filter(models.Constraint.project_id == pid)
              .order_by(models.Constraint.name, models.Constraint.id)):
        if not c.is_valid:
            skipped.append(f"Constraint '{c.name}' ist ungueltig (verweist auf geloeschte Kategorie "
                           "oder geloeschten Wert) und wurde nicht angewendet.")
            continue
        try:
            expression = json.loads(c.expression_json)
            problems = invalid_references(db, pid, expression)
            if problems:
                raise ValueError("; ".join(problems))
            engine_rules.append(ConstraintRule(expression=expression, category_map=cat_map, value_map=val_map))
        except Exception as e:  # noqa: BLE001 - jedes Problem wird dem Nutzer gemeldet
            log.warning("Skipping invalid constraint id=%d: %s", c.id, e)
            skipped.append(f"Constraint '{c.name}' ist nicht auswertbar und wurde nicht angewendet.")

    return RuleEngine(engine_rules), skipped


class TestcaseCheckRequest(schemas.BaseModel):
    """REQ-6006 / BUG C-19: (Teil-)Belegung {Kategorie: Wert}."""
    assignment: dict


@router.post("/projects/{pid}/testcases/check")
def check_testcase(pid: DbId, payload: TestcaseCheckRequest, db: Session = Depends(get_db)):
    """REQ-6006 / BUG C-19: Prueft einen manuellen Testfall gegen Regeln und Constraints.

    Liefert die verletzten Regeln/Constraints (sicher verletzt, auch bei Teilbelegung)
    und ob sich die Belegung noch zu einem gueltigen Testfall vervollstaendigen laesst.
    """
    from combinatorics.feasibility import FeasibilityChecker
    from ..services import load_categories_values

    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    assignment = {str(k): str(v) for k, v in payload.assignment.items() if v not in (None, "")}
    catmap = load_categories_values(db, pid)
    unknown = [f"{c}={v}" for c, v in assignment.items() if v not in catmap.get(c, [])]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unbekannte Kategorie oder unbekannter Wert: {', '.join(unknown)}")

    violations: list[str] = []
    names = {c.id: c.name for c in db.query(models.Category).filter(models.Category.project_id == pid)}
    for r in db.query(models.Rule).filter(models.Rule.project_id == pid).order_by(models.Rule.id):
        ic, tc = names.get(r.if_category_id), names.get(r.then_category_id)
        if assignment.get(ic) != r.if_value or tc not in assignment:
            continue
        if r.type == "exclude" and assignment[tc] == r.then_value:
            violations.append(f"Regel: {ic}={r.if_value} schliesst {tc}={r.then_value} aus")
        elif r.type == "dependency" and assignment[tc] != r.then_value:
            violations.append(f"Regel: {ic}={r.if_value} verlangt {tc}={r.then_value}")
        elif r.type == "combine" and assignment[tc] not in json.loads(r.then_values_json or "[]"):
            violations.append(f"Regel: {ic}={r.if_value} erlaubt fuer {tc} nur bestimmte Werte")

    cat_map = {name: cid for cid, name in names.items()}
    val_map = {(v.category_id, v.value): v.id for v in db.query(models.Value).filter(
        models.Value.category_id.in_(cat_map.values()))}
    for c in (db.query(models.Constraint)
              .filter(models.Constraint.project_id == pid, models.Constraint.is_valid == True)  # noqa: E712
              .order_by(models.Constraint.name)):
        rule = ConstraintRule(expression=json.loads(c.expression_json), category_map=cat_map, value_map=val_map)
        if rule.is_violated(assignment):
            violations.append(f"Constraint: {c.name}")

    engine, _ = build_rule_engine_with_report(db, pid)
    completable = not violations and FeasibilityChecker(catmap, engine).is_feasible(assignment)
    return {"valid": not violations, "completable": completable, "violations": violations}


def _build_rule_engine(db: Session, pid: int) -> RuleEngine:
    """Regel-Engine ohne Bericht (siehe build_rule_engine_with_report)."""
    return build_rule_engine_with_report(db, pid)[0]

def _timeout_error(timeout) -> HTTPException:
    """BUG B-03 / N-03: Einheitliche Antwort bei ueberschrittenem Zeitbudget (422 + Code)."""
    return HTTPException(
        status_code=422,
        detail={
            "code": "generation_timeout",
            "detail": f"Die Generierung hat das Zeitlimit von {timeout} s ueberschritten. Bitte Modell verkleinern oder andere Strategie waehlen.",
        },
    )


@router.post("/projects/{pid}/generate", response_model=schemas.GenerateResponse, dependencies=[Depends(require_writer), Depends(require_scope("generate"))])
def generate(
    pid: DbId,
    payload: schemas.GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    export: Optional[str] = Query(None, description="REQ-6012: Ergebnis direkt in diesem Exportformat liefern"),
    persist: bool = Query(True, description="REQ-6012: false = Generierung nicht dauerhaft speichern (nur mit export)"),
    lang: str = Query("de", description="Sprache (de/en) fuer den Export"),
):
    import time as _time

    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # BUG A-09: Komfort-Endpunkt – Parameter vor der Generierung pruefen
    if export is not None:
        if export not in _GENERATE_EXPORT_FORMATS and get_exporter(export) is None:
            raise HTTPException(status_code=422, detail={
                "code": "invalid_export_format", "detail": "Unbekanntes Exportformat"})
        api_auth = getattr(request.state, "api_token_auth", None)
        if api_auth and not api_auth[1].has_scope("export"):
            raise HTTPException(status_code=403, detail="API-Token hat nicht den erforderlichen Scope: export",
                                headers={"X-Error-Code": "insufficient_scope"})
    elif not persist:
        raise HTTPException(status_code=422, detail={
            "code": "persist_requires_export",
            "detail": "persist=false ist nur zusammen mit export moeglich"})

    # limit Validation via Pydantic (ge=1, le=100000) – kein manueller Check mehr

    # BUG B-04: Duplikate vor Generierung pruefen
    from collections import Counter
    all_cats = (
        db.query(models.Category)
        .filter(models.Category.project_id == pid)
        .all()
    )
    cat_names = [c.name.casefold() for c in all_cats]
    duplicates = [name for name, count in Counter(cat_names).items() if count > 1]
    if duplicates:
        raise HTTPException(status_code=409, detail=f"Doppelte Kategorienamen: {', '.join(duplicates)}. Bitte umbenennen.")

    catmap = load_categories_values(db, pid)
    if not catmap or any(len(v) == 0 for v in catmap.values()):
        raise HTTPException(status_code=400, detail="Projekt muss Kategorien und Werte enthalten.")

    # Groessenpruefung vor Generierung
    cat_count = len(catmap)
    total_possible = compute_cartesian_size(catmap)

    # t_strength: field_validator konvertiert None->2, aber bei HTTP-Requests
    # kann das nicht funktionieren; hier expliziter Fallback
    t_strength = payload.t_strength if payload.t_strength is not None else 2

    # Fuer 'all' oder t_wise mit t >= cat_count: kartesisches Produkt-Prüfung
    effective_strategy = payload.strategy
    # t_strength > cat_count gilt nur fuer pairwise/orthogonal (nicht fuer t_wise, da t>=cat_count -> cartesian)
    # "orthogonal": veralteter Alias fuer pairwise, nicht entfernen
    if effective_strategy in ("pairwise", "orthogonal") and t_strength > cat_count:
        raise HTTPException(
            status_code=422,
            detail=f"t_strength ({t_strength}) ueberschreitet Anzahl Kategorien ({cat_count}).",
        )

    if effective_strategy == "all" or (effective_strategy == "t_wise" and t_strength >= cat_count):
        max_comb = get_max_combinations()
        if total_possible > max_comb:
            # BUG N-03: 422 mit stabilem Code statt 409 (409 ist fuer Konflikte reserviert)
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "too_many_combinations",
                    "detail": f"Kartesisches Produkt ({total_possible}) ueberschreitet GREAT_MAX_COMBINATIONS ({max_comb}). Strategie oder Kategorien reduzieren.",
                },
            )

    # BUG B-03: Groessenpruefung auch fuer t-Tupel (T-Wise/Pairwise), bevor gerechnet wird.
    # Begrenzt Laufzeit und Speicher (Abdeckungsziel wird als Tupelmenge aufgebaut).
    if effective_strategy in ("t_wise", "pairwise", "orthogonal"):
        from combinatorics.budget import count_t_tuples
        t_eff = 2 if effective_strategy != "t_wise" else t_strength
        if t_eff < cat_count:
            n_tuples = count_t_tuples(catmap, t_eff)
            max_tuples = get_max_tuples()
            if n_tuples > max_tuples:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "too_many_combinations",
                        "detail": f"Zu viele {t_eff}-Tupel ({n_tuples}) fuer Staerke {t_eff}. Maximal erlaubt: {max_tuples} (GREAT_MAX_TUPLES). Bitte Staerke oder Werte reduzieren.",
                    },
                )

    # Timeout (deadline wird direkt an generate_cases() weitergegeben)
    timeout = get_generation_timeout()
    deadline = _time.time() + timeout

    # BUG B-03: Zeitbudget gilt fuer die gesamte Generierung inkl. Seeds und Regelanwendung.
    from combinatorics.budget import BudgetExceeded, time_budget
    try:
        with time_budget(deadline):
            # REQ-3005/REQ-3040: Regeln VOR der Generierung an die Strategien uebergeben
            rule_engine = None
            skipped_constraints: list[str] = []
            if payload.apply_rules:
                # BUG R-05: nicht angewendete Constraints werden gemeldet
                rule_engine, skipped_constraints = build_rule_engine_with_report(db, pid)

            # REQ-6009: Seed-Generierung oder normale Generierung
            seeds_count = 0
            supplemented_count = 0
            coverage_before = 0.0
            coverage_after = 0.0
            warnings: list[str] = list(skipped_constraints)
            rule_count = len(db.query(models.Rule).filter(models.Rule.project_id == pid).all())

            if payload.seed_set_id or payload.seeds:
                # Seed-Generierung
                from ..services_seed import generate_with_seeds

                try:
                    cases, report, seed_warnings = generate_with_seeds(
                        db, pid, payload.seed_set_id, payload.seeds,
                        payload.strategy, t_strength, rule_engine, deadline,
                    )
                except ValueError as e:  # BUG K-11: unbekannte Strategie
                    raise HTTPException(status_code=422, detail={"code": "invalid_strategy", "detail": str(e)})
                warnings.extend(seed_warnings)
                seeds_count = report.seeds_count
                supplemented_count = report.supplemented_count
                coverage_before = report.coverage_before
                coverage_after = report.coverage_after
            else:
                # Normale Generierung
                cases = generate_cases(
                    catmap, payload.strategy, db=db, project_id=pid,
                    t_strength=t_strength, rule_engine=rule_engine, deadline=deadline,
                )

                # Nach Generierung pruefen, ob Timeout erreicht wurde
                if _time.time() > deadline:
                    raise _timeout_error(timeout)

                # B-20/B-21: Regeln anwenden
                if payload.apply_rules:
                    cases, unreachable_warnings = apply_business_rules(pid, cases, db, catmap=catmap)
                    warnings.extend(unreachable_warnings)
                elif rule_count > 0:
                    rule_word = "Regeln" if rule_count > 1 else "Regel"
                    warnings.append(f"Das Projekt hat {rule_count} {rule_word}, sie wurden nicht angewendet (apply_rules=false).")
                else:
                    if rule_engine is not None:
                        cases = rule_engine.apply(cases)

                # REQ-3034: Risiko-Sortierung
                category_risk_map = load_categories_values_weighted(db, pid)
                cases = sort_by_risk_descending(cases, category_risk_map)

                # BUG-5/REQ-3018: Fehlerwert-Sortierung
                error_values = load_error_values(db, pid)
                cases = sort_testcases_error_last(cases, error_values)
    except BudgetExceeded:
        raise _timeout_error(timeout)

    # REQ-4018: Maximale Anzahl Testfaelle respektieren.
    effective_limit = payload.limit if payload.limit is not None else get_max_testcases()
    truncated = len(cases) > effective_limit
    seed_cases = [c for c in cases if c.get("origin") == "seed"]
    if seed_cases:
        # BUG K-12: Seeds sind Pflicht-Testfaelle und werden nie still abgeschnitten;
        # das Limit begrenzt nur die Ergaenzung.
        others = [c for c in cases if c.get("origin") != "seed"]
        keep = max(0, effective_limit - len(seed_cases))
        if len(seed_cases) > effective_limit:
            warnings.append(
                f"Limit {effective_limit} ist kleiner als die Anzahl der Seeds ({len(seed_cases)}). "
                "Alle Seeds wurden uebernommen, es wurde nichts ergaenzt.")
        elif len(others) > keep:
            warnings.append(
                f"Limit {effective_limit}: {len(others) - keep} ergaenzte Testfaelle wurden nicht uebernommen; "
                "die Abdeckung ist daher unvollstaendig.")
        kept = {id(c) for c in others[:keep]}
        cases = [c for c in cases if c.get("origin") == "seed" or id(c) in kept]
    else:
        cases = cases[:effective_limit]

    gen = models.Generation(
        project_id=pid,
        strategy=payload.strategy,
        seed_set_id=payload.seed_set_id,  # REQ-6009
    )
    db.add(gen)
    db.flush()

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == pid)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )

    for idx, assignment in enumerate(cases, start=1):
        origin = assignment.get("origin")  # REQ-6009
        tc = models.TestCase(
            generation_id=gen.id,
            name=f"TC_{idx}",
            origin=origin,  # REQ-6009: "seed" | "supplemented" | "generated"
        )
        db.add(tc)
        db.flush()

        persisted_assignment = {
            k: v for k, v in assignment.items() if k != "origin"
        }
        for cat in categories:
            if cat.is_result and cat.name not in persisted_assignment:
                persisted_assignment[cat.name] = ""

        for cat in categories:
            if cat.name not in persisted_assignment:
                continue
            db.add(
                models.TestCaseValue(
                    testcase_id=tc.id,
                    category_id=cat.id,
                    category_name=cat.name,  # B-18: Schnappschuss
                    value=persisted_assignment[cat.name],
                )
            )

    if export is not None:
        # BUG A-09: Export aus derselben Sitzung; bei persist=false wird alles verworfen.
        db.flush()
        response = _export_generation(db, gen.id, export, lang)
        if persist:
            db.commit()
        else:
            db.rollback()
        return response

    db.commit()

    return schemas.GenerateResponse(
        generation_id=gen.id,
        count=len(cases),
        total_possible=total_possible,
        truncated=truncated,
        rules_applied=payload.apply_rules,
        rule_count=rule_count,
        warnings=warnings,
        seeds_count=seeds_count,
        supplemented_count=supplemented_count,
        coverage_before=coverage_before,
        coverage_after=coverage_after,
    )


@router.get("/generations/{gid}/testcases", response_model=schemas.TestcasesResponse)
def get_testcases(gid: int, db: Session = Depends(get_db)):
    """REQ-3050 + REQ-3051: Testfälle mit risk_coverage + risk_summary."""
    gen = db.get(models.Generation, gid)
    if gen is None:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    name_by_id = {c.id: c.name for c in categories}

    # REQ-3050: risk_weight-Map laden (value_string -> risk_weight)
    all_values = (
        db.query(models.Value)
        .join(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .all()
    )
    value_risk_map = {v.value: v.risk_weight for v in all_values}

    testcases = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gid)
        .order_by(models.TestCase.id)
        .all()
    )

    # REQ-3063: Fehlerwerte laden für Markierung
    error_values = load_error_values(db, gen.project_id)

    result_categories = load_result_categories(db, gen.project_id)

    # Alle Werte der Generierung in einer Abfrage (frueher eine je Testfall)
    values_by_tc: dict[int, list] = {}
    for value_row in (
        db.query(models.TestCaseValue)
        .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
        .filter(models.TestCase.generation_id == gid)
        .order_by(models.TestCaseValue.id)
    ):
        values_by_tc.setdefault(value_row.testcase_id, []).append(value_row)

    out: List[dict] = []
    for tc in testcases:
        vals = values_by_tc.get(tc.id, [])
        assignments = {category.name: "" for category in categories}
        # B-18: Der gespeicherte Name zaehlt nur fuer GELOESCHTE Kategorien. Eine umbenannte
        # Kategorie ist ueber category_id weiter zugeordnet und erhaelt keine zweite Spalte
        # (frueher: {"Eingabe-neu": "x", "Eingabe": ""}).
        for value_row in vals:
            if value_row.category_id not in name_by_id and value_row.category_name:
                assignments.setdefault(value_row.category_name, "")

        for value_row in vals:
            cat_name = name_by_id.get(value_row.category_id)
            if cat_name is None and value_row.category_name:
                cat_name = value_row.category_name  # B-18: geloeschte Kategorie -> gespeicherter Name
            elif cat_name is None:
                cat_name = f"cat#{value_row.category_id}"  # Fallback wenn beides NULL
            assignments[cat_name] = value_row.value
        has_error = any(v in error_values for v in assignments.values() if v)  # REQ-4016: Ignoriere leere Werte
        
        # REQ-3050: Risikoabdeckung berechnen (Summe der risk_weight, leere Werte = 0)
        risk_coverage = sum(value_risk_map.get(val, 0) if val else 0 for val in assignments.values())
        
        out.append({
            "id": tc.id,
            "name": tc.name,
            "assignments": assignments,
            "has_error_value": has_error,
            "risk_coverage": float(risk_coverage),
            "origin": tc.origin,  # REQ-6009
        })

    # REQ-3051: Generierungsweite Risikoabdeckung berechnen
    category_risk_map = load_categories_values_weighted(db, gen.project_id)
    forbidden_rules = []
    db_rules = db.query(models.Rule).filter(models.Rule.project_id == gen.project_id).all()
    for rule in db_rules:
        if_category_name = name_by_id.get(rule.if_category_id)
        then_category_name = name_by_id.get(rule.then_category_id)
        if not if_category_name or not then_category_name:
            continue

        if rule.type == "exclude":
            forbidden_rules.append((if_category_name, rule.if_value, then_category_name, rule.then_value))
        elif rule.type == "combine":
            allowed = []
            if rule.then_values_json:
                try:
                    allowed = json.loads(rule.then_values_json) or []
                except Exception:
                    allowed = []
            allowed_set = set(allowed)
            then_values = [
                row.value
                for row in db.query(models.Value)
                .filter(models.Value.category_id == rule.then_category_id)
                .order_by(models.Value.order_index, models.Value.id)
                .all()
            ]
            for value in then_values:
                if value not in allowed_set:
                    forbidden_rules.append((if_category_name, rule.if_value, then_category_name, value))

    risk_summary = calculate_generation_risk_summary(
        out,
        value_risk_map,
        len(categories),
        category_risk_map=category_risk_map,
        forbidden_rules=forbidden_rules,
    )

    return {
        "testcases": out,
        "risk_summary": risk_summary,
        "result_categories": result_categories,
    }


@router.patch("/testcases/{tcid}/assignments", response_model=schemas.TestCaseAssignmentUpdateResponse, dependencies=[Depends(require_writer)])
def update_testcase_assignment(
    tcid: DbId,
    payload: schemas.TestCaseAssignmentUpdate,
    db: Session = Depends(get_db),
):
    testcase = db.get(models.TestCase, tcid)
    if testcase is None:
        raise HTTPException(status_code=404, detail="Testfall nicht gefunden")

    generation = db.get(models.Generation, testcase.generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    category = (
        db.query(models.Category)
        .filter(
            models.Category.project_id == generation.project_id,
            models.Category.name == payload.category_name,
        )
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")

    testcase_value = (
        db.query(models.TestCaseValue)
        .filter(
            models.TestCaseValue.testcase_id == tcid,
            models.TestCaseValue.category_id == category.id,
        )
        .first()
    )
    if testcase_value is None:
        testcase_value = models.TestCaseValue(
            testcase_id=tcid,
            category_id=category.id,
            category_name=category.name,  # B-18: Schnappschuss
            value=payload.value,
        )
        db.add(testcase_value)
    else:
        testcase_value.value = payload.value
        # B-18: category_name aktualisieren falls Kategorie umbenannt wurde
        if testcase_value.category_name != category.name:
            testcase_value.category_name = category.name

    db.commit()

    return {
        "testcase_id": tcid,
        "category_name": payload.category_name,
        "value": payload.value,
    }


@router.get("/generations/{gen_id}/export/csv")
def export_generation_csv(
    gen_id: DbId,
    include_status: bool = Query(False, alias="status"),
    encoding: str = Query("utf-8-sig", description="z. B. utf-8-sig, utf-8, cp1252, iso-8859-1, utf-16le, utf-16be, utf-16"),
    excel: bool = Query(True, description="Wenn True: erste Zeile 'sep=;' für Excel"),
    bom: Optional[bool] = Query(None, description="BOM explizit setzen/entfernen; Standard je nach Encoding"),
    lang: str = Query("de", description="Sprache (de/en) fuer Spaltenkoepfe"),
    db: Session = Depends(get_db),
):
    gen = db.get(models.Generation, gen_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    tcs = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )
    cats = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    cat_headers: List[str] = [c.name for c in cats]

    # B-18: Sammle alle Kategorienamen (einschliesslich geloeschter) aus historischen TestCaseValue
    tcv_rows = (
        db.query(models.TestCaseValue.category_name)
        .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
        .filter(models.TestCase.generation_id == gen_id)
        # B-18: nur geloeschte Kategorien; umbenannte sind ueber category_id zugeordnet
        .filter(models.TestCaseValue.category_id.is_(None))
        .distinct()
        .all()
    )
    historical_cat_names = {row[0] for row in tcv_rows if row[0]}
    existing_names = {c.name for c in cats}
    for hname in sorted(historical_cat_names - existing_names):
        cat_headers.append(hname)

    # REQ-3063: Fehlerwert-Spalte im Export
    error_values = load_error_values(db, gen.project_id)

    out = io.StringIO(newline="")
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)

    if excel:
        writer.writerow(["sep=;"])

    exh = _get_export_headers(lang)

    headers = [escape_spreadsheet_value(h) for h in cat_headers] + [  # B-05
        escape_spreadsheet_value(exh["testCaseId"]),
        escape_spreadsheet_value(exh["generationId"]),
        escape_spreadsheet_value(exh["strategy"]),
    ]
    if include_status:
        headers.append("Status")
    headers.append(exh["errorValue"])  # REQ-3063 / REQ-6005
    writer.writerow(headers)

    for tc in tcs:
        a = assignment_from_testcase(db, tc.id)
        row = [escape_spreadsheet_value(a.get(h, "")) for h in cat_headers]  # B-05
        row += [tc.id, gen.id, gen.strategy]
        if include_status:
            row.append(status_for_assignment(gen.project_id, a, db))
        # REQ-3063: Fehlerwert markieren
        has_error = any(v in error_values for v in a.values() if v)
        row.append(exh["yes"] if has_error else exh["no"])
        writer.writerow(row)

    csv_text: str = out.getvalue()

    enc_norm = encoding.lower().strip()
    aliases = {"latin1": "iso-8859-1", "latin-1": "iso-8859-1"}  # B-35
    enc = aliases.get(enc_norm, enc_norm)

    allowed = {"utf-8", "utf-8-sig", "cp1252", "iso-8859-1", "utf-16", "utf-16le", "utf-16be"}
    if enc not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported encoding '{encoding}'. Allowed: {sorted(allowed)}")

    if bom is None:
        bom_default = enc in {"utf-8-sig", "utf-16", "utf-16le", "utf-16be"}
    else:
        bom_default = bool(bom)

    content_charset = enc if enc != "utf-8-sig" else "utf-8"

    if enc == "utf-8-sig":
        data_bytes = csv_text.encode("utf-8-sig")
    elif enc in {"utf-16", "utf-16le", "utf-16be"}:
        data_bytes = csv_text.encode(enc if enc != "utf-16" else "utf-16")
        if bom_default:
            if enc == "utf-16le" and not data_bytes.startswith(b"\xff\xfe"):
                data_bytes = b"\xff\xfe" + data_bytes
            elif enc == "utf-16be" and not data_bytes.startswith(b"\xfe\xff"):
                data_bytes = b"\xfe\xff" + data_bytes
        else:
            if data_bytes.startswith(b"\xff\xfe"):
                data_bytes = data_bytes[2:]
            if data_bytes.startswith(b"\xfe\xff"):
                data_bytes = data_bytes[2:]
    else:
        data_bytes = csv_text.encode(enc, errors="strict")
        if bom_default and enc == "utf-8":
            data_bytes = b"\xef\xbb\xbf" + data_bytes

    filename = f"great_generation_{gen.id}.csv"
    resp_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": f"text/csv; charset={content_charset}",
    }
    return Response(content=data_bytes, headers=resp_headers, media_type=f"text/csv; charset={content_charset}")


# ---------------------------------------------------------------------------
# JSON Export – REQ-1001
# ---------------------------------------------------------------------------

@router.get("/generations/{gen_id}/export/json")
def export_generation_json(
    gen_id: DbId,
    lang: str = Query("de", description="Sprache (de/en), fuer Zukunftserweiterungen"),
    db: Session = Depends(get_db),
):
    """Exportiert alle Testfälle einer Generation als strukturiertes JSON.

    REQ-1001: JSON Export mit project/categories/testcases-Hierarchie.
    REQ-6005: lang-Parameter fuer API-Konsistenz.
    """
    gen = db.get(models.Generation, gen_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    name_by_id = {c.id: c.name for c in categories}

    testcases_db = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )

    # REQ-3063: Fehlerwert-Spalte im Export
    error_values = load_error_values(db, gen.project_id)

    testcases_out: List[dict] = []
    for tc in testcases_db:
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .order_by(models.TestCaseValue.id)
            .all()
        )
        assignments = {}
        for v in vals:
            cat_name = name_by_id.get(v.category_id)
            if cat_name is None and v.category_name:
                cat_name = v.category_name  # B-18
            elif cat_name is None:
                cat_name = f"cat#{v.category_id}"
            assignments[cat_name] = v.value
        # REQ-3063: Fehlerwert markieren
        has_error = any(val in error_values for val in assignments.values() if val)
        testcases_out.append({
            "name": tc.name,
            "assignments": assignments,
            "has_error_value": has_error,
        })

    payload = {
        "generation_id": gen.id,
        "project_id": gen.project_id,
        "strategy": gen.strategy,
        "testcase_count": len(testcases_out),
        "testcases": testcases_out,
    }

    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="great_generation_{gen.id}.json"'},
    )


# ---------------------------------------------------------------------------
# Excel Export – REQ-1002
# ---------------------------------------------------------------------------

@router.get("/generations/{gen_id}/export/xlsx")
def export_generation_xlsx(
    gen_id: DbId,
    lang: str = Query("de", description="Sprache (de/en) fuer Spaltenkoepfe"),
    db: Session = Depends(get_db),
):
    """Exportiert alle Testfälle einer Generation als Excel-Datei (.xlsx).

    REQ-1002: Excel Export mit openpyxl – Kategorien als Spaltenüberschriften.
    REQ-6005: Spaltenkoepfe pro Sprache.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl nicht installiert.")

    gen = db.get(models.Generation, gen_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    cat_headers: List[str] = [c.name for c in categories]
    name_by_id = {c.id: c.name for c in categories}

    # B-18: Sammle alle Kategorienamen (einschliesslich geloeschter) aus historischen TestCaseValue
    tcv_rows_xlsx = (
        db.query(models.TestCaseValue.category_name)
        .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
        .filter(models.TestCase.generation_id == gen_id)
        # B-18: nur geloeschte Kategorien; umbenannte sind ueber category_id zugeordnet
        .filter(models.TestCaseValue.category_id.is_(None))
        .distinct()
        .all()
    )
    historical_cat_names_xlsx = {row[0] for row in tcv_rows_xlsx if row[0]}
    existing_names_xlsx = {c.name for c in categories}
    for hname in sorted(historical_cat_names_xlsx - existing_names_xlsx):
        cat_headers.append(hname)

    testcases_db = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )

    # REQ-3063: Fehlerwert-Spalte im Export
    error_values = load_error_values(db, gen.project_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Generation_{gen.id}"

    # REQ-6005: Spaltenkoepfe pro Sprache
    exh = _get_export_headers(lang)

    # Header-Zeile (fett) – B-05: Formel-Injection verhindern
    headers = cat_headers + [exh["testCaseId"], exh["generationId"], exh["strategy"], exh["errorValue"]]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=escape_spreadsheet_value(header))
        cell.data_type = "s"  # B-05: explizit als String
        cell.font = Font(bold=True)

    # Datenzeilen – B-05: Textwerte escapen, IDs als Zahl belassen
    for row_idx, tc in enumerate(testcases_db, start=2):
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .order_by(models.TestCaseValue.id)
            .all()
        )
        assignments = {}
        for v in vals:
            cat_name = name_by_id.get(v.category_id)
            if cat_name is None and v.category_name:
                cat_name = v.category_name  # B-18
            elif cat_name is None:
                cat_name = f"cat#{v.category_id}"
            assignments[cat_name] = v.value
        row_data = [assignments.get(h, "") for h in cat_headers]
        row_data += [tc.id, gen.id, gen.strategy]
        # REQ-3063: Fehlerwert markieren
        has_error = any(val in error_values for val in assignments.values() if val)
        row_data.append(exh["yes"] if has_error else exh["no"])
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            # B-05: TC-ID (col_idx=cat_count+1) und Generierungs-ID (col_idx=cat_count+2) als Zahl
            if col_idx == len(cat_headers) + 1 or col_idx == len(cat_headers) + 2:
                cell.value = value  # int, unveraendert
            else:
                cell.value = escape_spreadsheet_value(str(value) if not isinstance(value, str) else value)
                cell.data_type = "s"  # B-05: explizit als String

    # In Bytes-Buffer schreiben
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"great_generation_{gen.id}.xlsx"
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(
        content=buffer.read(),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# REQ-6011: Exporte fuer Testmanagement/Automatisierung
# ---------------------------------------------------------------------------

from ..exporters import get_exporter


@router.get("/generations/{gen_id}/export/{format}")
def export_generation_format(
    gen_id: DbId,
    format: str,
    lang: str = Query("en", description="Sprache (de/en) fuer Gherkin"),
    deterministic: bool = Query(False, description="Deterministischer Export (fixes Datum)"),
    values: str | None = Query(None, description="Komma-separierte TC-Namen (Teilmengen-Auswahl)"),
    db: Session = Depends(get_db),
):
    """REQ-6011: Export generation in various formats.

    Supported formats: gherkin, pytest, json-data-driven, robot,
    xray-csv, testrail-csv, azuredevops-csv, markdown.
    """
    exporter = get_exporter(format)
    if not exporter:
        raise HTTPException(404, f"Unknown export format: {format}")

    gen = db.get(models.Generation, gen_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")

    project = db.get(models.Project, gen.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    name_by_id = {c.id: c.name for c in categories}

    testcases_db = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )

    # BUG A-10: Spalten = Kategorien, die in DIESER Generierung belegt sind (unveraenderliche
    # Historie). Noch vorhandene in aktueller Reihenfolge, geloeschte danach (gespeicherter Name);
    # spaeter angelegte Kategorien erscheinen nicht.
    used_ids, deleted_names = set(), []
    for cid, cname in (
        db.query(models.TestCaseValue.category_id, models.TestCaseValue.category_name)
        .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCaseValue.id)
    ):
        if cid in name_by_id:
            used_ids.add(cid)
        else:
            label = cname or f"cat#{cid}"
            if label not in deleted_names:
                deleted_names.append(label)
    used_names = [c.name for c in categories if c.id in used_ids]
    cat_names = used_names + [n for n in deleted_names if n not in used_names]
    result_cats = [c.name for c in categories if c.is_result and c.id in used_ids]

    # REQ-3063: Fehlerwerte
    error_values = load_error_values(db, gen.project_id)

    # Teilmengen-Auswahl
    if values:
        allowed_names = {v.strip() for v in values.split(",")}
        testcases_db = [tc for tc in testcases_db if tc.name in allowed_names]

    # generation_view aufbauen
    from ..version import __version__

    testcases_out: list[dict] = []
    for tc in testcases_db:
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .order_by(models.TestCaseValue.id)
            .all()
        )
        assignments = {}
        for v in vals:
            cat_name = name_by_id.get(v.category_id)
            if cat_name is None and v.category_name:
                cat_name = v.category_name
            elif cat_name is None:
                cat_name = f"cat#{v.category_id}"
            assignments[cat_name] = v.value

        has_error = any(val in error_values for val in assignments.values() if val)
        testcases_out.append({
            "id": tc.id,
            "name": tc.name,
            "assignments": assignments,
            "has_error_value": has_error,
        })

    generation_view = {
        "project_name": project.name,
        "project_id": gen.project_id,
        "generation_id": gen.id,
        "strategy": gen.strategy,
        "name": gen.name or "",
        "created_at": gen.created_at.strftime("%Y-%m-%d") if gen.created_at else "",
        "version": __version__,
        "categories": cat_names,
        "result_categories": result_cats,
        "error_values": sorted(error_values),
        "testcases": testcases_out,
    }

    options = {
        "lang": lang,
        "deterministic": deterministic,
    }

    # BUG A-02: Namen einzeilig machen, bevor sie in Code-/Zeilenformate gelangen
    from ..exporters.base import sanitize_generation_view
    content = exporter.render(sanitize_generation_view(generation_view), options)
    return Response(
        content=content,
        media_type=exporter.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="generation_{gen.id}{exporter.file_extension}"',
        },
    )


# ---------------------------------------------------------------------------
# BUG A-09: Komfort-Endpunkt generate?export=…&persist=…
# ---------------------------------------------------------------------------

_GENERATE_EXPORT_FORMATS = ("csv", "json", "xlsx")


def _export_generation(db: Session, gen_id: int, fmt: str, lang: str):
    """Liefert eine (ggf. noch nicht festgeschriebene) Generierung im Exportformat."""
    if fmt == "csv":
        return export_generation_csv(gen_id, include_status=False, encoding="utf-8-sig",
                                     excel=True, bom=None, lang=lang, db=db)
    if fmt == "json":
        return export_generation_json(gen_id, lang=lang, db=db)
    if fmt == "xlsx":
        return export_generation_xlsx(gen_id, lang=lang, db=db)
    return export_generation_format(gen_id, fmt, lang=lang, deterministic=False, values=None, db=db)
