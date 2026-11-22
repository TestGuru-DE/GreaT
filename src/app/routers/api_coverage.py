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
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule

# In-Memory-Cache fuer Coverage-Ergebnisse (pro generation_id)
_coverage_cache: Dict[int, dict] = {}

router = APIRouter(tags=["API"], dependencies=[Depends(require_api_capable)])


# ---------------------------------------------------------------------------
# Helper: RuleEngine aus DB aufbauen (wie in api_generate.py)
# ---------------------------------------------------------------------------

def _build_rule_engine(db: Session, pid: int) -> Optional[RuleEngine]:
    """REQ-6008: Regel-Engine aus Projektregeln + Constraints aufbauen."""
    import logging
    log = logging.getLogger("great.api")

    db_rules = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    constraints = db.query(models.Constraint).filter(
        models.Constraint.project_id == pid,
        models.Constraint.is_valid == True,  # noqa: E712
    ).all()

    if not db_rules and not constraints:
        log.debug("No rules or constraints for project %d", pid)
        return None

    log.debug("Building rule engine for project %d: %d rules, %d constraints", pid, len(db_rules), len(constraints))

    categories = db.query(models.Category).filter(models.Category.project_id == pid).all()
    cat_name_by_id = {c.id: c.name for c in categories}

    all_values = db.query(models.Value).filter(
        models.Value.category_id.in_(cat_name_by_id.keys())
    ).all()

    engine_rules = []
    for r in db_rules:
        ic = cat_name_by_id.get(r.if_category_id, "")
        tc_name = cat_name_by_id.get(r.then_category_id, "")
        if not ic or not tc_name:
            log.warning("Rule %d references unknown category", r.id)
            continue
        if r.type == "exclude":
            engine_rules.append(ForbiddenRule(ic, r.if_value, tc_name, r.then_value))
        elif r.type == "dependency":
            engine_rules.append(DependencyRule(ic, r.if_value, tc_name, r.then_value))
        elif r.type == "combine":
            allowed = json.loads(r.then_values_json or "[]")
            engine_rules.append(CombineRule(ic, r.if_value, tc_name, allowed))

    for c in constraints:
        try:
            from core.rules.rule_engine import ConstraintRule
            expression = json.loads(c.expression_json)
            cat_map = {name: cid for cid, name in cat_name_by_id.items()}
            val_map = {(v.category_id, v.value): v.id for v in all_values}
            engine_rules.append(ConstraintRule(
                expression=expression,
                category_map=cat_map,
                value_map=val_map,
            ))
        except Exception as e:
            log.warning("Skipping invalid constraint %d: %s", c.id, e)

    if not engine_rules:
        return None

    log.debug("Rule engine built with %d rules", len(engine_rules))
    return RuleEngine(engine_rules)


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

    testcases: List[Dict[str, str]] = []
    tc_id_map: Dict[str, List[int]] = {}  # (cat_a_val, cat_b_val) -> [tc_ids]

    for tc in testcases_db:
        vals = (
            db.query(models.TestCaseValue)
            .filter(models.TestCaseValue.testcase_id == tc.id)
            .all()
        )
        assignment: Dict[str, str] = {}
        for v in vals:
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

@router.get("/generations/{gid}/coverage")
def get_coverage(
    gid: int,
    t: int = Query(2, ge=1, le=3, description="t-wise Strength (1, 2 oder 3)"),
    db: Session = Depends(get_db),
):
    """REQ-6008: t-wise Coverage fuer eine Generierung berechnen und zurueckgeben.

    Standard: 1-wise und 2-wise. Bei ?t=3 auch 3-wise.
    Bei aelteren Generierungen: lazy computation beim ersten Abruf.
    """
    # Cache-Check
    if gid in _coverage_cache:
        cached = _coverage_cache[gid].copy()
        cached["cached"] = True
        if t == 3 and "coverage_3wise" not in cached:
            # 3-wise nachberechnen wenn angefragt
            gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)
            rule_engine = _build_rule_engine(db, gen.project_id)
            try:
                c3 = calculate_coverage(testcases, catmap, 3, rule_engine, result_names)
                cached["coverage_3wise"] = {
                    "t": c3.t,
                    "covered": c3.covered,
                    "possible": c3.possible,
                    "percentage": c3.percentage,
                    "excluded_by_rules": c3.excluded_by_rules,
                }
            except ValueError:
                cached["coverage_3wise"] = None
        return cached

    gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)
    rule_engine = _build_rule_engine(db, gen.project_id)

    # 1-wise
    c1 = calculate_coverage(testcases, catmap, 1, rule_engine, result_names)

    # 2-wise
    c2 = calculate_coverage(testcases, catmap, 2, rule_engine, result_names)

    # Heatmap-Uebersicht aller Kategorienpaare
    cat_names = sorted(catmap.keys())
    pairs = []
    for cat_a, cat_b in combinations(cat_names, 2):
        hm = compute_heatmap(cat_a, cat_b, testcases, catmap, rule_engine)
        total_cells = len(hm.rows) * len(hm.cols)
        covered_cells = sum(
            1 for cell in hm.cells.values() if cell.status == "covered"
        )
        # Excluded cells don't count toward possible
        excluded_cells = sum(
            1 for cell in hm.cells.values() if cell.status == "excluded"
        )
        possible = total_cells - excluded_cells
        pct = round((covered_cells / possible) * 100, 2) if possible > 0 else 0.0
        pairs.append({
            "cat_a": cat_a,
            "cat_b": cat_b,
            "coverage_pct": pct,
            "covered": covered_cells,
            "possible": possible,
        })

    # Unabgedeckte 2-wise Tupel (serialisiert)
    uncovered_2wise = []
    for tup in c2.uncovered_tuples:
        # frozenset von (cat, val) Paaren -> lesbares Format
        items = sorted(tup)
        uncovered_2wise.append({
            "categories": [item[0] for item in items],
            "values": [item[1] for item in items],
        })

    result = {
        "generation_id": gid,
        "coverage_1wise": {
            "t": c1.t,
            "covered": c1.covered,
            "possible": c1.possible,
            "percentage": c1.percentage,
            "excluded_by_rules": c1.excluded_by_rules,
        },
        "coverage_2wise": {
            "t": c2.t,
            "covered": c2.covered,
            "possible": c2.possible,
            "percentage": c2.percentage,
            "excluded_by_rules": c2.excluded_by_rules,
        },
        "heatmap": {
            "categories": cat_names,
            "pairs": pairs,
        },
        "uncovered_tuples_2wise": uncovered_2wise,
        "cached": False,
    }

    # Optional 3-wise
    if t == 3:
        try:
            c3 = calculate_coverage(testcases, catmap, 3, rule_engine, result_names)
            result["coverage_3wise"] = {
                "t": c3.t,
                "covered": c3.covered,
                "possible": c3.possible,
                "percentage": c3.percentage,
                "excluded_by_rules": c3.excluded_by_rules,
            }
        except ValueError as e:
            result["coverage_3wise"] = None
            result["coverage_3wise_error"] = str(e)

    # Cache speichern
    _coverage_cache[gid] = result.copy()

    return result


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
    rule_engine = _build_rule_engine(db, gen.project_id)

    if a not in catmap:
        raise HTTPException(status_code=400, detail=f"Unbekannte Kategorie: {a}")
    if b not in catmap:
        raise HTTPException(status_code=400, detail=f"Unbekannte Kategorie: {b}")

    hm = compute_heatmap(a, b, testcases, catmap, rule_engine)

    # Build cells dict with testcase IDs
    cells: Dict[str, dict] = {}
    for (row_val, col_val), cell_data in hm.cells.items():
        # Finde TC-IDs fuer dieses Paar
        tc_ids = []
        for idx, tc in enumerate(testcases):
            if tc.get(a) == row_val and tc.get(b) == col_val:
                tc_ids.append(testcases_db[idx].id if idx < len(testcases_db) else 0)

        cells[f"{row_val}-{col_val}"] = {
            "count": cell_data.count,
            "status": cell_data.status,
            "testcase_ids": tc_ids,
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
    """
    gen, categories, catmap, testcases, result_names, name_by_id, testcases_db = _load_generation_data(db, gid)
    rule_engine = _build_rule_engine(db, gen.project_id)

    c = calculate_coverage(testcases, catmap, strength, rule_engine, result_names)

    tuples_out = []
    for tup in c.uncovered_tuples:
        items = sorted(tup)
        tuples_out.append({
            "categories": [item[0] for item in items],
            "values": [item[1] for item in items],
        })

    if format == "csv":
        # CSV-Export
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(["Kategorien", "Werte"])
        for t in tuples_out:
            writer.writerow([", ".join(t["categories"]), ", ".join(t["values"])])

        csv_text = output.getvalue()
        return Response(
            content=csv_text.encode("utf-8-sig"),
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