"""Gemeinsame API-Typen."""
from typing import Annotated
from fastapi import Path

# ID-Typ fuer alle Pfadparameter: positive Integer, max 2^63-1 (SQLite LIMIT)
DbId = Annotated[int, Path(ge=1, le=2**63 - 1)]