# src/app/schemas.py
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class ProjectRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class CategoryCreate(BaseModel):
    name: str
    order_index: int = 0

class CategoryRead(BaseModel):
    id: int
    name: str
    order_index: int
    model_config = ConfigDict(from_attributes=True)

class ValueCreate(BaseModel):
    value: str
    risk_weight: int = 1

VALID_VTYPES = {"string", "number", "date", "time", "boolean", "email", "text"}

class ValueRead(BaseModel):
    id: int
    value: str
    risk_weight: int
    vtype: str = "string"
    allowed: bool = True
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True)


class ValuePropertiesUpdate(BaseModel):
    """REQ-3007: Partielle Aktualisierung von Wert-Eigenschaften."""
    risk_weight: Optional[int] = None
    vtype: Optional[str] = None
    allowed: Optional[bool] = None

    @field_validator("risk_weight")
    @classmethod
    def validate_risk(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 10):
            raise ValueError("risk_weight muss zwischen 1 und 10 liegen.")
        return v

    @field_validator("vtype")
    @classmethod
    def validate_vtype(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_VTYPES:
            raise ValueError(f"vtype muss einer von {sorted(VALID_VTYPES)} sein.")
        return v

class GenerateRequest(BaseModel):
    strategy: str  # "all" | "each" | "pairwise" | "t_wise"
    limit: Optional[int] = None
    apply_rules: bool = False  # REQ-3005
    t_strength: Optional[int] = 2  # REQ-3039: T-Wise Parameter (Default: 2 = Pairwise)

class GenerateResponse(BaseModel):
    generation_id: int
    count: int

class TestCaseOut(BaseModel):
    name: str
    assignments: Dict[str, str]
    risk_coverage: float = 0.0  # REQ-3050: Summe der risk_weight aller Werte

# REQ-3051: Risikoabdeckungs-Zusammenfassung
class RiskSummary(BaseModel):
    """Risikoabdeckungs-Statistik für eine gesamte Generierung."""
    total_risk: float
    max_possible_risk: float
    risk_coverage_percent: float
    testcase_count: int

# REQ-2001: Generierungshistorie
class GenerationSummary(BaseModel):
    id: int
    strategy: str
    name: str
    created_at: str
    testcase_count: int
    model_config = ConfigDict(from_attributes=True)

# REQ-2002: Bulk-Delete
class BulkDeleteRequest(BaseModel):
    project_ids: List[int]

class BulkDeleteResponse(BaseModel):
    deleted: int
    blocked: List[int] = []

# REQ-2003: Datenklassen
class DataClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    value_type: str
    description: Optional[str] = None

class DataClassRead(BaseModel):
    id: int
    name: str
    value_type: str
    description: Optional[str]
    is_system: bool = False
    model_config = ConfigDict(from_attributes=True)

class DataClassValueCreate(BaseModel):
    value: str = Field(min_length=0, max_length=500)

class DataClassValueRead(BaseModel):
    id: int
    value: str
    model_config = ConfigDict(from_attributes=True)

class ApplyDataClassRequest(BaseModel):
    dataclass_id: int


# REQ-2004: Editierbarer Generierungsname
class GenerationRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)


# REQ-2006: Bulk-Delete Datenklassen
class DataclassBulkDeleteRequest(BaseModel):
    dataclass_ids: List[int]


class DataclassBulkDeleteResponse(BaseModel):
    deleted: int
    blocked: int = 0


# REQ-3003: Regel anlegen/lesen
VALID_RULE_TYPES = {"exclude", "dependency", "combine"}

class RuleCreate(BaseModel):
    type: str = Field(..., description="exclude | dependency | combine")
    if_category_id: int
    if_value: str = Field(min_length=1, max_length=300)
    then_category_id: int
    then_value: Optional[str] = Field(default=None, max_length=300)
    then_values: Optional[List[str]] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_RULE_TYPES:
            raise ValueError(f"Regeltyp muss einer von {VALID_RULE_TYPES} sein, erhalten: {v!r}")
        return v


class RuleRead(BaseModel):
    id: int
    type: str
    if_category_id: int
    if_value: str
    then_category_id: int
    then_value: Optional[str] = None
    then_values_json: Optional[str] = None
    conflict_with: List[int] = []
    model_config = ConfigDict(from_attributes=True)


# REQ-3064: Multi-Range Boundary Value Analysis
class BVARangeSchema(BaseModel):
    """Ein Äquivalenzklassen-Bereich für Multi-Range-BVA."""
    min_val: str
    max_val: str
    allowed: bool = True


class BVAMultiRangeRequest(BaseModel):
    """Request für Multi-Range BVA."""
    ranges: List[BVARangeSchema]
    points: int = Field(default=2, ge=2, le=4)  # 2, 3 oder 4
    
    @field_validator("ranges")
    @classmethod
    def validate_ranges(cls, v: List[BVARangeSchema]) -> List[BVARangeSchema]:
        if not v:
            raise ValueError("Mindestens ein Bereich erforderlich")
        return v
