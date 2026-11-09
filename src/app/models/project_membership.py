"""REQ-4023: Projekt-Mitgliederverwaltung"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base


class ProjectMembership(Base):
    """REQ-4023: Verknuepfung zwischen User und Projekt mit Rolle."""
    __tablename__ = "project_memberships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False, default="viewer", server_default="viewer")  # editor, viewer

    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="project_memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )