# G.R.E.A.T. â€“ Schnellstart

> **Zwei Startoptionen:** Portable EXE (Endnutzer) oder Entwickler-Modus

---

## Option 1: Portable EXE (Endnutzer)

> **Keine Entwickler-Tools erforderlich!**

### Starten

1. **Doppelklick auf `GREAT.exe`**
2. Der Browser oeffnet sich automatisch auf `http://localhost:8000`
3. Falls der Browser nicht oeffnet: Manuel zu `http://localhost:8000` navigieren

### Stoppen

- **Task-Manager** (STRG + SHIFT + ESC)
- Prozess **GREAT.exe** auswÃ¤hlen
- **Aufgabe beenden** klicken

### Daten

- Datenbank: `%USERPROFILE%\.great\great.db` (automatisch angelegt)
- Die Datenbank bleibt erhalten, auch nach dem Beenden
- Zum Loeschen: `%USERPROFILE%\.great\great.db` loeschen â€“ wird beim naechsten Start neu angelegt

---

## Option 2: Entwickler-Modus

> Voraussetzung: Installation abgeschlossen (siehe **INSTALLATION.md**)

### Einfachste Methode: Doppelklick auf Start.bat

Doppelklick auf die Datei **`Start.bat`** im Projektordner.

Es oeffnet sich ein Terminalfenster:
- **GREAT Backend** â€“ FastAPI auf Port 8000

Dann Browser oeffnen: **http://localhost:8000**

> `Start.bat` baut vor dem Backend-Start das Frontend neu, damit Port `8000` denselben UI-Stand wie `5173` zeigt.

---

### Manuell starten (2 Terminals)

**Terminal 1 â€“ Backend:**
```cmd
cd C:\...\GreaT
set PYTHONPATH=src
python -m uvicorn src.app.main:app --reload --port 8000
```

**Terminal 2 â€“ Frontend (Entwicklermodus mit Hot-Reload):**
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
- Projekt anklicken â†’ **Oeffnen**
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

| Modus | Stoppen |
|---|---|
| **Portable EXE** | Task-Manager â†’ GREAT.exe beenden |
| **Start.bat** | Terminalfenster schliessen oder STRG + C |
| **Manuell** | Beide Terminals: STRG + C |

---

## Fehlerbehebung

| Problem | Loesung |
|---|---|
| Port 8000 belegt | `netstat -ano \| findstr :8000` â†’ Prozess beenden |
| `pip` nicht gefunden | Python neu installieren, "Add to PATH" aktivieren |
| `npm` nicht gefunden | Node.js neu installieren, "Add to PATH" aktivieren |
| Seite leer / weisser Bildschirm | `cd frontend && npm run build` erneut ausfuehren |
| `ModuleNotFoundError` | `pip install -r requirements.txt` erneut ausfuehren |
| Datenbankfehler | `great.db` loeschen â€“ wird beim Neustart automatisch neu angelegt |
| GREAT.exe startet nicht | Windows Defender/Firewall kann blockieren â€“ Ausnahme hinzufuegen |
| Browser oeffnet sich nicht | Manuel zu `http://localhost:8000` navigieren |