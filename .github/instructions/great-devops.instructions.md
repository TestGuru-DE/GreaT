---
name: GREAT DevOps Rules
description: Regeln fuer CI/CD, reproduzierbare Tests, Build, Startskripte, Packaging, Raspberry-Pi-Kompatibilitaet und Repo-Hygiene.
applyTo: "{.github/workflows/**,requirements*.txt,pytest.ini,.coveragerc,Start.*,Dockerfile,docker-compose*.yml,frontend/package*.json,frontend/vite.config.ts}"
---

# GREAT DevOps Rules

## Prueffelder
- Python: `python -m pytest`, Coverage, Importpfade, requirements.
- Frontend: `npm test`, `npm run build`, `npm run lint` falls eingerichtet.
- Start: `Start.bat` und `Start.sh` muessen nachvollziehbar und ohne lokale absolute Pfade sein.
- CI/CD: reproduzierbare Checks, keine Secrets, keine lokalen Artefakte.
- Repo-Hygiene: keine `node_modules`, `dist`, DBs, Caches, `__pycache__`, `.pytest_cache`.

## Sicherheits-/Release-Regeln
- Keine Secrets in Scripts oder Config.
- Keine manuelle Freigabe ohne dokumentierte Tests.
- Raspberry-Pi-Kompatibilitaet beachten, wenn Server-/Deployment-Pfade betroffen sind.
