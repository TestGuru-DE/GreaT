"""Auth-Modelle fuer EPIC-18.

REQ-4001: User-Modell mit Password-Hashing (argon2id)
REQ-4020: Rollen-Modell (Admin/Editor/Viewer)
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import argon2


class User(Base):
    """User-Modell mit argon2id-Password-Hashing und Rollen.

    REQ-4001: Authentifizierung (OAuth2/JWT)
    REQ-4020: Rollen & Rechte Basismodell (Admin/Editor/Viewer)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer", server_default="viewer")  # admin, editor, viewer
    is_active = Column(Boolean, default=True, server_default='1')
    is_first_admin = Column(Boolean, default=False, server_default='0')
    # REQ-4027 AK-10: persistierter Zustand "Standardpasswort aktiv" (Sperre REQ-4028, Hinweis REQ-4027)
    default_password_active = Column(Boolean, default=False, server_default='0', nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    project_memberships = relationship("ProjectMembership", back_populates="user")  # REQ-4023

    def __init__(self, **kwargs):
        """Ensure Python-level defaults for role and is_active."""
        super().__init__(**kwargs)
        if self.role is None:
            self.role = "viewer"
        if self.is_active is None:
            self.is_active = True
        if self.is_first_admin is None:
            self.is_first_admin = False
        if self.default_password_active is None:
            self.default_password_active = False

    def set_password(self, password: str) -> None:
        """Hash password with argon2id.

        REQ-4001: Passwoerder werden gehasht gespeichert, niemals im Klartext.
        """
        self.password_hash = argon2.PasswordHasher().hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash.

        Returns True if password matches, False otherwise.
        Never raises exceptions on mismatch (prevents timing attacks).
        """
        try:
            return argon2.PasswordHasher().verify(self.password_hash, password)
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception:
            # Handle any other argon2 errors gracefully
            return False


class RefreshToken(Base):
    """Serverseitiger Refresh-Token-Speicher fuer Logout/Revocation.

    REQ-4001: Logout invalidiert Refresh-Token serverseitig.
    B2: Token-Rotation – jeder Refresh erzeugt einen neuen Eintrag.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), nullable=False, index=True)  # B2: Kein UNIQUE – Rotation erzeugt mehrere Eintraege
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")