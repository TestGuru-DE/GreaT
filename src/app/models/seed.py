"""
REQ-6009: Seed-Modelle fuer Pflicht-Testfaelle und Lueckenschluss.

SeedSet: Sammlung von SeedCases, gehoert zu einem Projekt.
SeedCase: Einzelner Pflicht-Testfall als JSON-Assignment.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship

from ..database import Base


class SeedSet(Base):
    """REQ-6009: Sammlung von Seed-Testfaellen pro Projekt."""
    __tablename__ = "seed_sets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(300), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project = relationship("Project", back_populates="seed_sets")
    seed_cases = relationship(
        "SeedCase", back_populates="seed_set", cascade="all, delete-orphan"
    )


class SeedCase(Base):
    """REQ-6009: Einzelner Seed-Testfall (Assignment als JSON)."""
    __tablename__ = "seed_cases"

    id = Column(Integer, primary_key=True, index=True)
    seed_set_id = Column(
        Integer, ForeignKey("seed_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_json = Column(Text, nullable=False)  # {"A": "a1", "B": null, ...}
    order_index = Column(Integer, default=0, nullable=False)

    seed_set = relationship("SeedSet", back_populates="seed_cases")