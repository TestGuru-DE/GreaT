"""
services.py – G.R.E.A.T. Business-Logic-Schicht (DEBT-001)
Alle zustandslosen Hilfsfunktionen aus main.py extrahiert.
Keine HTTP-Konzepte außer HTTPException (FastAPI-Ausnahme).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models
from combinatorics import all_combinations, each_choice, orthogonal, linear_expansion, t_wise, mcdc
from combinatorics.risk_based import generate as risk_based_generate
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule


# ---------------------------------------------------------------------------
# Kategorie-/Werte-Lader
# ---------------------------------------------------------------------------

def load_categories_values(db: Session, project_id: int) -> Dict[str, List[str]]:
    """Gibt {Kategoriename: [erlaubte Werte + Fehlerwerte]} für ein Projekt zurück.
    
    BUG-6 Fix: Fehlerwerte (allowed == False) werden in die Generierung eingeschlossen.
    """
    cats = (
        db.query(models.Category)
        .filter(models.Category.project_id == project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    if not cats:
        return {}
    result: Dict[str, List[str]] = {}
    for c in cats:
        values = (
            db.query(models.Value)
            .filter(models.Value.category_id == c.id)
            .order_by(models.Value.id)
            .all()
        )
        result[c.name] = [v.value for v in values]
    return result


def load_error_values(db: Session, project_id: int) -> set:
    """BUG-5 + REQ-3063: Gibt alle Wert-Strings zurück die als Fehlerwert markiert sind (allowed=False)."""
    cats = db.query(models.Category).filter(models.Category.project_id == project_id).all()
    error_vals = set()
    for c in cats:
        vals = db.query(models.Value).filter(
            models.Value.category_id == c.id,
            models.Value.allowed == False
        ).all()
        error_vals.update(v.value for v in vals)
    return error_vals


def sort_testcases_error_last(testcases: List[Dict[str, str]], error_values: set) -> List[Dict[str, str]]:
    """BUG-5: Sortiert Testfälle sodass Testfälle mit mindestens einem Fehlerwert ans Ende kommen."""
    normal = []
    error = []
    for tc in testcases:
        if any(v in error_values for v in tc.values()):
            error.append(tc)
        else:
            normal.append(tc)
    return normal + error


def load_categories_values_weighted(db: Session, project_id: int) -> dict:
    """Gibt {Kategoriename: [(Wert, risk_weight), ...]} für die risikogewichtete Generierung zurück."""
    cats = (
        db.query(models.Category)
        .filter(models.Category.project_id == project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )
    if not cats:
        return {}
    result: dict = {}
    for c in cats:
        values = (
            db.query(models.Value)
            .filter(models.Value.category_id == c.id, models.Value.allowed == True)
            .order_by(models.Value.id)
            .all()
        )
        result[c.name] = [(v.value, v.risk_weight or 1) for v in values]
    return result


def generate_cases(categories: Dict[str, List[str]], strategy: str, db: Session = None, project_id: int = None, t_strength: int = 2) -> List[Dict[str, str]]:
    """Ruft die gewünschte Kombinatorik-Strategie auf (ohne Geschäftsregeln!)."""
    if strategy == "all":
        return all_combinations.generate(categories)
    if strategy == "each":
        return each_choice.generate(categories)
    if strategy in ("pairwise", "orthogonal"):
        return orthogonal.generate(categories)
    if strategy == "linear":
        return linear_expansion.generate(categories)
    if strategy == "t_wise":
        # REQ-3039: T-Wise mit konfigurierbarer Stärke
        return t_wise.generate(categories, t=t_strength)
    if strategy == "risk_based":
        # Risikogewichtete Generierung benötigt Gewichte aus der DB
        if db is not None and project_id is not None:
            weighted = load_categories_values_weighted(db, project_id)
            return risk_based_generate(weighted)
        # Fallback ohne Gewichte: wie each_choice
        return each_choice.generate(categories)
    if strategy == "mcdc":
        return mcdc.generate(categories)
    raise HTTPException(status_code=400, detail=f"Unbekannte Strategie: {strategy}")


# ---------------------------------------------------------------------------
# Regeln
# ---------------------------------------------------------------------------

def cat_id_to_name_map(db: Session, pid: int) -> Dict[int, str]:
    rows = db.query(models.Category.id, models.Category.name).filter(
        models.Category.project_id == pid
    ).all()
    return {cid: name for cid, name in rows}


def load_rules_structured(db: Session, pid: int) -> Dict[str, list]:
    """
    Lädt alle Regeln für ein Projekt:
    {
      "exclude": [(if_cat_id, if_value, then_cat_id, then_value), ...],
      "dependency": [(if_cat_id, if_value, then_cat_id, then_value), ...],
      "combine": [(if_cat_id, if_value, target_cat_id, [values...]), ...],
    }
    """
    rules = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    out: Dict[str, list] = {"exclude": [], "dependency": [], "combine": []}
    for r in rules:
        t = (r.if_category_id, r.if_value, r.then_category_id, r.then_value)
        if r.type == "exclude":
            out["exclude"].append(t)
        elif r.type == "dependency":
            out["dependency"].append(t)
        elif r.type == "combine":
            values: list = []
            if r.then_values_json:
                try:
                    values = json.loads(r.then_values_json)
                except Exception:
                    values = []
            out["combine"].append((r.if_category_id, r.if_value, r.then_category_id, values))
    return out


def apply_business_rules(
    pid: int,
    assignments: List[Dict[str, str]],
    db: Session,
) -> List[Dict[str, str]]:
    """
    Wendet alle Geschäftsregeln auf die Testfälle an.
    Reihenfolge: CombineRule → ForbiddenRule → DependencyRule
    """
    rules_raw = load_rules_structured(db, pid)
    id2name = cat_id_to_name_map(db, pid)

    rules: list = []
    for (if_cid, if_val, target_cid, target_values) in rules_raw["combine"]:
        if_name = id2name.get(if_cid)
        target_name = id2name.get(target_cid)
        if if_name and target_name and target_values:
            rules.append(CombineRule(if_category=if_name, if_value=if_val,
                                     then_category=target_name, allowed_values=target_values))

    for (if_cid, if_val, then_cid, then_val) in rules_raw["exclude"]:
        if_name = id2name.get(if_cid)
        then_name = id2name.get(then_cid)
        if if_name and then_name:
            rules.append(ForbiddenRule(if_category=if_name, if_value=if_val,
                                       then_category=then_name, then_value=then_val))

    for (if_cid, if_val, then_cid, then_val) in rules_raw["dependency"]:
        if_name = id2name.get(if_cid)
        then_name = id2name.get(then_cid)
        if if_name and then_name:
            rules.append(DependencyRule(if_category=if_name, if_value=if_val,
                                        then_category=then_name, then_value=then_val))

    engine = RuleEngine(rules=rules)
    result = engine.apply(list(assignments))

    seen: set = set()
    unique: List[Dict[str, str]] = []
    for a in result:
        key = tuple(sorted(a.items()))
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


# ---------------------------------------------------------------------------
# Lösch-Hilfsfunktionen
# ---------------------------------------------------------------------------

def project_has_generations(db: Session, pid: int) -> bool:
    return db.query(models.Generation).filter(models.Generation.project_id == pid).first() is not None


def force_delete_project(db: Session, pid: int) -> None:
    gids = [g.id for g in db.query(models.Generation.id).filter(models.Generation.project_id == pid).all()]
    if gids:
        tids = [t.id for t in db.query(models.TestCase.id).filter(models.TestCase.generation_id.in_(gids)).all()]
        if tids:
            db.query(models.TestCaseValue).filter(models.TestCaseValue.testcase_id.in_(tids)).delete(synchronize_session=False)
            db.query(models.TestCase).filter(models.TestCase.id.in_(tids)).delete(synchronize_session=False)
        db.query(models.Generation).filter(models.Generation.id.in_(gids)).delete(synchronize_session=False)
    cids = [c.id for c in db.query(models.Category.id).filter(models.Category.project_id == pid).all()]
    if cids:
        db.query(models.Value).filter(models.Value.category_id.in_(cids)).delete(synchronize_session=False)
        db.query(models.Category).filter(models.Category.id.in_(cids)).delete(synchronize_session=False)
    db.query(models.Project).filter(models.Project.id == pid).delete(synchronize_session=False)


def force_delete_category(db: Session, cid: int) -> int:
    cat = db.get(models.Category, cid)
    if not cat:
        return 0
    pid = cat.project_id
    db.query(models.TestCaseValue).filter(models.TestCaseValue.category_id == cid).delete(synchronize_session=False)
    db.query(models.Value).filter(models.Value.category_id == cid).delete(synchronize_session=False)
    db.delete(cat)
    return pid


def force_delete_value(db: Session, vid: int) -> int:
    v = db.get(models.Value, vid)
    if not v:
        return 0
    cid = v.category_id
    db.query(models.TestCaseValue).filter(
        models.TestCaseValue.category_id == cid,
        models.TestCaseValue.value == v.value,
    ).delete(synchronize_session=False)
    db.delete(v)
    return cid


# ---------------------------------------------------------------------------
# Export / Status
# ---------------------------------------------------------------------------

def assignment_from_testcase(db: Session, tc_id: int) -> Dict[str, str]:
    rows = (
        db.query(models.TestCaseValue, models.Category.name)
        .join(models.Category, models.Category.id == models.TestCaseValue.category_id)
        .filter(models.TestCaseValue.testcase_id == tc_id)
        .all()
    )
    return {cat_name: tcv.value for tcv, cat_name in rows}


def status_for_assignment(pid: int, a: Dict[str, str], db: Session) -> str:
    rules = load_rules_structured(db, pid)
    id2name = cat_id_to_name_map(db, pid)
    for (if_cid, if_val, target_cid, target_values) in rules["combine"]:
        if not target_values:
            continue
        if_name = id2name.get(if_cid)
        target_name = id2name.get(target_cid)
        if not if_name or not target_name:
            continue
        if a.get(if_name) == if_val and a.get(target_name) in target_values:
            return f"combined:{target_name}={a.get(target_name)}"
    return "ok"


# ---------------------------------------------------------------------------
# Wert-Normalisierung
# ---------------------------------------------------------------------------

def normalize_value_by_vtype(vtype: str, raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalisiert raw je nach vtype → (normalized, error_message)."""
    if raw is None:
        return None, "Kein Wert übergeben."
    s = str(raw).strip()

    if vtype == "string":
        return s, None

    if vtype == "integer":
        if re.fullmatch(r"[+-]?\d+", s):
            try:
                return str(int(s)), None
            except Exception:
                return None, "Wert ist kein gültiger Integer."
        return None, "Wert ist kein Integer (z. B. 42, -7)."

    if vtype == "number":
        s2 = s.replace(",", ".")
        try:
            f = float(s2)
            return format(f, "g"), None
        except Exception:
            return None, "Wert ist keine Zahl (z. B. 3.14 oder 3,14)."

    if vtype == "boolean":
        mapping = {
            "true": "true", "false": "false",
            "wahr": "true", "falsch": "false",
            "ja": "true", "nein": "false",
            "y": "true", "n": "false",
            "1": "true", "0": "false",
        }
        key = s.lower()
        if key in mapping:
            return mapping[key], None
        return None, "Wert ist kein Boolean (true/false, ja/nein, 1/0)."

    if vtype == "date":
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                pass
        return None, "Datum nicht erkennbar (YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY)."

    return s, None


def bool_from_form(value: str) -> bool:
    """Checkbox-Wert aus HTML-Form ('on', 'true', '1', ...) in bool wandeln."""
    return str(value).strip().lower() in ("1", "true", "on", "yes", "y")
