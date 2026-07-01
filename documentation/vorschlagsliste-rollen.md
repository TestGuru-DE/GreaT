# G.R.E.A.T. – Vorschlagsliste der Rollen (Stand 2026-06-29)

## Gesammelt aus Rollen-Perspektiven

---

### 🎯 Program Manager

**Vorschläge:**
- **Projekt-Vorlagen (Templates)**: Ein Projekt als Vorlage markieren. Neues Projekt kann daraus erstellt werden (Kategorien, Werte, Regeln werden übernommen). → Spart Zeit bei ähnlichen Projekten.
- **Regelsets exportieren/importieren**: Regelkonfiguration eines Projekts als JSON exportieren und in anderes Projekt importieren.
- **Projekt-Dashboard**: Übersichtsseite pro Projekt (Anzahl Kategorien, Werte, Regeln, Generierungen, offene Warnungen).
- **Fortschritts-Indikator**: Ampel-Status pro Projekt (z. B. Rot = Regelwidersprüche vorhanden, Gelb = tote Werte, Grün = alles OK).

---

### 🏛️ Chief Architect

**Vorschläge:**
- **REST-API Versionierung**: `/api/v1/` Präfix einführen bevor externe Konsumenten entstehen.
- **Audit-Log**: Wer hat wann was geändert (Kategorie angelegt, Regel gelöscht, Generierung erstellt)? Vorbereitung für Multi-User.
- **Pagination für Generierungen**: Bei großen Projekten (>100 Generierungen) Paginierung einbauen.
- **Konfigurierbarer DB-Pfad**: Über Umgebungsvariable `GREAT_DB_PATH` steuerbar (wichtig für Raspberry Pi / Docker).

---

### 🧪 Senior QA Director

**Vorschläge:**
- **Test-Coverage-Analyse**: Nach der Generierung anzeigen welcher Prozentsatz der theoretisch möglichen Kombinationen abgedeckt ist.
- **Testfall-Kommentar**: Jeder Testfall kann einen Freitext-Kommentar bekommen (z. B. „Bekannter Bug", „Priorisiert").
- **Generierungs-Vergleich**: Zwei Generierungen desselben Projekts nebeneinander vergleichen – welche Testfälle neu/weggefallen sind.
- **Fehlerwert-Report**: Export eines separaten Reports der nur Fehlerwert-Testfälle enthält.

---

### 💻 Senior Developer

**Vorschläge:**
- **Undo/Redo**: Für Kategorie- und Wertoperationen (Ctrl+Z / Ctrl+Y). Besonders hilfreich bei versehentlichem Löschen.
- **Massenimport von Kategorien**: CSV-Upload um viele Kategorien und Werte auf einmal anzulegen.
- **Wert-Sortierung per Drag & Drop in Kategorien**: Bereits vorbereitet (order_index vorhanden), aber noch nicht im Frontend.
- **Keyboard-Navigation in Generierungstabelle**: Pfeiltasten, Tab, Enter für schnellere Bedienung ohne Maus.

---

### 📐 Combinatorics Expert

**Vorschläge:**
- **Kombinatorische Abdeckungsanzeige**: N-Wise Coverage-Metrik (1-wise = each, 2-wise = pairwise) nach Generierung anzeigen.
- **Orthogonale Arrays (OA) als Strategie**: Echte OA-Matrizen (Taguchi) als zusätzliche Strategie neben Pairwise.
- **Constraint-Komplexitätsmessung**: Bei REQ-3015 (toter Wert) Einschränkung auf einfache Fälle da vollständige Constraint-Propagation NP-hard ist bei großen Regelsets.
- **Testfall-Gewichtung**: Risikogewichtete Sortierung (höchstes kumuliertes Risiko der Werte = erster Testfall).

---

### 🎨 UX Lead

**Vorschläge:**
- **Manuelle Kombinatorik als Tabellengitter**: REQ-3016 sollte eine echte Tabelle sein (wie Excel), mit Zellen-Navigation (Tab/Enter).
- **Wert-Suche in Kategorien**: Suchfeld über der Werteliste bei großen Kategorien (>10 Werte).
- **Responsive Verbesserungen**: Mobile-Ansicht für Tablet-Nutzung (Review von Testfällen unterwegs).
- **Dark Mode**: Optionaler Dark Mode (über Einstellungen, die bereits als Leerseite existieren).
- **Onboarding-Tour**: Kurze geführte Einführung für Erstnutzer (Schritt-für-Schritt durch Projekt anlegen → Kategorien → Generieren).

---

### 🔒 Security Architect

**Vorschläge:**
- **Input-Sanitization Audit**: Sicherstellen dass alle Freitexteingaben (Projektname, Kategoriename, Werte) HTML/Script-Injection verhindern.
- **Rate Limiting**: Generierungsendpunkt sollte bei sehr großen Projekten (>1000 Kombinationen) begrenzt werden.
- **Datei-Export Sicherheit**: Sicherstellen dass Excel-Export (openpyxl) keine Makros oder externe Verlinkungen erzeugt.

---

### ⚙️ DevOps Engineer

**Vorschläge:**
- **Docker-Container**: `Dockerfile` + `docker-compose.yml` für einfache Installation (besonders für Raspberry Pi).
- **Health-Check-Endpoint**: `GET /health` mit DB-Status, Version, Uptime.
- **Automatischer DB-Backup**: Täglicher SQLite-Backup via Cron-Job oder startup-Routine.
- **Konfigurierbarer Port**: Port über Umgebungsvariable `GREAT_PORT` (Default 8000).

---

### ✍️ Technical Writer

**Vorschläge:**
- **In-App Hilfe**: Kontextbezogene Hilfetexte (Tooltip-Bubbles) für komplexe Felder (z. B. was ist Pairwise genau?).
- **CHANGELOG.md**: Automatisch aus Git-Commits generiertes Änderungsprotokoll.
- **API-Dokumentationsseite**: Ergänzung der Swagger-Docs mit Beispielen für häufige Workflows.

---

## Zusammenfassung: Top-Kandidaten für nächste Phasen

| Vorschlag | Rolle | Aufwand | Mehrwert |
|---|---|---|---|
| Undo/Redo | Developer | M | ⭐⭐⭐ |
| Docker/Raspberry Pi | DevOps | S | ⭐⭐⭐ |
| Projekt-Vorlagen | PM | M | ⭐⭐⭐ |
| Test-Coverage-Anzeige | QA | M | ⭐⭐⭐ |
| Drag & Drop Wert-Sortierung | Developer | S | ⭐⭐ |
| Wert-Suche in Kategorien | UX | S | ⭐⭐ |
| Health-Check-Endpoint | DevOps | XS | ⭐⭐ |
| Onboarding-Tour | UX | L | ⭐⭐ |
| Massenimport CSV | Developer | M | ⭐⭐ |
| Risikogewichtete Sortierung | Combinatorics | M | ⭐⭐ |
| Testfall-Kommentar | QA | S | ⭐⭐ |
| Dark Mode | UX | M | ⭐ |
| Regelsets exportieren | PM | M | ⭐⭐ |
| In-App Hilfe | TechWriter | L | ⭐⭐ |

*Aufwand: XS=<1h, S=1-4h, M=1-2 Tage, L=3-5 Tage*