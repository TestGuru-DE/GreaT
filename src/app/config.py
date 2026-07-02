"""Zentrale Konfiguration via Umgebungsvariablen.

REQ-4007: GREAT_PORT Umgebungsvariable fuer portierbare Deployment-Konfiguration.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # lädt .env falls vorhanden

GREAT_PORT: int = int(os.getenv("GREAT_PORT", "8000"))
GREAT_HOST: str = os.getenv("GREAT_HOST", "0.0.0.0")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./great.db")
