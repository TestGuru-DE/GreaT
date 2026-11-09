from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from ..database import Base
from sqlalchemy import Boolean, String

# REQ-4023: Import User first (ProjectMembership references it), then ProjectMembership
from .auth import User  # noqa: F401
from .project_membership import ProjectMembership  # noqa: F401


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    categories = relationship("Category", back_populates="project", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="project", cascade="all, delete-orphan")
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")  # REQ-4023

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    is_result = Column(Boolean, default=False, nullable=False, server_default='0')  # REQ-4016: Ergebnis-Typ
    category_type = Column(String(20), default="standard", server_default="standard", nullable=False)  # REQ-5002: Kategorie-Typ (standard, cause, effect)
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="categories")
    values = relationship("Value", back_populates="category", cascade="all, delete-orphan")

class Value(Base):
    __tablename__ = "values"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=False)
    risk_weight = Column(Integer, default=1, nullable=False)
    allowed = Column(Boolean, nullable=False, default=True)      # NEU
    vtype = Column(String(20), nullable=False, default="string") # NEU
    order_index = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)  # REQ-3008
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    category = relationship("Category", back_populates="values")

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    strategy = Column(String(50), nullable=False)
    name = Column(String(300), nullable=True)  # REQ-2004: Editierbarer Name
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    coverage_meta = Column(Text, nullable=True)  # JSON-String (optional)ing (optional)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="generations")
    testcases = relationship("TestCase", back_populates="generation", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True)
    generation_id = Column(Integer, ForeignKey("generations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    generation = relationship("Generation", back_populates="testcases")
    values = relationship("TestCaseValue", back_populates="testcase", cascade="all, delete-orphan")

class TestCaseValue(Base):
    __tablename__ = "testcase_values"
    id = Column(Integer, primary_key=True)
    testcase_id = Column(Integer, ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=False)
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    testcase = relationship("TestCase", back_populates="values")

class Rule(Base):
    """
    Abhängigkeitsregel auf Projektebene:
    - type: aktuell nur 'dependency' (Wenn KategorieA=WertX, Dann KategorieB=WertY)
    - if_category_id / if_value: Auslöser (Antezedens)
    - then_category_id / then_value: Konsequenz (Konzedens)

    Alle IDs referenzieren das aktuelle Projekt (project_id).
    """
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021

    type = Column(String(20), nullable=False, default="dependency")

    if_category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    if_value       = Column(String, nullable=False)

    then_category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    then_value       = Column(String, nullable=False)
    # Für type='combine': Ziel-Kategorie steht in then_category_id,
    # die Zielwerte stehen JSON-kodiert als Array in then_values_json (z. B. '["DE","US","FR"]').
    then_values_json = Column(Text, nullable=True)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Datenklassen (REQ-2003) – Wiederverwendbare Äquivalenzklassen-Bibliothek
# ---------------------------------------------------------------------------

DATACLASS_TYPES = ("text", "number", "date", "time", "boolean", "email", "freetext")


class DataClass(Base):
    """Wiederverwendbare Äquivalenzklasse – benutzerdefiniert oder System."""
    __tablename__ = "dataclasses"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    value_type = Column(String(30), nullable=False, default="text")
    description = Column(String(500), nullable=True)
    is_system = Column(Boolean, nullable=False, default=False)  # REQ-2005: System-Datenklassen
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    dc_values = relationship("DataClassValue", back_populates="dataclass", cascade="all, delete-orphan")


class DataClassValue(Base):
    """Ein konkreter Wert einer Datenklasse."""
    __tablename__ = "dataclass_values"
    id = Column(Integer, primary_key=True)
    dataclass_id = Column(Integer, ForeignKey("dataclasses.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)  # REQ-4014: Drag & Drop Reihenfolge
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    dataclass = relationship("DataClass", back_populates="dc_values")


# ---------------------------------------------------------------------------
# REQ-4018: Hierarchische Datenklassen – Selbstreferenzierender Baum
# ---------------------------------------------------------------------------

class DataNode(Base):
    """REQ-4018: Hierarchischer Datenknoten (Kategorie/Gruppe/Klasse)."""
    __tablename__ = "data_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("data_nodes.id", ondelete="CASCADE"), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False, server_default='0')
    source = Column(String(100), nullable=True)  # z.B. "bugmagnet"
    sort_order = Column(Integer, default=0, nullable=False, server_default='0')
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    
    # Relationships
    parent = relationship("DataNode", back_populates="children", remote_side="DataNode.id")
    children = relationship("DataNode", back_populates="parent", order_by="DataNode.sort_order", cascade="all, delete-orphan")
    values = relationship("DataNodeValue", back_populates="node", order_by="DataNodeValue.sort_order", cascade="all, delete-orphan")


class DataNodeValue(Base):
    """REQ-4018: Wert eines Datenknotens."""
    __tablename__ = "data_node_values"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("data_nodes.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False, server_default='0')
    version = Column(Integer, default=0, server_default="0", nullable=False)  # REQ-4021
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # REQ-4024: Audit-Trail
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    
    node = relationship("DataNode", back_populates="values")

