"""
routers/api_generate.py – G.R.E.A.T. REST-API für Testfall-Generierung und Export.
"""
from __future__ import annotations

import io
import csv
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer, require_scope
from ..api_types import DbId
from .. import models, schemas
from ..config import get_max_testcases, get_max_combinations, get_generation_timeout  # REQ-4018: konfigurierbare Obergrenze
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



def _build_rule_engine(db: Session, pid: int) -> RuleEngine:
    """REQ-3005/REQ-3040/REQ-6001: Regel-Engine aus Projektregeln + Constraints aufbauen."""
    db_rules = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    categories = db.query(models.Category).filter(models.Category.project_id == pid).all()
    cat_name_by_id = {c.id: c.name for c in categories}

    # REQ-6001: value_id -> value_name Mapping (pro Kategorie)
    all_values = db.query(models.Value).filter(
        models.Value.category_id.in_(cat_name_by_id.keys())
    ).all()
    value_name_by_id: dict[int, str] = {v.id: v.value for v in all_values}
    # Umgekehrtes Mapping: (category_id, value_id) -> value_name
    val_map: dict[tuple[int, int], int] = {}  # (cat_id, val_id) -> val_id (selbst, fuer ConstraintRule)

    engine_rules = []
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

    # REQ-6001: Constraints laden und als ConstraintRule hinzufügen
    constraints = db.query(models.Constraint).filter(
        models.Constraint.project_id == pid,
        models.Constraint.is_valid == True,  # noqa: E712
    ).all()

    for c in constraints:
        import json as json_mod
        try:
            expression = json_mod.loads(c.expression_json)
            # category_map: category_name -> category_id
            # value_map: (category_id, value_name) -> value_id
            cat_map: dict[str, int] = {name: cid for cid, name in cat_name_by_id.items()}
            val_map2: dict[tuple[int, str], int] = {}
            for v in all_values:
                val_map2[(v.category_id, v.value)] = v.id

            engine_rules.append(ConstraintRule(
                expression=expression,
                category_map=cat_map,
                value_map=val_map2,
            ))
        except (json_mod.JSONDecodeError, Exception) as e:
            # Ungueltige Constraints ueberspringen (is_valid=False setzen wuerde besser passen)
            log = __import__("logging").getLogger("great.api")
            log.warning("Skipping invalid constraint id=%d: %s", c.id, e)

    return RuleEngine(engine_rules)

@router.post("/projects/{pid}/generate", response_model=schemas.GenerateResponse, dependencies=[Depends(require_writer), Depends(require_scope("generate"))])
def generate(
    pid: DbId,
    payload: schemas.GenerateRequest,
    db: Session = Depends(get_db),
    export: Optional[str] = None,  # REQ-6012: Komfort-Endpunkt (csv/json)
    persist: bool = True,          # REQ-6012: persist=false = keine dauerhafte Generierung
):
    import time as _time

    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

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
            raise HTTPException(
                status_code=409,
                detail=f"Kartesisches Produkt ({total_possible}) ueberschreitet GREAT_MAX_COMBINATIONS ({max_comb}). Strategie oder Kategorien reduzieren.",
            )

    # Timeout (deadline wird direkt an generate_cases() weitergegeben)
    timeout = get_generation_timeout()
    deadline = _time.time() + timeout

    # REQ-3005/REQ-3040: Regeln VOR der Generierung an die Strategien uebergeben
    rule_engine = None
    if payload.apply_rules:
        rule_engine = _build_rule_engine(db, pid)

    cases = generate_cases(
        catmap, payload.strategy, db=db, project_id=pid,
        t_strength=t_strength, rule_engine=rule_engine, deadline=deadline,
    )

    # Nach Generierung pruefen, ob Timeout erreicht wurde
    if _time.time() > deadline:
        raise HTTPException(
            status_code=408,
            detail=f"Generierung hat Timeout von {timeout}s ueberschritten.",
        )

    # B-20/B-21: Regeln anwenden (ersetzt rule_engine.apply mit apply_business_rules)
    rule_count = len(db.query(models.Rule).filter(models.Rule.project_id == pid).all())
    warnings: list[str] = []

    if payload.apply_rules:
        cases, unreachable_warnings = apply_business_rules(pid, cases, db, catmap=catmap)
        warnings.extend(unreachable_warnings)
    elif rule_count > 0:
        # B-21: Warnung wenn Regeln existieren aber nicht angewendet
        rule_word = "Regeln" if rule_count > 1 else "Regel"
        warnings.append(f"Das Projekt hat {rule_count} {rule_word}, sie wurden nicht angewendet (apply_rules=false).")
    else:
        # Fallback: existing behavior when no rules exist
        if rule_engine is not None:
            cases = rule_engine.apply(cases)

    # REQ-3034: Zuerst nach Risiko absteigend sortieren (von Generierung getrennt)
    category_risk_map = load_categories_values_weighted(db, pid)
    cases = sort_by_risk_descending(cases, category_risk_map)

    # BUG-5/REQ-3018: Fehlerwert-Testfaelle ans Ende sortieren
    error_values = load_error_values(db, pid)
    cases = sort_testcases_error_last(cases, error_values)

    # REQ-4018: Maximale Anzahl Testfaelle respektieren.
    effective_limit = payload.limit if payload.limit is not None else get_max_testcases()
    truncated = len(cases) > effective_limit
    cases = cases[:effective_limit]

    gen = models.Generation(project_id=pid, strategy=payload.strategy)
    db.add(gen)
    db.flush()

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == pid)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )

    for idx, assignment in enumerate(cases, start=1):
        tc = models.TestCase(generation_id=gen.id, name=f"TC_{idx}")
        db.add(tc)
        db.flush()

        persisted_assignment = dict(assignment)
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

    db.commit()

    return schemas.GenerateResponse(
        generation_id=gen.id,
        count=len(cases),
        total_possible=total_possible,
        truncated=truncated,
        rules_applied=payload.apply_rules,
        rule_count=rule_count,
        warnings=warnings,
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

    out: List[dict] = []
    for tc in testcases:
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .order_by(models.TestCaseValue.id)
            .all()
        )
        assignments = {category.name: "" for category in categories}
        # B-18: Sammle auch category_name-Werte aus TestCaseValue fuer geloeschte Kategorien
        all_cat_names = set()
        for value_row in vals:
            if value_row.category_name and value_row.category_name not in name_by_id.values():
                all_cat_names.add(value_row.category_name)
        for cat_name in all_cat_names:
            if cat_name not in assignments:
                assignments[cat_name] = ""

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
                .order_by(models.Value.id)
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
    cat_names = [c.name for c in categories]
    result_cats = [c.name for c in categories if c.is_result]

    testcases_db = (
        db.query(models.TestCase)
        .filter(models.TestCase.generation_id == gen_id)
        .order_by(models.TestCase.id)
        .all()
    )

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

    content = exporter.render(generation_view, options)
    return Response(
        content=content,
        media_type=exporter.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="generation_{gen.id}{exporter.file_extension}"',
        },
    )
