"""Datensicherung & Wiederherstellung – REQ-4011."""
import io
import json
import zipfile
import base64
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Project, Category, Value
from app.logging_config import get_logger

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

router = APIRouter(prefix="/api/backup", tags=["backup"])
log = get_logger(__name__)

SALT = b"great_backup_salt_v1"


def _make_key(password: str) -> bytes:
    """Derive encryption key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _encrypt(data: bytes, password: str) -> bytes:
    """Encrypt data with password using Fernet (AES-128)."""
    return Fernet(_make_key(password)).encrypt(data)


def _decrypt(data: bytes, password: str) -> bytes:
    """Decrypt data with password."""
    try:
        return Fernet(_make_key(password)).decrypt(data)
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Falsches Passwort oder beschädigte Datei")


def _export_data(db: Session) -> dict:
    """Alle Daten als dict serialisieren."""
    projects = db.query(Project).all()
    result = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "projects": []
    }

    for p in projects:
        proj_data = {
            "id": p.id,
            "name": p.name,
            "categories": []
        }
        for cat in p.categories:
            cat_data = {
                "id": cat.id,
                "name": cat.name,
                "values": [
                    {
                        "id": v.id,
                        "value": v.value,
                        "risk_weight": v.risk_weight,
                        "vtype": v.vtype,
                        "allowed": v.allowed,
                    }
                    for v in cat.values
                ]
            }
            proj_data["categories"].append(cat_data)
        result["projects"].append(proj_data)

    return result


@router.get("")
def create_backup(
    password: str = Query(default=None, description="Optionales Passwort für Verschlüsselung"),
    db: Session = Depends(get_db),
):
    """Backup aller Daten als ZIP herunterladen."""
    data = _export_data(db)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if password and CRYPTO_AVAILABLE:
            encrypted = _encrypt(json_bytes, password)
            zf.writestr("backup.json.enc", encrypted)
            zf.writestr("README.txt", "Diese Sicherung ist verschlüsselt. Passwort beim Wiederherstellen eingeben.")
        else:
            zf.writestr("backup.json", json_bytes)

    zip_buffer.seek(0)
    today = date.today().isoformat()
    filename = f"great_backup_{today}.zip"

    log.info("backup_created", projects=len(data["projects"]), encrypted=bool(password))
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    password: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """Backup wiederherstellen."""
    content = await file.read()
    zip_buffer = io.BytesIO(content)

    try:
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            names = zf.namelist()
            if "backup.json.enc" in names:
                if not password:
                    raise HTTPException(status_code=400, detail="Passwort erforderlich für verschlüsselte Sicherung")
                encrypted = zf.read("backup.json.enc")
                json_bytes = _decrypt(encrypted, password)
            elif "backup.json" in names:
                json_bytes = zf.read("backup.json")
            else:
                raise HTTPException(status_code=400, detail="Ungültige Backup-Datei")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Keine gültige ZIP-Datei")

    data = json.loads(json_bytes)
    restored = 0

    for proj_data in data.get("projects", []):
        name = proj_data["name"]
        # Namenskonflikt: Suffix anhängen
        existing = db.query(Project).filter(Project.name == name).first()
        if existing:
            name = f"{name}_restored"

        project = Project(name=name)
        db.add(project)
        db.flush()

        for cat_data in proj_data.get("categories", []):
            cat = Category(name=cat_data["name"], project_id=project.id)
            db.add(cat)
            db.flush()
            for val_data in cat_data.get("values", []):
                val = Value(
                    value=val_data["value"],
                    category_id=cat.id,
                    risk_weight=val_data.get("risk_weight", 1),
                    vtype=val_data.get("vtype", "string"),
                    allowed=val_data.get("allowed", True),
                )
                db.add(val)
        restored += 1

    db.commit()
    log.info("backup_restored", projects_restored=restored)
    return {"status": "ok", "projects_restored": restored}
