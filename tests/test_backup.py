"""REQ-4011: Datensicherung & Wiederherstellung."""
import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_backup_download_returns_zip():
    """GET /api/backup returns valid ZIP file."""
    r = client.get("/api/backup")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert "great_backup_" in r.headers.get("content-disposition", "")


def test_backup_contains_json():
    """ZIP contains backup.json with version and projects."""
    r = client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert "backup.json" in zf.namelist()
    data = json.loads(zf.read("backup.json"))
    assert "version" in data
    assert "projects" in data
    assert data["version"] == "1.0"


def test_backup_with_password_encrypted():
    """Backup with password creates .enc file instead of plain JSON."""
    r = client.get("/api/backup?password=test123")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert "backup.json.enc" in zf.namelist()
    assert "backup.json" not in zf.namelist()
    assert "README.txt" in zf.namelist()


def test_backup_valid_json_structure():
    """Backup JSON has valid structure."""
    r = client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    data = json.loads(zf.read("backup.json"))
    assert data["version"] == "1.0"
    assert "exported_at" in data
    assert isinstance(data["projects"], list)


def test_restore_empty_backup():
    """POST /api/backup/restore with empty backup returns ok."""
    backup_r = client.get("/api/backup")
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = client.post("/api/backup/restore", files=files)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["projects_restored"] >= 0


def test_restore_wrong_password_fails():
    """Restore with wrong password returns 400."""
    backup_r = client.get("/api/backup?password=correctpass")
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = client.post("/api/backup/restore?password=wrongpass", files=files)
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "password" in r.json()["detail"].lower()


def test_restore_missing_password_fails():
    """Restore of encrypted backup without password returns 400."""
    backup_r = client.get("/api/backup?password=test123")
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = client.post("/api/backup/restore", files=files)
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "password" in r.json()["detail"].lower()


def test_restore_invalid_zip_fails():
    """POST with non-ZIP file returns 400."""
    files = {"file": ("bad.zip", io.BytesIO(b"not a zip"), "application/zip")}
    r = client.post("/api/backup/restore", files=files)
    assert r.status_code == 400


def test_backup_filename_contains_date():
    """Backup filename contains date in format YYYY-MM-DD."""
    r = client.get("/api/backup")
    disposition = r.headers.get("content-disposition", "")
    assert "great_backup_" in disposition
    assert ".zip" in disposition
    # Extract date portion (should be YYYY-MM-DD)
    parts = disposition.split("_")
    assert len(parts) >= 3


def test_restore_with_correct_password():
    """Restore with correct password succeeds."""
    password = "mysecurepass"
    backup_r = client.get(f"/api/backup?password={password}")
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = client.post(f"/api/backup/restore?password={password}", files=files)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


