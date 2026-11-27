"""Beispielprojekte – REQ-4017.

Quelle sind die Modelldateien unter examples/ (Format REQ-6013). Sie werden
beim ersten Start und nach dem Zuruecksetzen der Datenbank importiert:

- Portoberechnung (Beispiel): Kombinatorik mit Ergebnis-Kategorie "Portopreis"
- Lieferbedingungen – Regeln: Abhaengig-, Verboten- und Kombinieren-Regeln
- Versandkosten – Constraints: logische Constraints mit und/oder/nicht
- Retourenabwicklung – Entscheidungstabelle: Ursachen und Wirkungen

Ein Merker in app_state ("examples_version") verhindert, dass Beispiele, die der
Nutzer geloescht hat, bei jedem Neustart wiederkommen. Kommen neue Beispiele hinzu,
wird EXAMPLES_VERSION erhoeht; dann werden nur fehlende Beispiele ergaenzt.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AppState, Category, Project

log = logging.getLogger(__name__)

EXAMPLE_PROJECT_NAME = "Portoberechnung (Beispiel)"
EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
EXAMPLES_VERSION = "2"
_STATE_KEY = "examples_version"


def example_files() -> list[Path]:
    """Alle Beispiel-Modelldateien in fester Reihenfolge."""
    return sorted(EXAMPLES_DIR.glob("*.great.yaml"))


def _fix_legacy_porto_result(db: Session) -> None:
    """Aeltere Installationen: "Portopreis (Ergebnis)" war keine echte Ergebnis-Kategorie."""
    project = db.query(Project).filter(Project.name == EXAMPLE_PROJECT_NAME).first()
    if project is None:
        return
    category = (
        db.query(Category)
        .filter(Category.project_id == project.id, Category.name == "Portopreis (Ergebnis)")
        .first()
    )
    if category is not None and not category.is_result:
        category.name = "Portopreis"
        category.is_result = True
        db.commit()


def seed_example_project(db: Session, force: bool = False) -> list[str]:
    """Legt fehlende Beispielprojekte an (einmal je EXAMPLES_VERSION, oder immer mit force).

    Returns:
        Namen der neu angelegten Projekte.
    """
    from app import model_io

    state = db.get(AppState, _STATE_KEY)
    if not force and state is not None and state.value == EXAMPLES_VERSION:
        return []

    _fix_legacy_porto_result(db)

    created: list[str] = []
    files = example_files()
    if not files:
        log.warning("Keine Beispielprojekte gefunden unter %s", EXAMPLES_DIR)
    for path in files:
        try:
            model = model_io.from_yaml(path.read_text(encoding="utf-8"))
            exists = (
                db.query(Project)
                .filter(func.lower(Project.name) == model.project_name.lower())
                .first()
            )
            if exists:
                continue
            project = model_io.apply_model(db, None, model.model_dump(mode="json"), "dict")
            created.append(project.name)
        except Exception:  # noqa: BLE001 - ein defektes Beispiel darf den Start nicht verhindern
            db.rollback()
            log.exception("Beispielprojekt %s konnte nicht angelegt werden", path.name)

    if state is None:
        state = AppState(key=_STATE_KEY, value=EXAMPLES_VERSION)
        db.add(state)
    else:
        state.value = EXAMPLES_VERSION
    db.commit()
    return created
