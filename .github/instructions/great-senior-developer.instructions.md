---
name: GREAT Developer Rules
description: Implementierungsregeln fuer Python/FastAPI, React/TypeScript, TDD, Refactoring, Clean Architecture, Performance und Repo-Hygiene.
applyTo: "{src/**,frontend/src/**,tests/**}"
---

# GREAT Developer Rules

## TDD-Ablauf
1. REQ/Scope klaeren.
2. Test zuerst oder vorhandenen Test gezielt erweitern.
3. Minimal implementieren.
4. Refactoren ohne Verhalten zu aendern.
5. Relevante Tests ausfuehren und Ergebnis melden.

## Architektur
- Router duenn halten, Logik in Services/Domain-Modulen.
- SQLAlchemy ORM statt Raw SQL.
- Code-Bezeichner Englisch, Dokumentation Deutsch.
- Type Hints fuer neue Python-Funktionen.
- React/TypeScript-Komponenten klein, testbar und fachlich benannt.

## Verbote
- Keine generierten Artefakte committen: DBs, Caches, `node_modules`, `dist`, `__pycache__`.
- Kein Scope Creep ohne Program-/Requirements-Entscheidung.
- Kein "fertig" ohne QA-Gate.
