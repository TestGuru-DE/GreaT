---
name: GREAT Security Rules
description: Regeln fuer Security Reviews, OWASP, Secrets, CORS, Auth/AuthZ, Input-Validierung, Dependencies und sichere Defaults.
applyTo: "{src/app/**,src/backend/**,frontend/src/**,.github/workflows/**,requirements*.txt,Start.*}"
---

# GREAT Security Rules

- Keine Secrets, Tokens, API-Keys oder produktiven Zugangsdaten im Repo.
- CORS, Debug-Modus und offene Endpunkte bewusst bewerten.
- API-Payloads, Dateiimporte und Query-Parameter validieren.
- Kein Raw SQL; ORM und Parametrisierung nutzen.
- Dependencies auf Lizenz, Maintenance und bekannte Sicherheitsrisiken pruefen.
- Auth/AuthZ-Features nur mit REQ/ADR und Tests einfuehren.
