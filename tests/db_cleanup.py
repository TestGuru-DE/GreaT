"""REQ-1300 Testintegritaet: Sauberes Aufraeumen benannter Testnutzer in der geteilten Test-DB.

Hintergrund: Viele Tabellen referenzieren ``users.id`` ueber ``last_modified_by``
(ohne Cascade). Ein naives ``DELETE FROM users`` scheitert dann an Foreign Keys.
Frueher wurde dieser Fehler verschluckt (``except Exception: pass``), die Nutzer
blieben bestehen und der naechste Test lief in ``UNIQUE constraint failed:
users.username``.

Dieses Modul loescht Testnutzer vollstaendig: Referenzen werden auf NULL gesetzt,
abhaengige Refresh-Tokens und Projekt-Mitgliedschaften entfernt, dann der Nutzer.
Es arbeitet ausschliesslich auf der ueber conftest umgeleiteten Test-DB.
"""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import update, delete

from app.database import Base
from app.models.auth import User, RefreshToken
from app.models.project_membership import ProjectMembership


def purge_users(db, usernames: Optional[Iterable[str]] = None) -> None:
    """Entfernt die genannten Nutzer (oder alle Nutzer, wenn ``usernames`` None ist).

    Fehler werden NICHT verschluckt: ein fehlgeschlagenes Aufraeumen soll den Test
    sichtbar machen, statt spaeter als UNIQUE-Konflikt aufzutauchen.
    """
    query = db.query(User.id)
    if usernames is not None:
        query = query.filter(User.username.in_(list(usernames)))
    user_ids = [row[0] for row in query.all()]
    if not user_ids:
        return

    # Referenzen auf die Nutzer in allen Tabellen loesen (last_modified_by ist nullable).
    for table in Base.metadata.sorted_tables:
        if "last_modified_by" in table.c:
            db.execute(
                update(table)
                .where(table.c.last_modified_by.in_(user_ids))
                .values(last_modified_by=None)
            )

    db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(user_ids)))
    db.execute(delete(ProjectMembership).where(ProjectMembership.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.id.in_(user_ids)))
    db.commit()
