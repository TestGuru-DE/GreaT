# src/app/schemas.py
import re
from typing import List, Optional, Dict
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._@-]{3,50}$")

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Projektname darf nicht leer oder nur Leerzeichen sein.")
        return v.strip()

class ProjectRead(BaseModel):
    id: int
    name: str
    version: int = 0  # REQ-4021: Versionsnummer fuer Konflikterkennung
    model_config = ConfigDict(from_attributes=True)

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    order_index: int = 0
    is_result: bool = False  # REQ-4016: Ergebnis-Kategorie
    category_type: str = "standard"  # REQ-5002: standard | cause | effect

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Kategoriename darf nicht leer sein.")
        if len(trimmed) > 200:
            raise ValueError("Kategoriename darf maximal 200 Zeichen haben.")
        return trimmed

    @field_validator("category_type")
    @classmethod
    def validate_category_type(cls, v: str) -> str:
        if v not in VALID_CATEGORY_TYPES:
            raise ValueError(f"category_type muss einer von {sorted(VALID_CATEGORY_TYPES)} sein.")
        return v

class CategoryRead(BaseModel):
    id: int
    name: str
    order_index: int
    is_result: bool = False  # REQ-4016: Ergebnis-Typ (Expected Result)
    category_type: str = "standard"  # REQ-5002
    model_config = ConfigDict(from_attributes=True)

class ValueCreate(BaseModel):
    value: str
    risk_weight: int = 1

    @field_validator("value")
    @classmethod
    def value_not_empty(cls, v: str) -> str:
        if v == "":
            raise ValueError("Wert darf nicht leer sein.")
        if len(v) > 500:
            raise ValueError("Wert darf maximal 500 Zeichen haben.")
        return v  # NICHT trimmen!

    @field_validator("risk_weight")
    @classmethod
    def validate_risk_weight(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("risk_weight muss zwischen 1 und 10 liegen.")
        return v

VALID_VTYPES = {"string", "number", "date", "time", "boolean", "email", "text"}
# REQ-5002: Kategorie-Typ (Ursache/Wirkung fuer Entscheidungstabelle)
VALID_CATEGORY_TYPES = {"standard", "cause", "effect"}

class ValueRead(BaseModel):
    id: int
    value: str
    risk_weight: int
    vtype: str = "string"
    allowed: bool = True
    is_error: bool = False  # REQ-4015: Fehlerwert-Flag für BVA
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
    limit: Optional[int] = Field(default=None, ge=1, le=100000)
    apply_rules: bool = False  # REQ-3005
    t_strength: Optional[int] = Field(default=None, ge=1, le=10)
    # REQ-6009: Seeds
    seed_set_id: Optional[int] = None  # Referenz auf gespeicherten Seed-Satz
    seeds: Optional[List[dict]] = None  # Inline-Seed-Liste [{"A": "a1", "B": null}, ...]

    @field_validator("t_strength", mode="before")
    @classmethod
    def resolve_t_strength(cls, v):
        if v is None:
            return 2
        return v


class GenerateResponse(BaseModel):
    generation_id: int
    count: int
    total_possible: Optional[int] = None
    truncated: bool = False
    rules_applied: bool = False
    rule_count: int = 0
    warnings: List[str] = []
    # REQ-6009: Seed-Generierung
    seeds_count: int = 0
    supplemented_count: int = 0
    coverage_before: float = 0.0
    coverage_after: float = 0.0

class TestCaseOut(BaseModel):
    id: int
    name: str
    assignments: Dict[str, str]
    has_error_value: bool = False  # REQ-3063: Flag für Fehlerwert-Markierung
    risk_coverage: float = 0.0  # REQ-3050: Summe der risk_weight aller Werte
    origin: Optional[str] = None  # REQ-6009: "seed" | "supplemented" | "generated"

    model_config = ConfigDict(populate_by_name=True)

# REQ-3051: Risikoabdeckungs-Zusammenfassung
class RiskSummary(BaseModel):
    """Risikoabdeckungs-Statistik für eine gesamte Generierung."""
    total_risk: float
    max_possible_risk: float
    risk_coverage_percent: float
    testcase_count: int


class ResultCategoryValueRead(BaseModel):
    id: int
    value: str


class ResultCategoryRead(BaseModel):
    id: int
    name: str
    editable: bool = True
    values: List[ResultCategoryValueRead] = []


class TestcasesResponse(BaseModel):
    testcases: List[TestCaseOut]
    risk_summary: RiskSummary
    result_categories: List[ResultCategoryRead] = []


class TestCaseAssignmentUpdate(BaseModel):
    category_name: str = Field(min_length=1, max_length=200)
    value: str = Field(default="", max_length=500)


class TestCaseAssignmentUpdateResponse(BaseModel):
    testcase_id: int
    category_name: str
    value: str

# REQ-2001: Generierungshistorie
class GenerationSummary(BaseModel):
    id: int
    strategy: str
    name: str
    created_at: str
    testcase_count: int
    coverage_2wise_pct: Optional[float] = None  # REQ-6008: 2-wise Coverage %
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


# ---------------------------------------------------------------------------
# REQ-6007: Extended BVA for date, time, datetime, string length
# ---------------------------------------------------------------------------

class BVAExtendedRangeSchema(BaseModel):
    """Erweiterter Bereich fuer REQ-6007 mit Datentyp."""
    min_val: str
    max_val: str
    allowed: bool = True
    type: str = "number"  # 'number', 'date', 'time', 'datetime', 'strlen'


class BVAExtendedRequest(BaseModel):
    """Request fuer erweiterte BVA (REQ-6007).

    Felder:
    - type: 'number' (Standard), 'date', 'time', 'datetime', 'strlen'
    - ranges: Liste von Bereichen (min_val/max_val als Strings)
    - points: 2, 3 oder 4
    - options: Typspezifische Optionen
    """
    type: str = "number"
    ranges: List[BVAExtendedRangeSchema]
    points: int = Field(default=2, ge=2, le=4)
    options: Optional[dict] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"number", "date", "time", "datetime", "strlen"}
        if v not in allowed:
            raise ValueError(f"type muss einer sein von: {allowed}, nicht {v!r}")
        return v

    @field_validator("ranges")
    @classmethod
    def validate_ranges(cls, v: List[BVAExtendedRangeSchema]) -> List[BVAExtendedRangeSchema]:
        if not v:
            raise ValueError("Mindestens ein Bereich erforderlich")
        return v


class BVAExtendedResult(BaseModel):
    """Einzelnes Ergebnis der erweiterten BVA."""
    value: str
    is_error: bool
    vtype: str
    label: str = ""


class BVAExtendedResponse(BaseModel):
    """Response fuer erweiterte BVA (REQ-6007)."""
    values: List[BVAExtendedResult]
    category_id: int


# REQ-4018: Hierarchische Datenklassen
class DataNodeValueBase(BaseModel):
    value: str
    sort_order: int = 0

class DataNodeValueRead(DataNodeValueBase):
    id: int
    node_id: int
    model_config = ConfigDict(from_attributes=True)

class DataNodeRead(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    is_system: bool = False
    source: Optional[str] = None
    sort_order: int = 0
    version: int = 0  # B-09: Fuer Concurrency-Control in PUT
    values: List[DataNodeValueRead] = []
    children: List["DataNodeRead"] = []  # Rekursiv
    
    model_config = ConfigDict(from_attributes=True)

# Für rekursive Referenz notwendig
DataNodeRead.model_rebuild()

class DataNodeCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0

class DataNodeValueCreate(BaseModel):
    value: str
    sort_order: int = 0

class DataNodeUpdate(BaseModel):
    # REQ-4018/REQ-4021: Teil-Update; nur gesetzte Felder werden uebernommen
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    version: Optional[int] = None  # Optimistic Concurrency (REQ-4021)

# REQ-4025: Benutzerverwaltung
VALID_USER_ROLES = {"admin", "editor", "viewer", "api_user"}

def _check_user_role(v: Optional[str]) -> Optional[str]:
    if v is not None and v not in VALID_USER_ROLES:
        raise ValueError(f"role muss einer von {sorted(VALID_USER_ROLES)} sein.")
    return v

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)
    role: str = "viewer"

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        trimmed = v.strip()
        if not USERNAME_PATTERN.match(trimmed):
            raise ValueError("Benutzername muss 3-50 Zeichen aus A-Z a-z 0-9 . _ - @ enthalten.")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        from .password_policy import validate_new_password, PasswordError
        try:
            validate_new_password(v)
        except PasswordError as e:
            raise ValueError(e.code)
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return _check_user_role(v)

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        return _check_user_role(v)

class UserPasswordChange(BaseModel):
    # Frontend sendet {"password": ...}, Tests/API-Doku {"new_password": ...}: beide akzeptieren
    new_password: str = Field(min_length=1, max_length=200, validation_alias=AliasChoices("new_password", "password"))

class UserRead(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)

# REQ-4028 AK-3: Selbst-Passwortwechsel
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)

# REQ-6005: Sprachpraferenz aktualisieren
class UserPreferencesRequest(BaseModel):
    language: str = Field(min_length=2, max_length=2)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in {"de", "en"}:
            raise ValueError("language muss 'de' oder 'en' sein.")
        return v

class UserPreferencesResponse(BaseModel):
    language: Optional[str] = None

# ============================================================================
# Backup-Schemas (v2.0 Format)
# ============================================================================

class BackupPasswordRequest(BaseModel):
    """Request-Schema fuer verschluesseltes Backup (POST /api/backup)."""
    password: str


class BackupValueSchema(BaseModel):
    value: str
    risk_weight: int = 1
    vtype: str = "string"
    allowed: bool = True
    order_index: int = 0
    is_default: bool = False


class BackupCategorySchema(BaseModel):
    name: str
    order_index: int = 0
    is_result: bool = False
    category_type: str = "standard"
    values: list[BackupValueSchema] = []


class BackupRuleSchema(BaseModel):
    type: str
    if_category_name: str
    if_value: str
    then_category_name: str
    then_value: str | None = None
    then_values_json: str | None = None


class BackupDataClassSchema(BaseModel):
    name: str
    value_type: str
    description: str | None = None
    values: list[str] = []


class BackupDataNodeSchema(BaseModel):
    """Rekursives Schema fuer hierarchische Datenknoten."""
    name: str
    sort_order: int = 0
    source: str | None = None
    values: list[str] = []
    children: list["BackupDataNodeSchema"] = []


BackupDataNodeSchema.model_rebuild()


class BackupDecisionConstraintSchema(BaseModel):
    constraint_type: str
    targets: dict
    description: str | None = None


class BackupConstraintSchema(BaseModel):
    """REQ-6001 AK-10: Constraint im Backup-Format (Namen statt IDs)."""
    name: str
    kind: str
    expression: dict
    is_valid: bool = True


class BackupProjectSchema(BaseModel):
    name: str
    categories: list[BackupCategorySchema] = []
    rules: list[BackupRuleSchema] = []
    generations: list[dict] = []
    dataclasses: list[BackupDataClassSchema] = []
    data_nodes: list[BackupDataNodeSchema] = []
    decision_constraints: list[BackupDecisionConstraintSchema] = []
    constraints: list[BackupConstraintSchema] = []


class BackupSchema(BaseModel):
    """Top-Level Backup-Schema (v1.0 und v2.0)."""
    version: str
    exported_at: str
    projects: list[BackupProjectSchema]


# ============================================================================
# REQ-4023: Projekt-Mitgliedschaften
class ProjectMemberRead(BaseModel):
    user_id: int
    username: Optional[str] = None
    role: str

class AddProjectMemberRequest(BaseModel):
    user_id: int
    role: str = "viewer"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in {"editor", "viewer"}:
            raise ValueError("role muss 'editor' oder 'viewer' sein.")
        return v


# ============================================================================
# REQ-6001: Logische Constraints (Mehrbedingungs-Regeln)
# ============================================================================

VALID_CONSTRAINT_KINDS = {"forbid", "implies"}


class ConstraintCreate(BaseModel):
    """Request-Schema zum Anlegen eines Constraints."""
    name: str = Field(min_length=1, max_length=300)
    kind: str  # "forbid" oder "implies"
    expression: dict  # JSON-AST condition nach ADR-020
    consequence: Optional[dict] = None  # nur bei implies

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        if v not in VALID_CONSTRAINT_KINDS:
            raise ValueError(f"kind muss einer von {VALID_CONSTRAINT_KINDS} sein.")
        return v


class ConstraintUpdate(BaseModel):
    """Partielle Aktualisierung eines Constraints."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    kind: Optional[str] = None
    expression: Optional[dict] = None
    consequence: Optional[dict] = None  # nur bei implies
    is_valid: Optional[bool] = None

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CONSTRAINT_KINDS:
            raise ValueError(f"kind muss einer von {VALID_CONSTRAINT_KINDS} sein.")
        return v


class ConstraintRead(BaseModel):
    """Response-Schema fuer ein Constraint.

    expression: nur die condition (kein verschachteltes AST)
    consequence: nur bei 'implies'-Constraints
    """
    id: int
    project_id: int
    name: str
    kind: str
    expression: dict  # condition-AST (nicht das komplette Constraint-AST)
    consequence: Optional[dict] = None  # nur bei 'implies'
    is_valid: bool
    created_at: str
    updated_at: str
    warnings: List[str] = []  # REQ-6001 AK-8: Widerspruchswarnungen

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        # Custom serialization: parse expression_json and extract condition/consequence
        import json
        data = obj.__dict__.copy()
        ast_dict = json.loads(obj.expression_json) if obj.expression_json else {}
        # Extract condition as expression (flat structure for frontend)
        data['expression'] = ast_dict.get('condition', {})
        # Extract consequence as separate field
        data['consequence'] = ast_dict.get('consequence')
        data.pop('expression_json', None)
        return cls(**data)


class ConstraintValidateRequest(BaseModel):
    """Request-Schema zur Validierung eines AST ohne Speicherung."""
    expression: dict
    kind: str = "forbid"
    consequence: Optional[dict] = None

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        if v not in VALID_CONSTRAINT_KINDS:
            raise ValueError(f"kind muss einer von {VALID_CONSTRAINT_KINDS} sein.")
        return v


class ConstraintValidateResponse(BaseModel):
    """Response-Schema fuer AST-Validierung."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    leaf_count: int = 0
    depth: int = 0


# ============================================================================
# REQ-6008: Coverage Schemas
# ============================================================================

class CoverageStat(BaseModel):
    """t-wise Abdeckungsstatistik."""
    t: int
    covered: int
    possible: int
    percentage: float
    excluded_by_rules: int = 0


class HeatmapPair(BaseModel):
    """Ein Kategorienpaar in der Uebersichtsmatrix."""
    cat_a: str
    cat_b: str
    coverage_pct: float
    covered: int
    possible: int


class HeatmapOverview(BaseModel):
    """Uebersicht aller Kategorienpaare mit Abdeckungsgrad."""
    categories: List[str]
    pairs: List[HeatmapPair]


class CoverageResponse(BaseModel):
    """Response fuer GET /api/generations/{gid}/coverage.
    
    Enthalt 1-wise und 2-wise Coverage, Uebersicht aller Kategorienpaare,
    unabgedeckte Tupel und optional 3-wise (bei ?t=3).
    """
    generation_id: int
    coverage_1wise: CoverageStat
    coverage_2wise: CoverageStat
    coverage_3wise: Optional[CoverageStat] = None
    heatmap: HeatmapOverview
    uncovered_tuples_2wise: List[dict] = []
    cached: bool = False


class HeatmapCellData(BaseModel):
    """Einzelne Zelle in der Heatmap."""
    count: int
    status: str  # "covered" | "uncovered" | "excluded"
    testcase_ids: List[int] = []


class HeatmapResponse(BaseModel):
    """Response fuer GET /api/generations/{gid}/coverage/pair.
    
    Detail-Heatmap fuer zwei Kategorien.
    """
    cat_a: str
    cat_b: str
    rows: List[str]
    cols: List[str]
    cells: Dict[str, HeatmapCellData]


class UncoveredTupleResponse(BaseModel):
    """Response fuer GET /api/generations/{gid}/coverage/missing.
    
    Liste unabgedeckter Tupel, sortiert und filterbar.
    """
    generation_id: int
    t: int
    tuples: List[dict]
    total: int


# ============================================================================
# REQ-6009: Seed-Saetze und Seed-Testfaelle
# ============================================================================

MAX_SEEDS_PER_SET = 10000


class SeedCaseCreate(BaseModel):
    """REQ-6009: Einzelner Seed-Testfall (Assignment als JSON)."""
    assignment: Dict[str, Optional[str]]  # {"A": "a1", "B": None, ...}
    order_index: int = 0

    @field_validator("assignment")
    @classmethod
    def assignment_not_empty(cls, v: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        if not v:
            raise ValueError("Assignment darf nicht leer sein.")
        return v


class SeedCaseRead(BaseModel):
    """REQ-6009: Seed-Testfall zum Lesen."""
    id: int
    seed_set_id: int
    assignment: Dict[str, Optional[str]]
    order_index: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        import json as json_mod
        data = obj.__dict__.copy()
        data["assignment"] = json_mod.loads(obj.assignment_json)
        data.pop("assignment_json", None)
        return cls(**data)


class SeedSetCreate(BaseModel):
    """REQ-6009: Seed-Satz anlegen."""
    name: str = Field(min_length=1, max_length=300)
    seeds: List[Dict[str, Optional[str]]] = []

    @field_validator("name")
    @classmethod
    def name_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name darf nicht leer oder nur Leerzeichen sein.")
        return v.strip()

    @field_validator("seeds")
    @classmethod
    def seeds_max_count(cls, v: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
        if len(v) > MAX_SEEDS_PER_SET:
            raise ValueError(f"Maximal {MAX_SEEDS_PER_SET} Seeds pro Satz erlaubt.")
        return v


class SeedSetUpdate(BaseModel):
    """REQ-6009: Seed-Satz aktualisieren (teilweise)."""
    name: Optional[str] = None
    seeds: Optional[List[Dict[str, Optional[str]]]] = None

    @field_validator("name")
    @classmethod
    def name_not_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name darf nicht leer oder nur Leerzeichen sein.")
        return v.strip() if v else v

    @field_validator("seeds")
    @classmethod
    def seeds_max_count(cls, v: Optional[List[Dict[str, Optional[str]]]]) -> Optional[List[Dict[str, Optional[str]]]]:
        if v is not None and len(v) > MAX_SEEDS_PER_SET:
            raise ValueError(f"Maximal {MAX_SEEDS_PER_SET} Seeds pro Satz erlaubt.")
        return v


class SeedSetRead(BaseModel):
    """REQ-6009: Seed-Satz zum Lesen."""
    id: int
    project_id: int
    name: str
    created_at: str
    updated_at: str
    seed_cases: List[SeedCaseRead] = []
    seed_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SeedSetListRead(BaseModel):
    """REQ-6009: Kurzinfo fuer Uebersicht."""
    id: int
    name: str
    seed_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class SeedCSVImportResponse(BaseModel):
    """REQ-6009: Antwort nach CSV-Import."""
    seed_set_id: int
    seed_count: int
    warnings: List[str] = []


class SeedGenerateResponse(BaseModel):
    """REQ-6009: Antwort nach Seed-Generierung."""
    generation_id: int
    count: int
    seeds_count: int
    supplemented_count: int
    coverage_before: float
    coverage_after: float
    warnings: List[str] = []
    report: dict = {}


class GapFillRequest(BaseModel):
    """REQ-6009: Lueckenschluss-Request."""
    strategy: str = "pairwise"
    t_strength: Optional[int] = Field(default=None, ge=1, le=10)
    apply_rules: bool = False

    @field_validator("t_strength", mode="before")
    @classmethod
    def resolve_t_strength(cls, v):
        if v is None:
            return 2
        return v


class GapFillResponse(BaseModel):
    """REQ-6009: Antwort nach Lueckenschluss."""
    new_generation_id: int
    old_generation_id: int
    count: int
    supplemented_count: int
    coverage_before: float
    coverage_after: float
    warnings: List[str] = []
    report: dict = {}
