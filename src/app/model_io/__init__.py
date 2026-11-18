"""REQ-6013: model_io - Export/Import/Validierung/Diff des Testmodells.

Public API:
- export_model(db, project_id) -> GreatModel
- validate_model(data) -> List[ValidationError]
- diff_model(db, project_id, data) -> diff result
- apply_model(db, project_id|None, content, format) -> Project
- to_yaml(model) -> str
- to_json(model) -> str
- from_yaml(yaml_str) -> GreatModel
- from_json(json_str) -> GreatModel
"""
from .exporter import export_model
from .validator import validate_model, ValidationError
from .differ import diff_model
from .applier import apply_model
from .serializers import to_yaml, to_json, from_yaml, from_json
from .models import GreatModel, ModelCategory, ModelValue, ModelRule

__all__ = [
    "export_model",
    "validate_model",
    "ValidationError",
    "diff_model",
    "apply_model",
    "to_yaml",
    "to_json",
    "from_yaml",
    "from_json",
    "GreatModel",
    "ModelCategory",
    "ModelValue",
    "ModelRule",
]