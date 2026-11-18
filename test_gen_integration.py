"""Test: Generator-Integration mit Constraints (REQ-6001)"""
import sys
sys.path.insert(0, 'src')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Login
r = client.post('/auth/login', json={'username': 'admin', 'password': 'admin'})
print(f'Login: {r.status_code}')

# Projekt ID holen (Beispielprojekt)
r = client.get('/api/projects')
projects = r.json()
example = [p for p in projects if 'Porto' in p['name']]
if not example:
    print('Kein Beispielprojekt gefunden')
    exit(1)
pid = example[0]['id']
print(f'Projekt ID: {pid}, Name: {example[0]["name"]}')

# Kategorien laden
r = client.get(f'/api/projects/{pid}/categories')
cats = r.json()
print(f'Kategorien: {len(cats)}')
for c in cats[:3]:
    print(f'  - {c["name"]} (id={c["id"]})')

# Werte der ersten Kategorie
if cats:
    cat1 = cats[0]
    r = client.get(f'/api/categories/{cat1["id"]}/values')
    vals = r.json()
    print(f'Werte {cat1["name"]}: {[v["value"] for v in vals[:3]]}')

    # Constraint erstellen: forbid cat1=val1
    payload = {
        'name': 'Test-Constraint',
        'kind': 'forbid',
        'expression': {
            'op': 'eq',
            'category_id': cat1['id'],
            'value_id': vals[0]['id']
        }
    }
    r = client.post(f'/api/v1/projects/{pid}/constraints', json=payload)
    print(f'Constraint erstellen: {r.status_code}')
    if r.status_code == 201:
        cid = r.json()['id']
        print(f'Constraint ID: {cid}')

        # Constraint lesen
        r = client.get(f'/api/v1/projects/{pid}/constraints/{cid}')
        print(f'Constraint lesen: {r.status_code}, Name: {r.json()["name"]}')

        # Generierung testen
        r = client.post(f'/api/projects/{pid}/generate', json={'strategy': 'pairwise', 'limit': 10})
        print(f'Generierung: {r.status_code}')
        if r.status_code == 200:
            gen = r.json()
            print(f'Testfaelle: {gen["count"]}')
            # Pruefen ob verbotenener Wert vorkommt
            forbidden_val = vals[0]['value']
            has_forbidden = any(forbidden_val in str(tc) for tc in gen.get('testcases', []))
            print(f'Verbotener Wert "{forbidden_val}" in Ergebnissen: {has_forbidden}')
            if not has_forbidden:
                print('✅ Constraint wirkt: verbotener Wert wurde gefiltert!')
            else:
                print('❌ Constraint wirkt NICHT: verbotener Wert ist noch da!')
        else:
            print(f'Generierungsfehler: {r.text[:200]}')
    else:
        print(f'Fehler: {r.text[:200]}')
else:
    print('Keine Kategorien gefunden')