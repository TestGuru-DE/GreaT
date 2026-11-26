"""Referenzen eines Constraint-AST auf Kategorien und Werte.

BUG K-05: Beim Anlegen/Aendern muessen alle Referenzen zum eigenen Projekt gehoeren.
BUG K-02 / REQ-6001 AK-10: Vor dem Loeschen einer referenzierten Kategorie oder
eines referenzierten Werts werden die betroffenen Constraints ermittelt.
"""
from __future__ import annotations

import json
from typing import Iterator, List, Optional, Tuple

from sqlalchemy.orm import Session

from .ast_parser import COMPARISON_OPS


def iter_references(node) -> Iterator[Tuple[object, List[object]]]:
    """Liefert (category_id, [value_ids]) fuer jeden atomaren Vergleich im AST.

    Akzeptiert das komplette AST ({kind, condition, consequence}) oder einen Teilbaum.
    """
    if not isinstance(node, dict):
        return
    op = node.get("op")
    if op in COMPARISON_OPS:
        if "value_ids" in node and isinstance(node.get("value_ids"), list):
            vids = list(node["value_ids"])
        else:
            vids = [node.get("value_id")]
        yield node.get("category_id"), vids
        return
    for key in ("condition", "consequence", "arg"):
        if key in node:
            yield from iter_references(node[key])
    args = node.get("args")
    if isinstance(args, list):
        for child in args:
            yield from iter_references(child)


def invalid_references(db: Session, project_id: int, ast: dict) -> List[str]:
    """Fehlermeldungen fuer Referenzen, die nicht zum Projekt passen (leer = alles gueltig)."""
    from .. import models

    cats = {c.id for c in db.query(models.Category.id).filter(models.Category.project_id == project_id)}
    value_cat = {
        v.id: v.category_id
        for v in db.query(models.Value.id, models.Value.category_id).filter(models.Value.category_id.in_(cats))
    } if cats else {}

    errors: List[str] = []
    for cid, vids in iter_references(ast):
        if cid not in cats:
            errors.append(f"Kategorie {cid} gehoert nicht zu diesem Projekt")
            continue
        for vid in vids:
            if vid not in value_cat:
                errors.append(f"Wert {vid} gehoert nicht zu diesem Projekt")
            elif value_cat[vid] != cid:
                errors.append(f"Wert {vid} gehoert nicht zur Kategorie {cid}")
    return errors


def referencing_constraints(
    db: Session,
    project_id: int,
    category_id: Optional[int] = None,
    value_ids: Optional[List[int]] = None,
):
    """Gueltige Constraints des Projekts, die die Kategorie oder einen der Werte referenzieren."""
    from .. import models

    wanted_values = set(value_ids or [])
    hits = []
    for c in (
        db.query(models.Constraint)
        .filter(models.Constraint.project_id == project_id, models.Constraint.is_valid == True)  # noqa: E712
        .order_by(models.Constraint.name, models.Constraint.id)
    ):
        try:
            ast = json.loads(c.expression_json) if c.expression_json else {}
        except ValueError:
            continue
        for cid, vids in iter_references(ast):
            if (category_id is not None and cid == category_id) or wanted_values.intersection(vids):
                hits.append(c)
                break
    return hits
