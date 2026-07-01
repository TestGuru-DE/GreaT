# Phase 3 Sprint 4 – Planning Summary
**Finales Planning-Dokument für Sprint 4 Start**

**Datum:** 2026-07-01  
**Phase:** 3 (React-First + HTMX-Ablösung)  
**Status:** ✅ **GO FOR SPRINT-START**  

---

## 🎯 Executive Summary (für Product Owner)

**Was wird in Sprint 4 umgesetzt?**
1. **Grenzwertanalyse-Dialog** (REQ-3041) – Benutzerfreundliche Maske für numerische Grenzen
2. **Regelengine-Refactor** (REQ-3040) – Geschäftsregeln werden während Generierung berücksichtigt
3. **T-Wise Vorbereitung** (REQ-3039) – Basis für flexible N-Weise Testfall-Generierung
4. **MCDC-Grundlage** (REQ-3044) – Vorbereitung für Entscheidungslogik-Tests

| **Metrik** | **Wert** |
|---|---|
| **Sprint-Dauer** | 2 Wochen (ca. 2026-07-02 bis 2026-07-16) |
| **Team-Kapazität** | ~150 Story Points |
| **Geplanter Scope** | ~150 SP (**100% Auslastung = Tight!**) |
| **Status** | Alle Requirements Refinement-Ready |
| **Risiken** | 4 bekannt, alle mit Mitigationen |

**Bottom Line:** Sprint 4 fokussiert auf **Kernalgorithmik + BVA-UX**. Komplex, aber machbar.

---

## 📊 Backlog-Refinement: Abgeschlossen ✅

**Sondierung der letzten 3 Wochen:**
- ✅ **20 Backlog-Items** aus Vorschlagsliste (REQ-3019–3038)  
- ✅ **6 neue Requirements** aus Rollen-Interviews (REQ-3039–3044)  
- ✅ **2 Tech-Entscheidungen** getroffen (Dezimal.js, BVA-Input-Strategie)  
- ✅ **Alle Dependencies** dokumentiert (REQ-3040 blockt 5 andere)  

**Qualität des Refinements:**
- ✅ User Stories mit Acceptance Criteria  
- ✅ Story-Point-Schätzung validiert  
- ✅ Risiken identifiziert (Scores >= 10)  
- ✅ Tech-Schulden katalogisiert  

---

## 🔧 Tech-Entscheidungen (ADRs)

### ✅ ADR-009: Dezimal.js für exakte Numerik
**Entscheidung:** Dezimal.js nutzen (Python + JavaScript)  
**Grund:** 0.1 + 0.2 = 0.3 exakt (sonst 0.30000000001)  
**Impact:** +10KB npm, +50KB Python, aber korrekte Grenzwertberechnung  

### ✅ ADR-010: BVA Min/Max ohne Auto-Prefill
**Entscheidung:** Benutzer füllt Min/Max manuell (leere Felder)  
**Grund:** Explizit > Implizit. Benutzer hat volle Kontrolle, keine versteckten Annahmen  
**Impact:** Einfachere UI, Benutzer muss weniger Metadaten pflegen  

---

## 🎬 Sprint 4 Requirements (4 Items, ~150 SP)

### Must-Have

#### **REQ-3040 | RuleEngine-Refactor** (~60 SP)
**Was:** Geschäftsregeln in alle Kombinatorik-Generatoren integrieren  
**Warum:** Bisher: Testfälle generieren → ungültige filtern. Neu: Nur gültige generieren (schneller, eleganter)  
**Dependencies:** REQ-3004, REQ-3005, REQ-0806, REQ-3015  
**Blockt:** REQ-3039, REQ-3032–3038  
**Success:** Alle bestehenden Tests bestehen, Performance <= +10% Overhead  

#### **REQ-3041 | BVA-Dialog UX** (~50 SP)
**Was:** React-Dialog zur Eingabe von Min/Max → generiert Testwerte automatisch  
**Warum:** Tester braucht intuitive Maske, nicht API-Calls  
**Dependencies:** REQ-3035 (Wireframe), REQ-0306, REQ-3042, REQ-3043  
**Success:** Dialog functional on Chrome, Firefox, Edge. Live-Vorschau funktioniert. Dezimal.js liefert korrekte Werte.  

---

### Should-Have (Hochgestuftes Backlog)

#### **REQ-3039 | T-Wise Algorithmus** (~35 SP)
**Status:** Hochgestuft von Phase 4 (Combinatorics Expert Empfehlung)  
**Was:** N-Weise Testfall-Generierung (3-Weise, 4-Weise, flexibel)  
**Abhängig von:** REQ-3040 muss VOR REQ-3039 done sein  
**Sprint 4 Scope:** Planung & Analyse (25 SP). Finish Sprint 5 (10 SP).  

#### **REQ-3044 | MCDC-Algorithmus** (~40 SP)
**Status:** Should – Hintergrund-Feature  
**Was:** Modified Condition/Decision Coverage für komplexe Bedingungen  
**Sprint 4 Scope:** Basis + Tests (15 SP). Finish Sprint 5 (25 SP).  

---

## 💼 Effort & Kapazität

\\\
Sprint 4 Workload:
  REQ-3040 (RuleEngine)  ████████████████████░░░░░░░░░  60 SP
  REQ-3041 (BVA-Dialog)  █████████████░░░░░░░░░░░░░░░░  50 SP
  REQ-3039 (T-Wise Plan) ███████░░░░░░░░░░░░░░░░░░░░░░  25 SP
  REQ-3044 (MCDC Basis)  ███░░░░░░░░░░░░░░░░░░░░░░░░░░  15 SP
  ─────────────────────────────────────────────────────
  TOTAL:                 ███████████████████████████████  150 SP ✅
\\\

**Team Capacity:** 150 SP → 100% Auslastung (KEIN PUFFER!)

---

## ✅ Success Criteria & Quality Gates

| Kriterium | Ziel | Owner |
|---|---|---|
| Unit-Test-Coverage (REQ-3040) | >= 95% | Dev + QA |
| Regression-Tests bestanden | 100% | QA |
| Dezimal.js-Precision | 100% exakt | QA |
| Performance <= +10% | Validiert | Load-Test |
| BVA-Dialog E2E-Tests | Alle grün | QA |

---

## ⚠️ Known Risks & Mitigations

| Risk | Score | Maßnahme |
|---|---|---|
| RuleEngine-Komplexität | 20 | TDD, Mathematische Verifikation, Code-Review |
| Dezimal.js-Integration | 12 | Unit-Tests, Fallback Python decimal |
| REQ-3040-Blockade | 16 | REQ-3041 parallel, Daily Tracking |
| main.py Monolith | 20 | Phase 4 geplant, keine neuen Features in main.py |

---

## 🚀 Sprint Timeline

**Vor Sprint-Start:** Kickoff, Architektur-Review, Test-Strategie  
**Woche 1:** REQ-3040 (40%), REQ-3041 (30%), Dezimal.js-Validierung  
**Woche 2:** REQ-3040 (100%), REQ-3041 (100%), REQ-3039+3044 Planung  
**Sprint-Ende:** Sprint-Review, Demo, Retrospektive  

---

**Gültig:** 2026-07-01  
**Program Manager Freigabe:** ✅ GO FOR SPRINT-START  
