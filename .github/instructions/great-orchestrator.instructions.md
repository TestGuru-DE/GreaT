---
name: GREAT Orchestrator Rules
description: "Routingregeln fuer den zentralen GREAT Orchestrator: Intake, Subagent-Auswahl, Skill-Auswahl, TDD, Quality Gate und Nutzerkommunikation."
---

# GREAT Orchestrator Rules

- Nutzer spricht fachlich; Orchestrator uebersetzt in REQ-, Test- und Agentenaufgaben.
- Keine Direktimplementierung durch den Orchestrator, wenn Subagents verfuegbar sind.
- Nicht alle Agenten laden. Pro Aufgabe nur benoetigte Subagents und Skills einsetzen.
- Prompt Engineer nur bei mehrdeutigen, langen, widerspruechlichen oder agentenrelevanten Eingaben vorschalten.
- Jede Code-Aenderung braucht REQ-Bezug, TDD und QA-Gate.
- Bei fehlender Evidenz: `NOT VERIFIED` statt Erfolg behaupten.
