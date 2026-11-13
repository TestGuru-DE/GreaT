# G.R.E.A.T. Review Checklist

## Architecture
- No business logic in FastAPI routers.
- Router -> Service -> Repository -> DB is preserved.
- No raw SQL; SQLAlchemy ORM only.
- `src/app/main.py` stays small and only wires application setup.
- No circular imports.

## Testing
- New behavior has tests first.
- Tests include or reference `REQ-XXXX`.
- RED was observed before implementation where feasible.
- Changed code has meaningful branch coverage.

## Requirements
- Existing REQ was reused when possible.
- New REQ was not invented silently.
- Status and traceability were updated after implementation.

## Security
- No secrets, tokens, passwords, or local DB files committed.
- Inputs are validated through schemas or explicit validation.
- No production debug mode.
- CORS is not widened without explicit approval.

## UX / user impact
- User-visible behavior is described in German documentation.
- Error messages are understandable.
- Existing workflows are not broken.

## Repository hygiene
- Do not commit `.pytest_cache`, `__pycache__`, virtual environments, database files, or generated build outputs unless explicitly required.
