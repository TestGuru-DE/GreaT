"""Datensicherung & Wiederherstellung – REQ-4011.

Vollstaendiger Rewrite mit:
- Backup v2.0 Format (alle Felder, Namen statt IDs)
- Verschlusselung per POST /api/backup (Passwort im Body, nicht URL)
- Robuster Restore mit atomarem Commit, Groessenpruefung, Zip-Bomb-Schutz
- Pydantic-Validierung des Backup-Formats
- Passwort nie in Logs
"""
import os
import io
import json
import zipfile
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.models.auth import User
from app.logging_config import get_logger
from app.services import reset_database_state
from app.auth_deps import require_api_capable, require_admin

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

LEGACY_SALT = b"great_backup_salt_v1"  # Fallback fuer alte Backups

router = APIRouter(prefix="/api/backup", tags=["backup"])
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Kryptofunktionen mit Salt
# ---------------------------------------------------------------------------

def _make_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2 with custom salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _encrypt(data: bytes, password: str, salt: bytes) -> bytes:
    """Encrypt data with password using Fernet (AES-128)."""
    return Fernet(_make_key(password, salt)).encrypt(data)


def _decrypt(data: bytes, password: str, salt: bytes = None) -> bytes:
    """Decrypt data with password. Falls kein Salt: LEGACY_SALT als Fallback."""
    if salt is None:
        salt = LEGACY_SALT
    try:
        return Fernet(_make_key(password, salt)).decrypt(data)
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Falsches Passwort oder beschadigte Datei")


# ---------------------------------------------------------------------------
# Export (Backup v2.0)
# ---------------------------------------------------------------------------

def _export_data(db: Session) -> dict:
    """Alle Daten als dict serialisieren (v2.0 Format mit Namen statt IDs).

    Enthalt:
    - Projekte mit allen Feldern
    - Kategorien: name, order_index, is_result, category_type, values
    - Werte: value, risk_weight, vtype, allowed, order_index, is_default
    - Regeln: type, if_category_name (NAMEN!), if_value, then_category_name, then_value, then_values_json
    - Generierungen + TestCases (category_name als NAME)
    - Datenklassen (is_system=False)
    - Datenknoten (is_system=False, rekursiv)
    - Decision Constraints (project_name als NAME)
    - version: "2.0", exported_at: UTC ISO

    Enthalt NICHT:
    - Benutzer / Passwoerter
    - System-Datenklassen (is_system=True)
    - System-Datenknoten (is_system=True)
    """
    projects = db.query(models.Project).all()
    result = {
        "version": "2.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "projects": []
    }

    for p in projects:
        # Kategorie-Namen -> IDs Mapping fuer Regeln
        cat_id_to_name: dict[int, str] = {}
        cat_name_to_id: dict[str, int] = {}

        proj_data: dict = {
            "name": p.name,
            "categories": [],
            "rules": [],
            "generations": [],
            "dataclasses": [],
            "data_nodes": [],
            "decision_constraints": [],
        }

        # Kategorien
        for cat in p.categories:
            cat_id_to_name[cat.id] = cat.name
            cat_name_to_id[cat.name] = cat.id

            cat_data: dict = {
                "name": cat.name,
                "order_index": cat.order_index,
                "is_result": cat.is_result,
                "category_type": cat.category_type,
                "values": [
                    {
                        "value": v.value,
                        "risk_weight": v.risk_weight,
                        "vtype": v.vtype,
                        "allowed": v.allowed,
                        "order_index": v.order_index,
                        "is_default": v.is_default,
                    }
                    for v in cat.values
                ],
            }
            proj_data["categories"].append(cat_data)

        # Regeln (Kategorie-Namen statt IDs)
        for rule in p.rules:
            if_cat_name = cat_id_to_name.get(rule.if_category_id, "")
            then_cat_name = cat_id_to_name.get(rule.then_category_id, "")
            rule_data: dict = {
                "type": rule.type,
                "if_category_name": if_cat_name,
                "if_value": rule.if_value,
                "then_category_name": then_cat_name,
                "then_value": rule.then_value,
                "then_values_json": rule.then_values_json,
            }
            proj_data["rules"].append(rule_data)

        # Generierungen + TestCases
        for gen in p.generations:
            gen_data: dict = {
                "strategy": gen.strategy,
                "name": gen.name,
                "created_at": gen.created_at.isoformat() if gen.created_at else None,
                "coverage_meta": gen.coverage_meta,
                "testcases": [],
            }
            for tc in gen.testcases:
                tc_data: dict = {
                    "name": tc.name,
                    "assignments": {},
                }
                for tcval in tc.values:
                    cat_name = cat_id_to_name.get(tcval.category_id, f"unknown_{tcval.category_id}")
                    tc_data["assignments"][cat_name] = tcval.value
                gen_data["testcases"].append(tc_data)
            proj_data["generations"].append(gen_data)

        # Datenklassen (nur benutzerdefinierte, is_system=False)
        user_dataclasses = db.query(models.DataClass).filter(
            models.DataClass.is_system == False
        ).all()
        for dc in user_dataclasses:
            dc_data: dict = {
                "name": dc.name,
                "value_type": dc.value_type,
                "description": dc.description,
                "values": [dv.value for dv in dc.dc_values],
            }
            proj_data["dataclasses"].append(dc_data)

        # Datenknoten (nur benutzerdefinierte, is_system=False, rekursiv)
        def _export_data_nodes(parent_id: int | None) -> list[dict]:
            nodes = db.query(models.DataNode).filter(
                models.DataNode.parent_id == parent_id,
                models.DataNode.is_system == False,
            ).order_by(models.DataNode.sort_order).all()
            result_nodes = []
            for node in nodes:
                node_data: dict = {
                    "name": node.name,
                    "sort_order": node.sort_order,
                    "source": node.source,
                    "values": [nv.value for nv in node.values],
                    "children": _export_data_nodes(node.id),
                }
                result_nodes.append(node_data)
            return result_nodes

        proj_data["data_nodes"] = _export_data_nodes(None)

        # Decision Constraints
        from app.models.decision_table_constraint import DecisionTableConstraint
        constraints = db.query(DecisionTableConstraint).filter(
            DecisionTableConstraint.project_id == p.id
        ).all()
        for dc in constraints:
            dc_data: dict = {
                "constraint_type": dc.constraint_type,
                "targets": dc.targets,
                "description": dc.description,
            }
            proj_data["decision_constraints"].append(dc_data)

        result["projects"].append(proj_data)

    return result


# ---------------------------------------------------------------------------
# Restore (atomar, robust)
# ---------------------------------------------------------------------------

def _restore_data(db: Session, backup: schemas.BackupSchema) -> int:
    """Restore Backup-Daten atomar in die Datenbank.

    - Namenskonflikt-Handling: bestehende Projekte bekommen Suffix _restored_{n}
    - Kategorien mit allen Feldern (order_index, is_result, category_type)
    - Werte mit allen Feldern (order_index, is_default)
    - Regeln: Kategorie-Namen zurueck zu IDs mappen
    - Generierungen + TestCases: Kategorie-Namen zurueck zu IDs mappen
    - Datenklassen, Datenknoten (rekursiv), Decision Constraints
    - EIN db.commit() am Ende (atomar)

    Gibt Anzahl wiederhergestellter Projekte zurueck.
    """
    restored = 0

    for proj_data in backup.projects:
        name = proj_data.name

        # Namenskonflikt-Handling
        existing = db.query(models.Project).filter(models.Project.name == name).first()
        if existing:
            counter = 1
            while True:
                candidate = f"{name}_restored_{counter}"
                if not db.query(models.Project).filter(models.Project.name == candidate).first():
                    name = candidate
                    break
                counter += 1
                if counter > 100:
                    raise ValueError(f"Zu viele Konflikte fuer Projekt '{name}'")

        project = models.Project(name=name)
        db.add(project)
        db.flush()

        # Kategorie-Namen -> neue IDs mappen
        cat_name_to_id: dict[str, int] = {}

        for cat_data in proj_data.categories:
            cat = models.Category(
                name=cat_data.name,
                project_id=project.id,
                order_index=cat_data.order_index,
                is_result=cat_data.is_result,
                category_type=cat_data.category_type,
            )
            db.add(cat)
            db.flush()
            cat_name_to_id[cat_data.name] = cat.id

            for val_data in cat_data.values:
                val = models.Value(
                    value=val_data.value,
                    category_id=cat.id,
                    risk_weight=val_data.risk_weight,
                    vtype=val_data.vtype,
                    allowed=val_data.allowed,
                    order_index=val_data.order_index,
                    is_default=val_data.is_default,
                )
                db.add(val)

        # Regeln (Kategorie-Namen -> IDs)
        for rule_data in proj_data.rules:
            if_cat_id = cat_name_to_id.get(rule_data.if_category_name)
            then_cat_id = cat_name_to_id.get(rule_data.then_category_name)
            if if_cat_id and then_cat_id:
                rule = models.Rule(
                    project_id=project.id,
                    type=rule_data.type,
                    if_category_id=if_cat_id,
                    if_value=rule_data.if_value,
                    then_category_id=then_cat_id,
                    then_value=rule_data.then_value or "",
                    then_values_json=rule_data.then_values_json,
                )
                db.add(rule)

        # Generierungen + TestCases
        for gen_data in proj_data.generations:
            gen = models.Generation(
                project_id=project.id,
                strategy=gen_data.get("strategy", "all"),
                name=gen_data.get("name"),
                coverage_meta=gen_data.get("coverage_meta"),
            )
            db.add(gen)
            db.flush()

            for tc_data in gen_data.get("testcases", []):
                tc_name = tc_data.get("name", "TC_unknown")
                tc = models.TestCase(
                    generation_id=gen.id,
                    name=tc_name,
                )
                db.add(tc)
                db.flush()

                for cat_name, val_value in tc_data.get("assignments", {}).items():
                    tc_cat_id = cat_name_to_id.get(cat_name)
                    if tc_cat_id:
                        tcval = models.TestCaseValue(
                            testcase_id=tc.id,
                            category_id=tc_cat_id,
                            value=val_value,
                        )
                        db.add(tcval)

        # Datenklassen (benutzerdefinierte)
        for dc_data in proj_data.dataclasses:
            existing_dc = db.query(models.DataClass).filter(
                models.DataClass.name == dc_data.name
            ).first()
            if not existing_dc:
                dc = models.DataClass(
                    name=dc_data.name,
                    value_type=dc_data.value_type,
                    description=dc_data.description,
                    is_system=False,
                )
                db.add(dc)
                db.flush()
                for v in dc_data.values:
                    dcval = models.DataClassValue(
                        dataclass_id=dc.id,
                        value=v,
                    )
                    db.add(dcval)

        # Datenknoten (rekursiv)
        def _restore_data_node_recursive(node_data, parent_id: int | None) -> None:
            node = models.DataNode(
                name=node_data.name,
                parent_id=parent_id,
                is_system=False,
                source=node_data.source,
                sort_order=node_data.sort_order,
            )
            db.add(node)
            db.flush()

            for v in node_data.values:
                nv = models.DataNodeValue(
                    node_id=node.id,
                    value=v,
                    sort_order=0,
                )
                db.add(nv)

            for child in node_data.children:
                _restore_data_node_recursive(child, node.id)

        for node_data in proj_data.data_nodes:
            _restore_data_node_recursive(node_data, None)

        # Decision Constraints
        from app.models.decision_table_constraint import DecisionTableConstraint
        for dc_data in proj_data.decision_constraints:
            dc = DecisionTableConstraint(
                project_id=project.id,
                constraint_type=dc_data.constraint_type,
                targets=dc_data.targets,
                description=dc_data.description,
            )
            db.add(dc)

        restored += 1

    return restored


# ---------------------------------------------------------------------------
# GET /api/backup – Nur unverschlusselt, Passwort in URL -> 400
# ---------------------------------------------------------------------------

@router.get("")
def create_backup(
    password: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
):
    """Backup aller Daten als ZIP herunterladen (unverschlusselt).

    B-12: Passwort in der URL wird abgewiesen (400).
    Nutze POST /api/backup mit JSON-Body fuer verschluesseltes Backup.
    """
    if password is not None:
        raise HTTPException(
            status_code=400,
            detail="Das Passwort darf nicht in der URL uebergeben werden. Nutze POST /api/backup mit JSON-Body."
        )

    data = _export_data(db)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", json_bytes)
    zip_buffer.seek(0)

    log.info("backup_created", projects_count=len(data["projects"]))
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=great_backup.zip"},
    )


# ---------------------------------------------------------------------------
# POST /api/backup – Verschlusseltes Backup
# ---------------------------------------------------------------------------

@router.post("")
def create_backup_encrypted(
    body: schemas.BackupPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
):
    """Verschluesseltes Backup aller Daten als ZIP herunterladen.

    B-12: Passwort kommt im JSON-Body an (nicht in der URL).
    Salt wird zufaellig generiert und in der ZIP gespeichert.
    """
    if not CRYPTO_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Verschluesselung nicht verfuegbar. Installiere 'cryptography'."
        )

    salt = os.urandom(16)
    data = _export_data(db)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    encrypted = _encrypt(json_bytes, body.password, salt)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json.enc", encrypted)
        zf.writestr("backup.salt", base64.b64encode(salt).decode())
        zf.writestr("README.txt", "Diese Sicherung ist verschluesselt.")
    zip_buffer.seek(0)

    log.info("encrypted_backup_created", projects_count=len(data["projects"]))
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=great_backup_encrypted.zip"},
    )


# ---------------------------------------------------------------------------
# POST /api/backup/restore – Robust, atomar, Passwort im Form
# ---------------------------------------------------------------------------

@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    password: str = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    request: Request = None,
):
    """Backup wiederherstellen.

    B-11: Groessenpruefung, Zip-Bomb-Schutz, atomarer Commit.
    B-12: Passwort im Form-Body (nicht in URL).
    """
    # B-12: Passwort in URL pruefen (auch bei multipart-Requests)
    if request and request.query_params.get("password"):
        raise HTTPException(
            status_code=400,
            detail="Das Passwort darf nicht in der URL uebergeben werden."
        )

    # Groessenpruefung (dynamisch aus Config lesen, damit monkeypatch in Tests funktioniert)
    from app.config import GREAT_MAX_BACKUP_MB as MAX_MB
    max_bytes = MAX_MB * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu gross. Maximum: {MAX_MB} MB."
        )

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu gross. Maximum: {MAX_MB} MB."
        )

    zip_buffer = io.BytesIO(content)
    try:
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            # Zip-Bomb-Schutz
            for info in zf.infolist():
                if info.file_size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Datei '{info.filename}' zu gross nach Entpacken."
                    )

            names = zf.namelist()
            if "backup.json.enc" in names:
                if not password:
                    raise HTTPException(
                        status_code=400,
                        detail="Passwort erforderlich"
                    )
                if not CRYPTO_AVAILABLE:
                    raise HTTPException(
                        status_code=501,
                        detail="Verschluesselung nicht verfuegbar"
                    )

                encrypted = zf.read("backup.json.enc")
                salt_b64 = zf.read("backup.salt").decode() if "backup.salt" in names else None
                salt = base64.b64decode(salt_b64) if salt_b64 else None
                json_bytes = _decrypt(encrypted, password, salt)
            elif "backup.json" in names:
                json_bytes = zf.read("backup.json")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Ungueltige Backup-Datei"
                )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Keine gueltige ZIP-Datei")

    # JSON + Pydantic-Validierung
    try:
        data = json.loads(json_bytes)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ungueltiges JSON: {e}")

    try:
        backup = schemas.BackupSchema.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ungueltiges Backup-Format: {e}")

    # Atomarer Restore
    try:
        restored = _restore_data(db, backup)
        db.commit()
        log.info("backup_restored", projects_restored=restored)
        return {"status": "ok", "projects_restored": restored}
    except Exception as e:
        db.rollback()
        log.exception("restore_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Restore fehlgeschlagen. Datenbank wurde nicht geaendert."
        )


# ---------------------------------------------------------------------------
# POST /api/backup/reset – Unveraendert belassen
# ---------------------------------------------------------------------------

@router.post("/reset")
def reset_database(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Setzt die komplette Datenbank auf den Standard-Startzustand zurueck.

    BLOCKER B2: Nur Admin darf die DB zuruecksetzen.
    """
    try:
        result = reset_database_state(db)
        log.info("database_reset", reset=result.get("reset"))
        return result
    except Exception as exc:
        log.exception("database_reset_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Datenbank konnte nicht zurueckgesetzt werden")