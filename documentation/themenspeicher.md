# G.R.E.A.T. – Themenspeicher (Geparkte Themen)

> Themen die vorerst nicht umgesetzt werden, aber nicht verloren gehen sollen.
> Kann jederzeit reaktiviert werden.

---

## 🍓 Raspberry Pi & Deployment (pausiert seit 2026-06-29)

**Entscheidung:** Deployment auf Raspberry Pi ist vorerst pausiert.
**Reaktivierung:** Nach Stabilisierung der Kernfunktionalität.

### Geparkte Vorschläge aus der Vorschlagsliste

| ID | Vorschlag | Original-Quelle |
|---|---|---|
| V4 | Konfigurierbarer Port via `GREAT_PORT` Umgebungsvariable | DevOps |
| V15 | Docker-Container + `docker-compose.yml` für Raspberry Pi | DevOps |

### Geparkte Requirements

| REQ | Titel | Status |
|---|---|---|
| REQ-0010 | Raspberry Pi 4/5 Kompatibilität (ARM64, Raspberry Pi OS) | ⏸ Pausiert |

### Technische Notizen für spätere Reaktivierung
- Python 3.10+ läuft nativ auf ARM64 (Raspberry Pi OS 64-bit)
- FastAPI + SQLite benötigen keine Anpassungen für ARM
- `aarch64`-Build von openpyxl verfügbar via pip
- Empfehlung: `uvicorn --host 0.0.0.0 --port $GREAT_PORT` + systemd-Unit-Datei
- Docker Base Image: `python:3.12-slim` läuft auf ARM64

---

## 🎓 Onboarding-Tour / In-App Guided Tour (geparkt seit 2026-07-01)

**Entscheidung:** Interaktive Onboarding-Tour wird nach UX-Studien und Nutzerfeedback priorisiert.
**Reaktivierung:** Nach Stabilisierung der Kernfunktionalität (Phase 3); geplante Umsetzung Phase 4–5.

### Geparkte Vorschläge aus der Vorschlagsliste

| ID | Vorschlag | Original-Quelle |
|---|---|---|
| V16 | Onboarding-Tour: Kurze geführte Einführung für Erstnutzer (Schritt-für-Schritt durch Projekt anlegen → Kategorien → Generieren) | UX Lead |

### Geparkte Requirements

Keine spezifischen Requirements derzeit – abhängig von UX-Evaluationsergebnissen.

### Szenario & Nutzen

**Zielgruppe:** Erstnutzer, die zum ersten Mal GreaT öffnen.

**Tour-Ablauf (beispielhafte Schritte):**
1. Willkommensdialog: „Willkommen zu GreaT – Kombinatorische Testfall-Generierung"
2. Schritt 1: Projekt anlegen (mit Highlight auf „Neues Projekt"-Button)
3. Schritt 2: Kategorie hinzufügen (z. B. „Browser" mit Werten: Chrome, Firefox, Safari)
4. Schritt 3: Zweite Kategorie hinzufügen (z. B. „OS" mit Werten: Windows, macOS, Linux)
5. Schritt 4: Generierung starten (mit Erklärung „Pairwise-Strategie")
6. Schritt 5: Testfälle anschauen und exportieren
7. Abschluss: „Tour abgeschlossen – weitere Hilfe unter Dokumentation"

**Mehrwert:**
- Reduziert Einstiegshürde für neue Nutzer
- Verbessert Erstnutzer-Erlebnis und Akzeptanz
- Ermöglicht Nutzer, ohne externe Tutorials zurechtzukommen

### Abhängigkeiten & Vorbedingungen

- **Phase 3 (aktuell):** Kern-Features (Projektverwaltung, Kategorien, Generierung) stabil ✓
- **Phase 4–5 (geplant):** Basis-UX-Verbesserungen (Responsive Design, Mobile-Support) sollten zuerst implementiert sein
- **UX-Studien erforderlich:** Bevor Umsetzung startet, sollten 3–5 Erstnutzer die Tour testen und Feedback geben
- **Abhängigkeiten zu anderen geparken Themen:**
  - Optional kombinierbar mit V-Dark Mode (Theme-Voreinstellung vor Tour)
  - Optional kombinierbar mit In-App Hilfe (V-InAppHilfe) für tiefere Erklärungen nach Tour
  
### Technische Hinweise für spätere Implementierung

- **Bibliothek-Empfehlung:** z. B. Shepherd.js (Browser-Tour) oder Driver.js für Focus-Highlights
- **State Management:** Tour-Status in LocalStorage speichern: `great_onboarding_completed: true/false`
- **Abbrechen/Überspringen:** Nutzer können Tour jederzeit abbrechen; nur beim Erstbesuch automatisch starten
- **Mehrsprachigkeit:** Tour muss mit i18n-System kompatibel sein (Deutsch, Englisch)
- **Tracking (optional):** Welche Schritte wurden abgeschlossen? Wo brechen Nutzer ab?

---

*Weitere geparkte Themen werden hier ergänzt.*