"""REQ-6013: Pydantic-Modelle fuer das G.R.E.A.T. Modell-Format.

Single Source of Truth fuer Export/Import.
Schema-Version 1: entspricht dem Backup v2.0 Format, aber pro-Projekt.
Unterstuetzt sowohl snake_case (intern) als auch camelCase (YAML/JSON).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from ..name_validation import reject_control_chars  # BUG A-02


# ---------------------------------------------------------------------------
# Wert
# ---------------------------------------------------------------------------

class ModelValue(BaseModel):
    """Ein Wert innerhalb einer Kategorie."""
    value: str = Field(min_length=0, max_length=500)
    risk_weight: int = Field(default=1, ge=1, le=10, alias="riskWeight")
    vtype: str = Field(default="string")
    allowed: bool = Field(default=True)
    order_index: int = Field(default=0, ge=0, alias="orderIndex")
    is_default: bool = Field(default=False, alias="isDefault")

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    @field_validator("vtype")
    @classmethod
    def validate_vtype(cls, v: str) -> str:
        valid = {"string", "number", "date", "time", "boolean", "email", "text"}
        if v not in valid:
            raise ValueError(f"vtype must be one of {sorted(valid)}, got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Kategorie
# ---------------------------------------------------------------------------

class ModelCategory(BaseModel):
    """Eine Kategorie mit ihren Werten."""
    name: str = Field(min_length=1, max_length=200)
    order_index: int = Field(default=0, ge=0, alias="orderIndex")
    is_result: bool = Field(default=False, alias="isResult")
    category_type: str = Field(default="standard", alias="categoryType")
    values: List[ModelValue] = Field(default_factory=list)

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return reject_control_chars(v)  # BUG A-02

    @field_validator("category_type")
    @classmethod
    def validate_category_type(cls, v: str) -> str:
        valid = {"standard", "cause", "effect"}
        if v not in valid:
            raise ValueError(f"category_type must be one of {sorted(valid)}, got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Regel
# ---------------------------------------------------------------------------

class ModelRule(BaseModel):
    """Abhaengigkeitsregel (Referenzen ueber Namen, nicht IDs)."""
    type: str = Field(default="dependency")
    if_category_name: str = Field(alias="ifCategoryName")
    if_value: str = Field(alias="ifValue")
    then_category_name: str = Field(alias="thenCategoryName")
    then_value: str = Field(default="", alias="thenValue")
    then_values_json: Optional[str] = Field(default=None, alias="thenValuesJson")

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    @field_validator("type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        valid = {"dependency", "combine", "exclude"}
        if v not in valid:
            raise ValueError(f"rule type must be one of {sorted(valid)}, got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Decision Constraint (optional, wenn EPIC-20 aktiv)
# ---------------------------------------------------------------------------

class ModelDecisionConstraint(BaseModel):
    """Constraint fuer Entscheidungstabelle."""
    constraint_type: str = Field(alias="constraintType")
    targets: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

    model_config = ConfigDict(frozen=False, populate_by_name=True)


# ---------------------------------------------------------------------------
# REQ-6001 AK-10: Logischer Constraint (Referenzen ueber Namen, nicht IDs)
# ---------------------------------------------------------------------------

class ModelConstraint(BaseModel):
    """REQ-6001: Logischer Constraint fuer Modell-Export/Import.

    expression verwendet category_name und value_name statt IDs,
    analog zu ModelRule.
    """
    name: str = Field(min_length=1, max_length=300)
    kind: str = Field(description="'forbid' oder 'implies'")
    expression: Dict[str, Any] = Field(default_factory=dict, description="JSON-AST mit category_name/value_name")
    is_valid: bool = Field(default=True)

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        if v not in ("forbid", "implies"):
            raise ValueError(f"kind must be 'forbid' or 'implies', got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Hauptmodell
# ---------------------------------------------------------------------------

class GreatModel(BaseModel):
    """Vollstaendiges Testmodell eines G.R.E.A.T.-Projekts.

    Nicht enthalten: Generierungen, Benutzer, IDs, Zeitstempel.
    Referenzen innerhalb der Datei erfolgen ueber Namen.
    """
    schema_version: int = Field(default=1, alias="schemaVersion")
    project_name: str = Field(min_length=1, max_length=200, alias="projectName")

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        return reject_control_chars(v)  # BUG A-02

    categories: List[ModelCategory] = Field(default_factory=list)
    rules: List[ModelRule] = Field(default_factory=list)
    decision_constraints: List[ModelDecisionConstraint] = Field(
        default_factory=list,
        alias="decisionConstraints",
    )
    constraints: List[ModelConstraint] = Field(
        default_factory=list,
        alias="constraints",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        frozen=False,
    )

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"schemaVersion must be >= 1, got {v}")
        return v