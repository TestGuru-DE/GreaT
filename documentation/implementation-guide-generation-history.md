# Implementierungsanleitung: Generierungshistorie unveraenderlich machen (B-18)

**Status:** Implementierungsanleitung fuer GREAT Senior Developer
**ADR:** ADR-018
**REQ-ID:** B-18 (Bugfix-Scope)
**Erstellt:** 2026-11-17

---

## Problem

Wird eine Kategorie geloescht, verschwinden ihre Spalten auch aus **bereits gespeicherten**
Generierungen. Ursache: `TestCaseValue.category_id` referenziert `categories.id` mit
`ON DELETE CASCADE`.

---

## 1. Datenmodell (src/app/models/__init__.py)

### 1.1 TestCaseValue-Modell aendern

**Datei:** `src/app/models/__init__.py`, Zeilen 99-111

**Aktuell:**
```python
class TestCaseValue(Base):
    __tablename__ = "testcase_values"
    id = Column(Integer, primary_key=True)
    testcase_id = Column(Integer, ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=False)
    ...
```

**Aenderung:**
- `category_id` FK: `ondelete="CASCADE"` → `ondelete="SET NULL"` + `nullable=True`
- Neue Spalte `category_name` hinzufuegen

**Ziel:**
```python
class TestCaseValue(Base):
    __tablename__ = "testcase_values"
    id = Column(Integer, primary_key=True)
    testcase_id = Column(Integer, ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    category_name = Column(String(300), nullable=True)  # B-18: Schnappschuss des Kategorienamens
    value = Column(String(500), nullable=False)
    ...
```

**Achtung:** Die Spaltenreihenfolge ist relevant fuer SQLAlchemy ORM – `category_name`
nach `category_id` einfuegen.

---

## 2. Migration (src/app/main.py – _migrate_db())

**Datei:** `src/app/main.py`, Funktion `_migrate_db()` (ab Zeile 149)

Folge dem bestehenden Muster (PRAGMA table_info → Spaltenpruefung → ALTER TABLE → Backfill).

**Zu ergaenzen in `_migrate_db()`:**

```python
# B-18: category_name Spalte zu testcase_values hinzufuegen (idempotent)
tcv_cols = conn.exec_driver_sql("PRAGMA table_info('testcase_values')").fetchall()
tcv_have = {c[1] for c in tcv_cols}
if "category_name" not in tcv_have:
    conn.exec_driver_sql("ALTER TABLE testcase_values ADD COLUMN category_name VARCHAR(300)")
    # Backfill: category_name aus category.name befuellen
    conn.exec_driver_sql("""
        UPDATE testcase_values
        SET category_name = (SELECT name FROM categories WHERE categories.id = testcase_values.category_id)
        WHERE category_name IS NULL AND category_id IS NOT NULL
    """)
```

**Wichtig:**
- Der Backfill muss **nach** dem ALTER TABLE, aber **innerhalb** derselben Transaktion laufen
- Die Migration ist idempotent: mehrfaches Aufrufen erzeugt keine Fehler
- Teste mit `_migrate_db()` zweimal aufrufen (wie in `test_first_start_hint.py`)

---

## 3. Generierung (src/app/routers/api_generate.py – generate())

**Datei:** `src/app/routers/api_generate.py`, Zeilen 179-188

**Aktuell:**
```python
for cat in categories:
    if cat.name not in persisted_assignment:
        continue
    db.add(
        models.TestCaseValue(
            testcase_id=tc.id,
            category_id=cat.id,
            value=persisted_assignment[cat.name],
        )
    )
```

**Aenderung:** `category_name` beim Erstellen befuellen:

```python
for cat in categories:
    if cat.name not in persisted_assignment:
        continue
    db.add(
        models.TestCaseValue(
            testcase_id=tc.id,
            category_id=cat.id,
            category_name=cat.name,  # B-18: Schnappschuss
            value=persisted_assignment[cat.name],
        )
    )
```

---

## 4. Testcase-Aktualisierung (src/app/routers/api_generate.py – update_testcase_assignment)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 309-358

Wenn ein Testfall-Wert aktualisiert oder neu erstellt wird, muss `category_name` gesetzt werden.

**Aktuell (Zeilen 343-348):**
```python
if testcase_value is None:
    testcase_value = models.TestCaseValue(
        testcase_id=tcid,
        category_id=category.id,
        value=payload.value,
    )
    db.add(testcase_value)
else:
    testcase_value.value = payload.value
```

**Aenderung:**
```python
if testcase_value is None:
    testcase_value = models.TestCaseValue(
        testcase_id=tcid,
        category_id=category.id,
        category_name=category.name,  # B-18: Schnappschuss
        value=payload.value,
    )
    db.add(testcase_value)
else:
    testcase_value.value = payload.value
    # B-18: category_name aktualisieren falls Kategorie umbenannt wurde
    if testcase_value.category_name != category.name:
        testcase_value.category_name = category.name
```

---

## 5. Kategorie-Loeschung (src/app/routers/api_projects.py – delete_category)

**Datei:** `src/app/routers/api_projects.py`, Zeilen 110-118

**Aktuell:**
```python
@router.delete("/categories/{cid}", dependencies=[Depends(require_writer)])
def delete_category(cid: DbId, db: Session = Depends(get_db)):
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    db.delete(cat)
    db.commit()
    return {"ok": True, "id": cid}
```

**Aenderung:** Vor dem Loeschen alle `TestCaseValue`-Zeilen disassociieren:

```python
@router.delete("/categories/{cid}", dependencies=[Depends(require_writer)])
def delete_category(cid: DbId, db: Session = Depends(get_db)):
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    # B-18: TestCaseValue-Referenzen auf NULL setzen (nicht CASCADE-Loeschen)
    db.query(models.TestCaseValue).filter(
        models.TestCaseValue.category_id == cid
    ).update(
        {models.TestCaseValue.category_id: None},
        synchronize_session=False
    )
    db.delete(cat)
    db.commit()
    return {"ok": True, "id": cid}
```

---

## 6. force_delete_category (src/app/services.py)

**Datei:** `src/app/services.py`, Zeilen 493-501

**Aktuell:**
```python
def force_delete_category(db: Session, cid: int) -> int:
    cat = db.get(models.Category, cid)
    if not cat:
        return 0
    pid = cat.project_id
    db.query(models.TestCaseValue).filter(models.TestCaseValue.category_id == cid).delete(synchronize_session=False)
    db.query(models.Value).filter(models.Value.category_id == cid).delete(synchronize_session=False)
    db.delete(cat)
    return pid
```

**Aenderung:** DELETE durch SET NULL ersetzen:

```python
def force_delete_category(db: Session, cid: int) -> int:
    cat = db.get(models.Category, cid)
    if not cat:
        return 0
    pid = cat.project_id
    # B-18: TestCaseValue-Referenzen auf NULL setzen (nicht loeschen)
    db.query(models.TestCaseValue).filter(
        models.TestCaseValue.category_id == cid
    ).update(
        {models.TestCaseValue.category_id: None},
        synchronize_session=False
    )
    db.query(models.Value).filter(models.Value.category_id == cid).delete(synchronize_session=False)
    db.delete(cat)
    return pid
```

---

## 7. Testcase-Export (src/app/routers/api_generate.py – get_testcases)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 203-306

**Problem:** `name_by_id` wird nur aus existierenden Kategorien erstellt.
Geloeschte Kategorien sind nicht mehr in `name_by_id` – die aktuelle Logik
faellt auf `f"cat#{value_row.category_id}"` zurueck (Zeile 249).

**Aktuell (Zeilen 247-249):**
```python
for value_row in vals:
    assignments[name_by_id.get(value_row.category_id, f"cat#{value_row.category_id}")] = value_row.value
```

**Aenderung:** `category_name` als Fallback verwenden:

```python
for value_row in vals:
    cat_name = name_by_id.get(value_row.category_id)
    if cat_name is None and value_row.category_name:
        cat_name = value_row.category_name  # B-18: geloeschte Kategorie -> gespeicherter Name
    elif cat_name is None:
        cat_name = f"cat#{value_row.category_id}"  # Fallback wenn beides NULL
    assignments[cat_name] = value_row.value
```

**Zusaetzlich:** Die `assignments`-Initialisierung (Zeile 248) erstellt Platzhalter
nur fuer existierende Kategorien. Geloeschte Kategorien fehlen als Key.
Dies muss erweitert werden:

```python
# B-18: Sammle auch category_name-Werte aus TestCaseValue fuer geloeschte Kategorien
all_cat_names = set()
for value_row in vals:
    if value_row.category_name and value_row.category_name not in name_by_id.values():
        all_cat_names.add(value_row.category_name)

assignments = {category.name: "" for category in categories}
# B-18: Füge geloeschte Kategorien hinzu
for cat_name in all_cat_names:
    if cat_name not in assignments:
        assignments[cat_name] = ""
```

---

## 8. assignment_from_testcase() (src/app/services.py)

**Datei:** `src/app/services.py`, Zeilen 521-528

**Aktuell:**
```python
def assignment_from_testcase(db: Session, tc_id: int) -> Dict[str, str]:
    rows = (
        db.query(models.TestCaseValue, models.Category.name)
        .join(models.Category, models.Category.id == models.TestCaseValue.category_id)
        .filter(models.TestCaseValue.testcase_id == tc_id)
        .all()
    )
    return {cat_name: tcv.value for tcv, cat_name in rows}
```

**Problem:** Der JOIN ist ein INNER JOIN – wenn `category_id=NULL` (geloeschte Kategorie),
wird die Zeile nicht zurueckgegeben.

**Aenderung:** OUTER JOIN + Fallback auf `category_name`:

```python
def assignment_from_testcase(db: Session, tc_id: int) -> Dict[str, str]:
    from sqlalchemy import outerjoin
    rows = (
        db.query(models.TestCaseValue, models.Category.name)
        .outerjoin(models.Category, models.Category.id == models.TestCaseValue.category_id)
        .filter(models.TestCaseValue.testcase_id == tc_id)
        .all()
    )
    result = {}
    for tcv, cat_name in rows:
        # B-18: Falls Kategorie geloescht (cat_name=None), verwende gespeicherten category_name
        if cat_name is None:
            cat_name = tcv.category_name or f"cat#{tcv.category_id}"
        result[cat_name] = tcv.value
    return result
```

---

## 9. CSV-Export (src/app/routers/api_generate.py – export_generation_csv)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 361-455

**Problem:** `cat_headers` wird nur aus existierenden Kategorien erstellt (Zeilen 386-388).
Geloeschte Kategorien fehlen in den CSV-Spalten.

**Aenderung:** Die Header-Zeile muss auch `category_name` aus historischen TestCaseValue-Zeilen
beruecksichtigen. Zwei Moeglichkeiten:

**Option A (einfacher):** Nutze `assignment_from_testcase()` (nach Aenderung aus Schritt 8)
– dieser liefert jetzt auch geloeschte Kategorien. Die `cat_headers`liste muss erweitert werden.

**Option B (vollstaendig):** Sammle alle unique `category_name`-Werte aus allen TestCaseValue
der Generation und erstelle daraus die Header:

```python
# B-18: Sammle alle Kategorienamen (einschliesslich geloeschter)
tcv_rows = (
    db.query(models.TestCaseValue.category_name)
    .join(models.TestCase, models.TestCase.id == models.TestCaseValue.testcase_id)
    .filter(models.TestCase.generation_id == gen_id)
    .distinct()
    .all()
)
historical_cat_names = {row[0] for row in tcv_rows if row[0]}

# cat_headers aus existierenden Kategorien + historische
cat_headers = [c.name for c in cats]
for hname in sorted(historical_cat_names - {c.name for c in cats}):
    cat_headers.append(hname)
```

**Empfehlung:** Option B implementieren, da sie robust und explizit ist.

---

## 10. JSON-Export (src/app/routers/api_generate.py – export_generation_json)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 462-522

**Aenderung:** Analog zu Schritt 7 – `name_by_id`-Lookup erweitern um `category_name`-Fallback:

```python
for tc in testcases_db:
    vals = (
        db.query(models.TestCaseValue)
        .filter(models.TestCaseValue.testcase_id == tc.id)
        .order_by(models.TestCaseValue.id)
        .all()
    )
    assignments = {}
    for v in vals:
        cat_name = name_by_id.get(v.category_id)
        if cat_name is None and v.category_name:
            cat_name = v.category_name  # B-18
        elif cat_name is None:
            cat_name = f"cat#{v.category_id}"
        assignments[cat_name] = v.value
    ...
```

---

## 11. XLSX-Export (src/app/routers/api_generate.py – export_generation_xlsx)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 525-612

**Aenderung:** Analog zu JSON-Export – `name_by_id`-Lookup erweitern + `cat_headers` erweitern
(geloeschte Kategorien hinzufuegen).

---

## 12. Risikoabdeckung (src/app/routers/api_generate.py – get_testcases)

**Datei:** `src/app/routers/api_generate.py`, Zeilen 218-225 (value_risk_map)

**Problem:** `value_risk_map` wird nur aus existierenden Werten erstellt.
Wenn eine Kategorie geloescht wurde, sind deren Werte nicht mehr in der Map.

**Aenderung:** Kein Problem – die aktuelle Logik (Zeile 253) faellt auf `0` zurueck:
```python
risk_coverage = sum(value_risk_map.get(val, 0) if val else 0 for val in assignments.values())
```
Wenn `category_name` eine geloeschte Kategorie ist, deren Wert nicht in `value_risk_map` steht,
wird `0` verwendet. Das ist korrekt: wir koennen das Risiko nicht mehr nachschlagen.

**Optional:** Ein Warn-Flag im Response koennte hinzugefuegt werden, wenn eine geloeschte
Kategorie in einer alten Generierung vorkommt. Dies ist jedoch kein Muss fuer B-18.

---

## 13. Tests (tests/test_bugfix_history_immutable.py – NEU)

Siehe die im Briefing spezifizierten 5 Tests:
1. `test_deleting_category_keeps_old_generation_columns`
2. `test_renaming_category_keeps_old_name_in_old_generation`
3. `test_new_generation_uses_new_name`
4. `test_export_csv_of_old_generation_after_category_delete`
5. `test_risk_summary_old_generation_after_category_delete`

**Wichtig:** Die Tests muessen nach der Migration laufen. Stelle sicher, dass
`_migrate_db()` vor den Tests aufgerufen wird (siehe `conftest.py` Muster).

---

## 14. Bestehende Tests anpassen

- `tests/test_api_projects.py` – delete_category-Tests: pruefen ob CASCADE-Loeschung
  von TestCaseValue getestet wird → anpassen
- `tests/test_backend_mvp.py` – Generierungs-Tests: sollten unveraendert funktionieren
- `tests/test_risk_coverage.py` – Risikoabdeckung: sollte unveraendert funktionieren
- `tests/test_req3051_risk_summary_api.py` – sollte unveraendert funktionieren

---

## 15. Nicht aendern

- Wie neue Generierungen erzeugt werden (Strategien, Sortierung)
- RuleEngine
- Frontend-Layout
- Backup-Schema (`BackupProjectSchema.generations` ist `list[dict]`, keine separate TestCaseValue-Schema-Aenderung)
- `force_delete_project()` in `services.py` – loescht explizit TestCaseValue vor Projektloeschung;
  dies bleibt korrekt (Projektloeschung ist ein Voll-Reset)

---

## Implementierungsreihenfolge (TDD)

1. **RED:** Testdatei `tests/test_bugfix_history_immutable.py` erstellen, Tests schreiben
2. **RED:** Tests laufen lassen → alle rot (da category_name noch nicht existiert)
3. **GREEN:**
   - Schritt 1: Datenmodell aendern (category_name + FK)
   - Schritt 2: Migration in `_migrate_db()` ergaenzen
   - Schritt 3: Generierung anpassen (category_name befuellen)
   - Schritt 4: delete_category anpassen (SET NULL)
   - Schritt 5: force_delete_category anpassen (SET NULL)
   - Schritt 6: get_testcases anpassen (category_name Fallback)
   - Schritt 7: assignment_from_testcase() anpassen (OUTER JOIN)
   - Schritt 8: CSV/JSON/XLSX Export anpassen
4. **GREEN:** Alle neuen + bestehenden Tests gruen
5. **REFACTOR:** Code bereinigen, Doku aktualisieren

---

## Risikoanalyse

| Risiko | Wahrscheinlichkeit | Auswirkung | Massnahme |
|---|---|---|---|
| Migration lauft nicht auf PostgreSQL | Mittel | Hoch | `batch_alter_table` in Alembic verwenden; PostgreSQL-Test |
| Bestehende Tests brechen | Hoch | Mittel | Alle Tests nach jeder Aenderung ausfuehren |
| Frontend bricht durch NULL category_id | Niedrig | Mittel | Frontend sollte category_name bevorzugen (kann in Phase 3 angepasst werden) |
| Performance bei grossen Generierungen | Niedrig | Niedrig | category_name ist nur ein String(300), kein signifikanter Overhead |