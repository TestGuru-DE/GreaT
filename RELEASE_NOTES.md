# G.R.E.A.T. v1.0.0 – Release Notes
**Release-Datum:** 2026-07-01  
**Codename:** Fresh Start

## Willkommen zu G.R.E.A.T.

**G.R.E.A.T.** (Georg Radikal Einfacher Automatisierter TestcaseDesigner) ist ein Open-Source-Tool zur systematischen Generierung von Testfällen mit modernen Kombinatorik-Verfahren.

## Wichtiger Hinweis zu diesem Release

Dies ist das **erste öffentliche Release** von G.R.E.A.T. Die Vorgänger-Software „Tanos" wurde komplett überarbeitet:

- Kompletter Rewrite von Grund auf
- Neuer Name: Tanos → G.R.E.A.T.
- Neue Architektur: Web-App statt Desktop-Anwendung
- Neue Technologien: Python/FastAPI + React/TypeScript
- Neue Lizenz: AGPL-3.0 mit Dual-Licensing für kommerzielle Nutzung
- Deutlich erweiterter Funktionsumfang

Die alte Git-History ist nicht mehr relevant und wurde bewusst nicht übernommen. Nutzer der Vorgängerversion betrachten G.R.E.A.T. bitte als komplett neues Tool – es existiert kein Upgrade-Pfad von Tanos.

## Features v1.0.0

### Projektmanagement
- Testprojekte mit Kategorien und Werten
- Wert-Eigenschaften: Risiko-Gewicht (1–10), Datentyp, Fehlerwert-Kennzeichnung, Default-Markierung
- Massenimport und Massenlöschung

### Regellogik
- 3 Regeltypen: **Verboten** (Paar), **Abhängig** (Wenn-Dann), **Kombinieren** (Fan-out)
- Automatische Widerspruchs-Erkennung
- Regel-Anwendung optional bei der Testfall-Generierung

### Kombinatorik
- **Each-Choice:** Jeder Wert mindestens einmal
- **Pairwise:** Alle Wertepaare abgedeckt
- **Lineare Expansion:** Kartesisches Produkt
- **Manuelle Kombinatorik:** Nutzer stellt Testfälle selbst zusammen
- **Grenzwertanalyse (BVA):** Backend-Endpoint (Frontend-Dialog in v1.1 geplant)

### Datenklassen
- **System-Datenklassen:** Vordefinierte Äquivalenzklassen (Grenzwerte, Zahlen, Datum, URLs, etc.)
- **User-Datenklassen:** Selbst erstellbar mit Typ-Validierung
- Direkt in Kategorien nutzbar via „Datenklasse einfügen"

### Export
- CSV, JSON, Excel
- Historie aller Generierungen pro Projekt
- Editierbare Generierungs-Namen

## Installation

```bash
# Backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn src.app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Details in [README.md](README.md).

## Roadmap – Was kommt als Nächstes?

### Phase 3 Sprint 4 (in Vorbereitung, geplant 2026-07-02 bis 2026-07-16)
- **REQ-3040** RuleEngine-Refactor: Constraint-aware Testfall-Generierung
- **REQ-3041** Grenzwertanalyse-Dialog (React-Frontend zur BVA)
- **REQ-3039** T-Wise Algorithmus (N-weise Kombinatorik)
- **REQ-3044** MCDC (Modified Condition/Decision Coverage)

### Sprint 5–6 Backlog
- Drag & Drop Wert-Sortierung
- Health-Check Endpoint
- Undo/Redo
- Projekt-Vorlagen
- Regelsets exportieren/importieren
- Test-Coverage-Anzeige
- Testfall-Kommentare
- Massenimport per CSV
- Risikogewichtete Testfall-Sortierung
- Wert-Suche in großen Kategorien
- Projekt-Dashboard
- Generierungs-Vergleich
- N-Wise Coverage-Metrik
- In-App Hilfe & Tooltips
- API-Versionierung
- Klassifikationsbaum-Methode
- Orthogonal Arrays
- Coverage-Gap-Closure

### Phase 4 (Zukunft)
- Authentifizierung (OAuth2/JWT)
- Multi-User mit PostgreSQL
- LLM-Integration (Ollama)
- Business Rule Based Testing

### Themenspeicher (pausiert)
- Raspberry Pi Deployment
- Interaktive Onboarding-Tour

## Lizenz und Nutzungsbedingungen

G.R.E.A.T. steht unter der **GNU Affero General Public License v3.0** (AGPL-3.0) mit einem **differenzierten Nutzungsmodell**:

### Kostenlose Nutzung

Der Einsatz von G.R.E.A.T. als **Werkzeug für den Testfall-Entwurf** ist kostenlos – auch in kommerziellen Umgebungen:

- ✅ Softwarehersteller, die eigene Produkte testen
- ✅ Interne QA-Teams
- ✅ Private, wissenschaftliche, akademische Nutzung
- ✅ Nicht-kommerzielle Open-Source-Projekte

Bei kostenloser Nutzung gelten die AGPL-3.0 Copyleft-Pflichten (Share-Alike, auch bei SaaS).

### Genehmigungspflichtige Nutzung

Wer mit G.R.E.A.T. selbst **Geld verdient**, benötigt vorherige Genehmigung und Umsatzbeteiligung:

- ❌ Consultants, die Testfälle als bezahlte Dienstleistung erstellen
- ❌ Tool-Anbieter, die G.R.E.A.T. in kommerzielle Produkte integrieren
- ❌ SaaS-Anbieter, die G.R.E.A.T. gegen Bezahlung hosten

Details: siehe [NOTICE.md](NOTICE.md) und [LICENSE](LICENSE).

**Haftung:** Nutzung auf eigene Gefahr, keinerlei Haftung durch den Autor.

## Mitwirken

Beiträge willkommen. Bitte beachten:
- Beiträge unterliegen AGPL-3.0 sowie dem differenzierten Nutzungsmodell (siehe NOTICE.md)
- Bugs & Features via GitHub Issues
- Pull Requests: Test-Coverage muss erhalten bleiben

## Kontakt

- **Repository:** https://github.com/TestGuru-DE/GreaT
- **Autor:** Georg Haupt (via GitHub)

---

**Version:** 1.0.0  
**Release-Datum:** 2026-07-01
