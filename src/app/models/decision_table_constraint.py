"""REQ-5012: Constraint-Model fuer Entscheidungstabelle

Persistente Speicherung von Constraints (E, O, I, R, M) pro Projekt.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class DecisionTableConstraint(Base):
    """REQ-5012: Ein Constraint fuer eine Entscheidungstabelle.

    constraint_type:
        E - Exclusive: max 1 cause kann Y sein
        O - One-and-Only-One: genau 1 cause muss Y sein
        I - Inclusive: mindestens 1 cause muss Y sein
        R - Requires: wenn cause1=Y dann cause2=Y
        M - Mask: wenn effect1=X dann effect2=None

    targets:
        Fuer E, O, I: Liste von cause-IDs (z.B. [1, 2, 3])
        Fuer R: {"from": cause_id, "to": cause_id}
        Fuer M: {"from": effect_id, "to": effect_id}
    """
    __tablename__ = "decision_table_constraints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    constraint_type = Column(String(1), nullable=False)  # E, O, I, R, M
    targets = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)

    project = relationship("Project")