"""
REQ-6009: API-Router fuer Seed-Saetze und Lueckenschluss.

Endpoints:
- GET    /api/projects/{pid}/seed-sets       - Liste
- POST   /api/projects/{pid}/seed-sets       - Erstellen
- GET    /api/projects/{pid}/seed-sets/{ssid} - Detail
- PUT    /api/projects/{pid}/seed-sets/{ssid} - Aktualisieren
- DELETE /api/projects/{pid}/seed-sets/{ssid} - Loeschen
- POST   /api/projects/{pid}/seed-sets/import-csv - CSV-Import
- POST   /api/generations/{gid}/gap-fill     - Lueckenschluss
"""
from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer
from ..api_types import DbId
from .. import models, schemas
from ..services_seed import (
    create_seed_set,
    get_seed_set,
    list_seed_sets,
    update_seed_set,
    delete_seed_set,
    import_csv_seeds,
    gap_fill_generation,
    MAX_SEEDS,
)
from ..routers.api_generate import _build_rule_engine

router = APIRouter(tags=["Seeds (REQ-6009)"], dependencies=[Depends(require_api_capable)])


# ---------------------------------------------------------------------------
# Response Schemas (inline, da spezifisch fuer diesen Router)
# ---------------------------------------------------------------------------


class SeedCaseOut(schemas.BaseModel):
    """REQ-6009: Seed-Testfall im Response."""
    id: int
    assignment_json: dict
    order_index: int

    model_config = schemas.ConfigDict(from_attributes=True)


class SeedSetOut(schemas.BaseModel):
    """REQ-6009: Seed-Satz im Response."""
    id: int
    project_id: int
    name: str
    created_at: str
    updated_at: str
    seed_count: int = 0
    seed_cases: List[SeedCaseOut] = []

    model_config = schemas.ConfigDict(from_attributes=True)


class SeedSetCreateResponse(schemas.BaseModel):
    """REQ-6009: Response beim Erstellen."""
    id: int
    name: str
    seed_count: int
    warnings: List[str] = []


class SeedSetListResponse(schemas.BaseModel):
    """REQ-6009: Response bei Liste."""
    seed_sets: List[SeedSetOut]


class SeedSetDetailResponse(schemas.BaseModel):
    """REQ-6009: Response bei Detail."""
    id: int
    project_id: int
    name: str
    created_at: str
    updated_at: str
    seed_cases: List[SeedCaseOut]
    warnings: List[str] = []


class SeedImportResponse(schemas.BaseModel):
    """REQ-6009: Response beim CSV-Import."""
    id: int
    name: str
    seed_count: int
    warnings: List[str] = []


class GapFillResponse(schemas.BaseModel):
    """REQ-6009: Response beim Lueckenschluss."""
    new_generation_id: int
    old_generation_id: int
    seed_count: int
    supplemented_count: int
    total_testcases: int
    coverage_before: float
    coverage_after: float
    impossible_tuples: List[list] = []
    warnings: List[str] = []


# ---------------------------------------------------------------------------
# CRUD Endpoints
# ---------------------------------------------------------------------------

@router.get("/projects/{pid}/seed-sets", response_model=SeedSetListResponse)
def api_list_seed_sets(
    pid: DbId,
    db: Session = Depends(get_db),
):
    """Listet alle Seed-Saetze eines Projekts."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    seed_sets = list_seed_sets(db, pid)
    result = []
    for ss in seed_sets:
        result.append(_seed_set_to_out(ss))

    return {"seed_sets": result}


@router.post("/projects/{pid}/seed-sets", status_code=201, response_model=SeedSetCreateResponse,
             dependencies=[Depends(require_writer)])
def api_create_seed_set(
    pid: DbId,
    payload: schemas.SeedSetCreate,
    db: Session = Depends(get_db),
):
    """Erstellt einen neuen Seed-Satz."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    # Seeds aus Payload extrahieren
    seeds = payload.seeds  # Jetzt direkt Dict-Liste

    rule_engine = _build_rule_engine(db, pid)
    seed_set, warnings = create_seed_set(
        db, pid, payload.name, seeds, rule_engine
    )

    return {
        "id": seed_set.id,
        "name": seed_set.name,
        "seed_count": len(seed_set.seed_cases),
        "warnings": warnings,
    }


@router.get("/projects/{pid}/seed-sets/{ssid}", response_model=SeedSetDetailResponse)
def api_get_seed_set(
    pid: DbId,
    ssid: DbId,
    db: Session = Depends(get_db),
):
    """Laedt einen Seed-Satz mit allen Seed-Testfaellen."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    seed_set = get_seed_set(db, ssid, pid)
    return {
        "id": seed_set.id,
        "project_id": seed_set.project_id,
        "name": seed_set.name,
        "created_at": seed_set.created_at.isoformat() if seed_set.created_at else "",
        "updated_at": seed_set.updated_at.isoformat() if seed_set.updated_at else "",
        "seed_cases": [
            {
                "id": sc.id,
                "assignment_json": json.loads(sc.assignment_json),
                "order_index": sc.order_index,
            }
            for sc in seed_set.seed_cases
        ],
        "warnings": [],
    }


@router.put("/projects/{pid}/seed-sets/{ssid}", response_model=SeedSetCreateResponse,
            dependencies=[Depends(require_writer)])
def api_update_seed_set(
    pid: DbId,
    ssid: DbId,
    payload: schemas.SeedSetUpdate,
    db: Session = Depends(get_db),
):
    """Aktualisiert einen Seed-Satz."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    # Seeds aus Payload extrahieren (oder None)
    seeds = payload.seeds  # Jetzt direkt Dict-Liste oder None

    rule_engine = _build_rule_engine(db, pid)
    seed_set, warnings = update_seed_set(
        db, ssid, pid, payload.name, seeds, rule_engine
    )

    seed_count = len(seed_set.seed_cases)

    return {
        "id": seed_set.id,
        "name": seed_set.name,
        "seed_count": seed_count,
        "warnings": warnings,
    }


@router.delete("/projects/{pid}/seed-sets/{ssid}", status_code=204,
               dependencies=[Depends(require_writer)])
def api_delete_seed_set(
    pid: DbId,
    ssid: DbId,
    db: Session = Depends(get_db),
):
    """Loescht einen Seed-Satz."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    delete_seed_set(db, ssid, pid)


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------

@router.post("/projects/{pid}/seed-sets/import-csv", response_model=SeedImportResponse,
             dependencies=[Depends(require_writer)])
def api_import_csv_seeds(
    pid: DbId,
    name: str = Form(...),
    csv_content: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Importiert Seeds aus einer CSV-Datei."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    csv_text = csv_content.file.read().decode("utf-8-sig")
    rule_engine = _build_rule_engine(db, pid)

    seed_set, warnings = import_csv_seeds(db, pid, name, csv_text, rule_engine)

    return {
        "id": seed_set.id,
        "name": seed_set.name,
        "seed_count": len(seed_set.seed_cases),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Gap Fill
# ---------------------------------------------------------------------------

@router.post("/generations/{gid}/gap-fill", response_model=GapFillResponse,
             dependencies=[Depends(require_writer)])
def api_gap_fill(
    gid: DbId,
    strategy: str = Query("pairwise", description="Strategie fuer Ergaenzung"),
    t_strength: int = Query(2, ge=1, le=10, description="t-Staerke"),
    db: Session = Depends(get_db),
):
    """
    Schliesst Luecken einer bestehenden Generierung.

    Erzeugt eine NEUE Generierung = alte Testfaelle + Ergaenzung.
    Die alte Generation bleibt unveraendert.
    """
    gen = db.get(models.Generation, gid)
    if not gen:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden.")

    rule_engine = _build_rule_engine(db, gen.project_id)

    # BUG B-03: Gleiches Zeitbudget wie bei der normalen Generierung
    import time as _time
    from combinatorics.budget import BudgetExceeded, time_budget
    from ..config import get_generation_timeout
    from .api_generate import _timeout_error
    timeout = get_generation_timeout()
    try:
        with time_budget(_time.time() + timeout):
            new_tcs, report, warnings = gap_fill_generation(
                db, gen.project_id, gid, strategy, t_strength, rule_engine
            )
    except BudgetExceeded:
        raise _timeout_error(timeout)
    except ValueError as e:  # BUG K-11: unbekannte Strategie
        raise HTTPException(status_code=422, detail={"code": "invalid_strategy", "detail": str(e)})

    # Neue Generierung speichern
    new_gen = models.Generation(
        project_id=gen.project_id,
        strategy=strategy,
        name=f"Lueckenschluss: {gen.name or gen.strategy}",
        seed_set_id=gen.seed_set_id,
    )
    db.add(new_gen)
    db.flush()

    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == gen.project_id)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )

    for idx, tc_data in enumerate(new_tcs, start=1):
        tc = models.TestCase(
            generation_id=new_gen.id,
            name=f"TC_{idx}",
            origin=tc_data.get("origin", "generated"),
        )
        db.add(tc)
        db.flush()

        for cat in categories:
            if cat.name in tc_data:
                db.add(
                    models.TestCaseValue(
                        testcase_id=tc.id,
                        category_id=cat.id,
                        category_name=cat.name,
                        value=tc_data[cat.name],
                    )
                )

    db.commit()

    return {
        "new_generation_id": new_gen.id,
        "old_generation_id": gid,
        "seed_count": report.seeds_count,
        "supplemented_count": report.supplemented_count,
        "total_testcases": report.total_testcases,
        "coverage_before": report.coverage_before,
        "coverage_after": report.coverage_after,
        "impossible_tuples": [sorted(list(t)) for t in report.impossible_tuples],  # BUG K-11
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _seed_set_to_out(seed_set: models.SeedSet) -> SeedSetOut:
    """Konvertiert ein SeedSet-Modell zum Response-Schema."""
    return SeedSetOut(
        id=seed_set.id,
        project_id=seed_set.project_id,
        name=seed_set.name,
        created_at=seed_set.created_at.isoformat() if seed_set.created_at else "",
        updated_at=seed_set.updated_at.isoformat() if seed_set.updated_at else "",
        seed_count=len(seed_set.seed_cases),
        seed_cases=[
            SeedCaseOut(
                id=sc.id,
                assignment_json=json.loads(sc.assignment_json),
                order_index=sc.order_index,
            )
            for sc in seed_set.seed_cases
        ],
    )