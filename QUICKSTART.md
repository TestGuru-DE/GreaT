# G.R.E.A.T. – Schnellstart

> Voraussetzung: Installation abgeschlossen (siehe **INSTALLATION.md**)

---

## System starten

### Einfachste Methode: Doppelklick auf Start.bat

Doppelklick auf die Datei **`Start.bat`** im Projektordner.

Es oeffnen sich 2 Terminalfenster:
- **GREAT Backend** – FastAPI auf Port 8000
- **GREAT Frontend** – Vite Dev-Server auf Port 5173

Dann Browser oeffnen: **http://localhost:5173**

---

### Manuell starten (2 Terminals)

**Terminal 1 – Backend:**
```cmd
cd C:\...\GreaT
set PYTHONPATH=src
python -m uvicorn src.app.main:app --reload --port 8000
```

**Terminal 2 – Frontend (Entwicklermodus mit Hot-Reload):**
```cmd
cd C:\...\GreaT\frontend
npm run dev
```

Browser: **http://localhost:5173**

---

### Nur Backend (kein Node.js noetig)

Wenn `npm run build` bereits ausgefuehrt wurde (Production-Build vorhanden):

```cmd
cd C:\...\GreaT
set PYTHONPATH=src
python -m uvicorn src.app.main:app --reload --port 8000
```

Browser: **http://localhost:8000**

> FastAPI liefert den React-Build direkt aus. Kein zweites Terminalfenster noetig.

---

## Adressen im Browser

| Adresse | Inhalt |
|---|---|
| `http://localhost:8000` | React-App (ueber FastAPI) |
| `http://localhost:5173` | React-App (direkter Dev-Server) |
| `http://localhost:8000/docs` | API-Dokumentation (Swagger UI) |
| `http://localhost:8000/ui/projects` | Klassische Ansicht (HTMX) |

---

## Erste Schritte in der App

### 1. Projekt anlegen
- Startseite oeffnen
- Namen eingeben und auf **Anlegen** klicken

### 2. Kategorien und Werte definieren
- Projekt anklicken → **Oeffnen**
- Linke Spalte: Kategoriename eingeben, **+** klicken
- Kategorie aufklappen (Pfeil), Werte hinzufuegen

### 3. Testfaelle generieren
- Rechte Spalte: Strategie waehlen
- **Generieren** klicken
- Ergebnis erscheint als Tabelle
- Export als **JSON**, **Excel** oder **CSV** moeglich

---

## Tastenkuerzel

| Tastenkuerzel | Aktion |
|---|---|
| **STRG + N** | Neue Kategorie (Fokus auf Eingabefeld) |
| **DEL** | Ausgewaehlte Kategorie loeschen |
| **Doppelklick** | Kategorie oder Wert umbenennen |
| **Rechtsklick** | Kontextmenue oeffnen |
| **Enter** | Eingabe bestaetigen |
| **ESC** | Eingabe abbrechen |
| **Spaltenheader klicken** | Testfalltabelle sortieren |

---

## System stoppen

Beide Terminalfenster schliessen oder jeweils **STRG + C** druecken.

---

## Fehlerbehebung

| Problem | Loesung |
|---|---|
| Port 8000 belegt | `netstat -ano \| findstr :8000` → Prozess beenden |
| `pip` nicht gefunden | Python neu installieren, "Add to PATH" aktivieren |
| `npm` nicht gefunden | Node.js neu installieren, "Add to PATH" aktivieren |
| Seite leer / weisser Bildschirm | `cd frontend && npm run build` erneut ausfuehren |
| `ModuleNotFoundError` | `pip install -r requirements.txt` erneut ausfuehren |
| Datenbankfehler | `great.db` loeschen – wird beim Neustart automatisch neu angelegt |