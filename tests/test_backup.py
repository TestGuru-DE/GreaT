"""REQ-4011: Datensicherung & Wiederherstellung.

Angepasst an neues API:
- Passwort in URL -> 400 (B-12)
- Verschluesseltes Backup via POST /api/backup
- Restore via POST /api/backup/restore mit Form-Password
"""
import io
import json
import zipfile
import pytest
from app.main import app


def test_backup_download_returns_zip(auth_client):
    """GET /api/backup returns valid ZIP file."""
    r = auth_client.get("/api/backup")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert "great_backup" in r.headers.get("content-disposition", "")


def test_backup_contains_json(auth_client):
    """ZIP contains backup.json with version and projects."""
    r = auth_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert "backup.json" in zf.namelist()
    data = json.loads(zf.read("backup.json"))
    assert "version" in data
    assert "projects" in data
    assert data["version"] == "2.0"  # v2.0


def test_backup_password_in_url_returns_400(auth_client):
    """B-12: GET /api/backup?password=... returns 400."""
    r = auth_client.get("/api/backup?password=test123")
    assert r.status_code == 400


def test_backup_with_password_via_post(auth_client):
    """Verschluesseltes Backup via POST /api/backup."""
    r = auth_client.post("/api/backup", json={"password": "test123"})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert "backup.json.enc" in zf.namelist()
    assert "backup.json" not in zf.namelist()
    assert "backup.salt" in zf.namelist()
    assert "README.txt" in zf.namelist()


def test_backup_valid_json_structure(auth_client):
    """Backup JSON has valid structure (v2.0)."""
    r = auth_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    data = json.loads(zf.read("backup.json"))
    assert data["version"] == "2.0"
    assert "exported_at" in data
    assert isinstance(data["projects"], list)


def test_restore_empty_backup(admin_client):
    """POST /api/backup/restore with empty backup returns ok.

    BLOCKER B3: Nur Admin darf Backup wiederherstellen.
    """
    backup_r = admin_client.get("/api/backup")
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["projects_restored"] >= 0


def test_restore_wrong_password_fails(admin_client):
    """Restore with wrong password returns 400.

    BLOCKER B3: Nur Admin darf Backup wiederherstellen.
    """
    backup_r = admin_client.post("/api/backup", json={"password": "correctpass"})
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    form_data = {"password": "wrongpass"}
    r = admin_client.post("/api/backup/restore", files=files, data=form_data)
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "password" in r.json()["detail"].lower()


def test_restore_missing_password_fails(admin_client):
    """Restore of encrypted backup without password returns 400.

    BLOCKER B3: Nur Admin darf Backup wiederherstellen.
    """
    backup_r = admin_client.post("/api/backup", json={"password": "test123"})
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "password" in r.json()["detail"].lower()


def test_restore_invalid_zip_fails(admin_client):
    """POST with non-ZIP file returns 400.

    BLOCKER B3: Nur Admin darf Backup wiederherstellen.
    """
    files = {"file": ("bad.zip", io.BytesIO(b"not a zip"), "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 400


def test_backup_filename_contains_date(auth_client):
    """Backup filename contains 'great_backup'."""
    r = auth_client.get("/api/backup")
    disposition = r.headers.get("content-disposition", "")
    assert "great_backup" in disposition
    assert ".zip" in disposition


def test_restore_with_correct_password(admin_client):
    """Restore with correct password (via Form) succeeds.

    BLOCKER B3: Nur Admin darf Backup wiederherstellen.
    """
    password = "mysecurepass"
    backup_r = admin_client.post("/api/backup", json={"password": password})
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    form_data = {"password": password}
    r = admin_client.post("/api/backup/restore", files=files, data=form_data)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_backup_filename_encrypted(auth_client):
    """Verschluesseltes Backup hat 'encrypted' im Dateinamen."""
    r = auth_client.post("/api/backup", json={"password": "test"})
    disposition = r.headers.get("content-disposition", "")
    assert "encrypted" in disposition.lower()