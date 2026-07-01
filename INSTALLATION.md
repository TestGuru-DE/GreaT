# G.R.E.A.T. – Installationsanleitung

**G.R.E.A.T.** (Georg Radikal Einfacher Automatisierter TestcaseDesigner)  
Testfall-Design-Tool fuer strukturierte Aequivalenzklassen und Kombinatorik-Strategien.

---

## Voraussetzungen

| Software | Mindestversion | Download |
|---|---|---|
| **Python** | 3.10 | https://www.python.org/downloads/ |
| **Node.js** | 20 LTS | https://nodejs.org/en/download (LTS waehlen) |
| **Git** | beliebig | https://git-scm.com/downloads |
| **Browser** | aktuell | Chrome, Firefox oder Edge |

> **Hinweis:** Python und Node.js muessen im Windows-PATH eingetragen sein.  
> Der Installer erledigt das automatisch, wenn "Add to PATH" aktiviert ist.

---

## Schritt 1 – Repository herunterladen

```cmd
git clone https://github.com/TestGuru-DE/GreaT.git
cd GreaT
```

Oder als ZIP: Grünen Button **"Code" → "Download ZIP"** auf GitHub klicken, entpacken.

---

## Schritt 2 – Python-Abhaengigkeiten installieren

```cmd
pip install -r requirements.txt
```

> Empfehlung: Virtuelle Umgebung verwenden (optional, aber sauber):
> ```cmd
> python -m venv .venv
> .venv\Scripts\activate
> pip install -r requirements.txt
> ```

---

## Schritt 3 – Frontend-Abhaengigkeiten installieren

```cmd
cd frontend
npm install
cd ..
```

> Dieser Schritt laedt alle React/TypeScript-Pakete herunter (~100 MB).  
> Einmalig ausfuehren – dauert je nach Verbindung 1-3 Minuten.

---

## Schritt 4 – Frontend bauen (einmalig)

```cmd
cd frontend
npm run build
cd ..
```

> Erzeugt den Production-Build unter `frontend/dist/`.  
> FastAPI liefert diesen automatisch aus.  
> **Nach jedem Update des Quellcodes** erneut ausfuehren.

---

## Installation abgeschlossen

Weiter zur **QUICKSTART.md** fuer Startanleitung.