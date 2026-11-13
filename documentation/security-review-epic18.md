# Security Review – EPIC-18 (Multi-User)

**Version:** 1.0
**Datum:** 2026-10-05
**Autor:** GREAT Security Architect Agent
**Scope:** Auth-Schema (REQ-4001), OWASP Top 10, Token-Handling, Rollen-Modell (REQ-4020), Risiko-Bewertung
**Status:** 🔴 **BLOCKER** – Sprint 11 Start bedingt (siehe Go/No-Go unten)

---

## 1. Auth-Schema-Review (REQ-4001)

### 1.1 OAuth2 Password Flow vs. andere Flows

| Flow | Geeignet für lokale Nutzer? | Sicherheit | Empfehlung |
|---|---|---|---|
| **Resource Owner Password Credentials (Password Flow)** | ✅ Ja, für lokale Nutzer | ⚠️ Mittel – Credentials direkt an Server | **Empfohlen** für G.R.E.A.T. (lokale Nutzer, kein Third-Party) |
| Authorization Code + PKCE | ❌ Nein – erfordert Redirect-URI, OAuth-Provider | ✅ Hoch | Für SSO-Integration (Out of Scope EPIC-18) |
| Client Credentials | ❌ Nein – für Machine-to-Machine | ✅ Hoch | Nicht relevant für User-Login |
| JWT-Only (keine OAuth2) | ⚠️ Teilweise | ⚠️ Mittel | Zu einfach, kein Refresh-Token-Standard |

**Entscheidung: OAuth2 Password Flow (RFC 6749 §4.3)**

**Begründung:**
- G.R.E.A.T. hat **lokale Nutzer** (kein Enterprise-SSO, kein Third-Party-Provider)
- OAuth2 Password Flow ist der einfachste Flow für lokale Credentials
- RFC 9528 (OAuth 2.1) deprecated Password Flow für Third-Party, aber **nicht** für First-Party-Auth
- Teams bis 10 Personen → kein komplexer Authorization-Server nötig
- FastAPI hat `fastapi-users` oder manuelle Implementierung mit `python-jose`/`PyJWT`

**⚠️ CRITICAL: Password Flow erfordert TLS (HTTPS) in Produktion.**
- Für lokale Nutzung (localhost) ist HTTP akzeptabel
- Für Netzwerk-Zugriff (Team auf Raspberry Pi) **muss** HTTPS aktiv sein
- Empfehlung: `caddy` oder `traefik` als Reverse-Proxy mit automatischem HTTPS

### 1.2 JWT Access-Token + Refresh-Token – Lebensdauern

| Token-Typ | Lebensdauer | Begründung |
|---|---|---|
| **Access Token (JWT)** | **15 Minuten** | Kurz genug um Schaden bei Diebstahl zu begrenzen, lang genug für normale Nutzung |
| **Refresh Token** | **7 Tage** | Lang genug um täglichen Login zu vermeiden, kurz genug um Kompromittierung zu begrenzen |

**Begründung:**
- 15 Min Access: OWASP empfiehlt 5-15 Min für sensitive Apps. G.R.E.A.T. ist Testdaten (nicht kritisch), aber besser sicher.
- 7 Tage Refresh: Teams arbeiten typisch 5-7 Tage pro Woche. Länger als 7 Tage erhöht Risiko bei gestohlenem Refresh-Token.
- **Token Rotation**: Jeder Refresh-Token darf NUR EINMAL verwendet werden. Nach Verwendung wird ein neuer Refresh-Token ausgegeben. Altes Token wird sofort invalidiert.

**Implementierungsempfehlung:**
```python
# config.py
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
SECRET_KEY: str = os.getenv("GREAT_SECRET_KEY")  # Niemals hardcoded!
```

### 1.3 Passwort-Hashing: bcrypt vs. argon2id

| Algorithmus | OWASP-Empfehlung | Python-Support | Raspberry Pi | Empfehlung |
|---|---|---|---|---|
| **argon2id** | ✅ #1 Empfehlung (OWASP 2024) | `argon2-cffi` | ✅ Ja (Pure Python FFI) | **⭐ EMPFOHLEN** |
| bcrypt | ⚠️ Akzeptabel, aber älter | `passlib[bcrypt]` | ✅ Ja | Alternative |
| PBKDF2 | ⚠️ Akzeptabel | `passlib` | ✅ Ja | Nur Fallback |
| scrypt | ⚠️ Gut, aber weniger verbreitet | `passlib` | ⚠️ Langsam auf ARM | Nicht empfohlen |

**Entscheidung: argon2id**

**Begründung:**
- OWASP Password Storage Cheat Sheet (2024): argon2id ist die #1-Empfehlung
- argon2id ist resistent gegen GPU- und ASIC-Angriffe (memory-hard)
- `argon2-cffi` ist ein reines Python-Paket mit C-FFI-Binding – funktioniert auf Raspberry Pi
- bcrypt hat eine feste Work-Factor und ist nicht memory-hard
- `passlib` unterstützt beide, aber argon2id ist zukunftssicherer

**⚠️ NEUE DEPENDENCY: `argon2-cffi>=23.1.0` (MIT-Lizenz, kompatibel)**

### 1.4 Token-Speicherung im Frontend

| Methode | XSS-Schutz | CSRF-Schutz | Auto-Refresh | Empfehlung |
|---|---|---|---|---|
| **httpOnly-Cookie** | ✅ Token nicht via JS erreichbar | ⚠️ CSRF-Risiko (mit SameSite=Strict reduziert) | ✅ Automatisch mit jedem Request | **⭐ EMPFOHLEN** |
| localStorage | ❌ Vollständig XSS-angreifbar | ✅ Kein CSRF (manuell im Header) | ⚠️ Manuell via Interceptor | **NICHT EMPFOHLEN** |
| memory (JS-Variable) | ✅ Token nicht persistent | ✅ Kein CSRF | ❌ Bei Reload verloren | Alternative |

**Entscheidung: httpOnly-Cookie für Access-Token + Refresh-Token**

**Begründung:**
- **Access-Token**: httpOnly-Cookie – automatisch mit jedem API-Request gesendet, nicht via JS lesbar (XSS-Schutz)
- **Refresh-Token**: httpOnly-Cookie mit `Path=/auth/refresh` – nur am Refresh-Endpoint verwendbar
- **SameSite=Strict**: Verhindert CSRF von externen Sites
- **Secure-Flag**: Nur über HTTPS setzen (in Dev: optional)

**⚠️ CSRF-Schutz bei httpOnly-Cookies:**
- SameSite=Strict blockiert Cross-Site-Requests von externen Origins
- Für zusätzlichen Schutz: Custom Header `X-Requested-With: XMLHttpRequest` prüfen (nicht von Forms sendbar)
- **Kein separates CSRF-Token nötig** wenn SameSite=Strict + Custom-Header-Kombination verwendet wird

### 1.5 Token-Invalidation bei Logout

| Methode | Aufwand | Sicherheit | Empfehlung |
|---|---|---|---|
| **Serverseitige Blacklist (DB)** | ⚠️ Mittel – DB-Query pro Request | ✅ Hoch – sofortige Invalidierung | **⭐ EMPFOHLEN** |
| Nur kurze Access-Token-Lebensdauer | ✅ Gering | ⚠️ Mittel – Refresh-Token bleibt gültig | Nicht ausreichend |
| Redis-Blacklist | ⚠️ Hoch – zusätzliche Infrastruktur | ✅ Hoch | Overkill für 10 User |

**Entscheidung: DB-basierte Refresh-Token-Blacklist**

**Begründung:**
- SQLite/PostgreSQL – keine zusätzliche Infrastruktur nötig
- Tabelle `refresh_tokens` mit Spalten: `token_hash`, `user_id`, `expires_at`, `revoked`
- Logout setzt `revoked=True` für alle Refresh-Tokens des Users
- Jeder Refresh-Request prüft: Token nicht revoked + nicht expired
- **Access-Token**: Kein Blacklist nötig – läuft nach 15 Min selbst ab

**DB-Modell:**
```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    token_hash = Column(String(255), unique=True, nullable=False)  # SHA256 des Tokens
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
```

### 1.6 Password-Reset-Flow

| Methode | Verfügbarkeit | Sicherheit | Empfehlung |
|---|---|---|---|
| **Email-basiert** | ✅ Standard | ✅ Hoch – temporärer Token per Email | **⭐ EMPFOHLEN** (wenn Email verfügbar) |
| **Admin-Reset** | ✅ Immer verfügbar | ⚠️ Mittel – Admin braucht Zugriff | Fallback |
| **Recovery-Question** | ✅ Immer | ❌ Gering – Questions sind schwach | **NICHT EMPFOHLEN** |
| **Kein Reset (nur Admin)** | ⚠️ Admin nötig | ✅ Hoch – kein Reset-Token | **EMPFOHLEN als Default** |

**Entscheidung: Admin-Reset als Default, Email-Reset als Option**

**Begründung:**
- G.R.E.A.T. ist eine lokale Team-App – kein Email-Server garantiert verfügbar
- **Default**: Nur Admin kann Passwörter zurücksetzen (`POST /auth/users/{id}/reset-password`)
- **Optional**: Email-Reset konfigurierbar via `GREAT_SMTP_*` Umgebungsvariablen
- Recovery-Questions sind kryptographisch schwach und werden von OWASP explizit abgeraten
- Für lokale Nutzung: Admin-Reset ist der pragmatischste und sicherste Weg

**⚠️ CRITICAL: Password-Reset-Token (wenn Email-Reset aktiv) müssen:**
- Einmalig verwendbar sein
- Maximal 15 Minuten gültig sein
- Kryptographisch zufällig (mindestens 32 Byte random, hex-encoded)

---

## 2. OWASP Top 10 Abdeckung

### A01: Broken Access Control

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **Rollenprüfung auf allen Endpunkten** | ❌ Nicht implementiert | `get_current_user` + `require_role` Dependency für alle schreibenden Endpunkte | 🔴 CRITICAL |
| **Projekt-Sharing (REQ-4023)** | ❌ Nicht implementiert | User darf nur eigene/zugeteilte Projekte sehen | 🔴 CRITICAL |
| **403 vs. 404 bei fehlendem Zugriff** | ❌ Nicht implementiert | Immer 403 (niemals 404) bei AuthZ-Fehler – vermeidet Information Disclosure | 🔴 CRITICAL |
| **Erster User = Admin** | ❌ Nicht implementiert | Atomare Race-Condition-Prävention (DB-Constraint + Transaction) | 🟡 MEDIUM |

**Empfohlene Implementierung:**
```python
# src/app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validiert JWT und gibt User-Objekt zurück. 401 bei ungültigem Token."""
    # JWT decode + verify signature + check expiry
    # User aus DB laden
    # Return User

async def require_role(required_role: str):
    """Dependency-Factory: Prüft Rolle des aktuellen Users."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {"admin": 3, "editor": 2, "viewer": 1}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                              detail="Unzureichende Berechtigungen")
        return current_user
    return role_checker
```

### A02: Cryptographic Failures

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **Passwort-Hashing** | ❌ Nicht implementiert | argon2id (siehe 1.3) | 🔴 CRITICAL |
| **JWT-Signatur** | ❌ Nicht implementiert | HMAC-SHA256 oder RS256, Secret aus Environment | 🔴 CRITICAL |
| **TLS/HTTPS** | ⚠️ Nicht konfiguriert | Reverse-Proxy mit HTTPS für Netzwerk-Zugriff | 🟡 MEDIUM |
| **Sensitive Daten in DB** | ⚠️ Teilweise | Keine Klartext-Passwörter, Tokens gehasht | 🔴 CRITICAL |
| **SECRET_KEY Management** | ❌ Nicht implementiert | `GREAT_SECRET_KEY` als Umgebungsvariable, niemals im Code | 🔴 CRITICAL |

### A03: Injection

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **SQL-Injection** | ✅ Geschützt | SQLAlchemy ORM verwendet parametrisierte Queries | 🟢 NIEDRIG |
| **XSS (React)** | ✅ Geschützt | React escaped automatisch, keine `dangerouslySetInnerHTML` | 🟢 NIEDRIG |
| **Command Injection** | ⚠️ Prüfen | `subprocess`-Aufrufe in `services.py` prüfen | 🟡 MEDIUM |
| **Path Traversal (Backup)** | ⚠️ Prüfen | `api_backup.py` – Dateipfade validieren | 🟡 MEDIUM |
| **LDAP Injection** | ✅ N/A | Kein LDAP in Scope | 🟢 NIEDRIG |

**⚠️ Legacy-Code `src/main.py` (PySide6-App):**
- Diese Datei ist **nicht** Teil der FastAPI-App und wird nicht über HTTP aufgerufen
- Kein SQL-Injection-Risiko (nutzt eigene DB-Logik)
- Empfehlung: Bei EPIC-18-Implementierung sicherstellen, dass `src/main.py` nicht versehentlich als HTTP-Server gestartet wird

### A05: Security Misconfiguration

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **CORS** | ❌ **OFFEN** | Whitelist-Konfiguration (`GREAT_CORS_ORIGINS`) | 🔴 CRITICAL |
| **CSP-Headers** | ❌ Nicht gesetzt | `Content-Security-Policy` für React-Frontend | 🟡 MEDIUM |
| **Debug-Modus** | ⚠️ `reload=True` in Dev | `reload=False` in Production (bereits via `sys.frozen` geprüft) | 🟢 NIEDRIG |
| **GREAT_HOST=0.0.0.0** | ⚠️ Binds an alle Interfaces | Dokumentation: Netzwerk-Zugriff erfordert HTTPS | 🟡 MEDIUM |
| **X-Frame-Options** | ❌ Nicht gesetzt | `DENY` oder `SAMEORIGIN` Header | 🟡 MEDIUM |
| **X-Content-Type-Options** | ❌ Nicht gesetzt | `nosniff` Header | 🟡 MEDIUM |
| **Referrer-Policy** | ❌ Nicht gesetzt | `strict-origin-when-cross-origin` | 🟢 NIEDRIG |

**⚠️ CRITICAL: CORS-Konfiguration ist aktuell nicht vorhanden!**
- `main.py` hat keine CORS-Middleware → FastAPI Default: alle Origins erlaubt
- **Sofortmaßnahme**: CORS-Middleware mit Whitelist in `main.py` hinzufügen
- `GREAT_CORS_ORIGINS` als Umgebungsvariable (Default: `http://localhost:5173` für Vite-Dev)

### A07: Identification and Authentication Failures

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **Brute-Force-Schutz** | ❌ Nicht implementiert | Rate-Limiting: max 5 Versuche/Minute pro IP/User | 🔴 CRITICAL |
| **Account-Lockout** | ❌ Nicht implementiert | Nach 10 fehlgeschlagenen Versuchen: 30-minütiger Lockout | 🟡 MEDIUM |
| **Password-Policy** | ❌ Nicht definiert | Min. 8 Zeichen, mind. 1 Zahl, 1 Sonderzeichen | 🟡 MEDIUM |
| **Session-Fixation** | ⚠️ Risiko | Neuer Token-Pair nach jedem Login | 🔴 CRITICAL |
| **Credential-Storage** | ❌ Nicht implementiert | argon2id-Hash, Salt automatisch | 🔴 CRITICAL |

**Rate-Limiting-Implementierung:**
```python
# src/app/middleware/rate_limit.py
from fastapi import Request, HTTPException, status
from collections import defaultdict
import time

# In-Memory Store (für SQLite-Betrieb ausreichend, <=10 User)
# Für PostgreSQL: Redis- oder DB-basiertes Rate-Limiting
rate_limit_store: dict[str, list[float]] = defaultdict(list)

async def login_rate_limiter(request: Request):
    """Max 5 Login-Versuche pro Minute pro IP-Adresse."""
    client_ip = request.client.host
    now = time.time()
    window = 60  # Sekunden
    
    # Alte Einträge aufräumen
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < window
    ]
    
    if len(rate_limit_store[client_ip]) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Zu viele Login-Versuche. Versuchen Sie es in einer Minute erneut."
        )
    
    rate_limit_store[client_ip].append(now)
```

### A09: Security Logging and Monitoring

| Aspekt | Status | Maßnahme | Priorität |
|---|---|---|---|
| **Audit-Trail (REQ-4024)** | ❌ Nicht implementiert | `last_modified_by` + `last_modified_at` auf allen Entitäten | 🟡 MEDIUM |
| **Login-Events loggen** | ❌ Nicht implementiert | Erfolgs/Fehlschlag-Log mit IP, User, Timestamp | 🔴 CRITICAL |
| **Failed-Auth-Log** | ❌ Nicht implementiert | Strukturierter Log für Security-Monitoring | 🔴 CRITICAL |
| **Request-Logging** | ✅ Teilweise | `log_requests` Middleware in `main.py` (REQ-4009) | 🟢 NIEDRIG |

**Empfohlene Audit-Log-Struktur:**
```python
# In log_requests Middleware ergänzen:
log.info(
    "auth_event",
    event_type="login_success" | "login_failure" | "logout" | "token_refresh",
    user_id=current_user.id if current_user else None,
    username=username_attempted,
    ip=request.client.host,
    user_agent=request.headers.get("user-agent"),
)
```

---

## 3. Token-Handling (Frontend + Backend)

### 3.1 Backend (FastAPI)

#### JWT-Decoder mit Signature-Verification

```python
# src/app/auth/jwt_handler.py
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from ..config import SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS

ALGORITHM = "HS256"  # HMAC-SHA256 für <=10 User ausreichend

def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Returns (raw_token, hashed_token_for_db)"""
    import hashlib, secrets
    raw_token = secrets.token_urlsafe(64)  # Kryptographisch sicherer Random-Token
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Speichere token_hash in DB (RefreshToken-Modell)
    # ...
    
    return raw_token, token_hash

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Token")
```

#### Dependency `get_current_user`

```python
# src/app/auth/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

# Für httpOnly-Cookie: Token aus Cookie lesen
def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Nicht authentifiziert")
    return token

async def get_current_user(
    token: str = Depends(get_token_from_cookie),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Ungültiges oder abgelaufenes Token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_active == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Nutzer nicht gefunden oder inaktiv")
    return user
```

#### Refresh-Token-Endpoint mit Rotation

```python
@app.post("/auth/refresh")
async def refresh_tokens(
    request: Request,
    db: Session = Depends(get_db)
):
    refresh_token_raw = request.cookies.get("refresh_token")
    if not refresh_token_raw:
        raise HTTPException(status_code=401, detail="Kein Refresh-Token")
    
    token_hash = hashlib.sha256(refresh_token_raw.encode()).hexdigest()
    
    # Prüfe: Token existiert, nicht revoked, nicht expired
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False
    ).first()
    
    if not stored:
        raise HTTPException(status_code=401, detail="Ungültiger Refresh-Token")
    
    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh-Token abgelaufen")
    
    # ⚠️ TOKEN ROTATION: Alten Token sofort revoke
    stored.revoked = True
    
    # Neue Token-Paar erstellen
    user = stored.user
    new_access = create_access_token(user.id, user.username, user.role)
    new_refresh_raw, new_refresh_hash = create_refresh_token(user.id)
    
    # Neuen Refresh-Token in DB speichern
    new_rt = RefreshToken(token_hash=new_refresh_hash, user_id=user.id, ...)
    db.add(new_rt)
    db.commit()
    
    # Neue Cookies setzen (httpOnly, Secure, SameSite=Strict)
    response = JSONResponse(content={"message": "Tokens refreshed"})
    response.set_cookie(key="access_token", value=new_access, httponly=True, 
                       secure=True, samesite="strict", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=new_refresh_raw, httponly=True,
                       secure=True, samesite="strict", max_age=7*86400, path="/auth/refresh")
    return response
```

#### Brute-Force-Schutz am Login-Endpoint

- Siehe A07 oben: Rate-Limiting-Middleware mit max 5 Versuchen/Minute pro IP
- Zusätzlich: Account-Lockout nach 10 Fehlversuchen (30 Minuten)

### 3.2 Frontend (React)

#### Token-Speicherung: httpOnly-Cookie

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,  // ⚠️ WICHTIG: Cookies mit jedem Request senden
});

// Automatic 401-Handling: Versuche Refresh, dann Retry
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Refresh-Token ist httpOnly – Browser sendet automatisch
        const { data } = await axios.post('/auth/refresh', {}, { withCredentials: true });
        
        // Access-Token wurde als neuer Cookie gesetzt – Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh fehlgeschlagen – zum Login weiterleiten
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

#### Logout: Token löschen + Server-Invalidierung

```typescript
// frontend/src/api/authApi.ts
import axios from 'axios';

export async function logout() {
  // 1. Server: Refresh-Token invalidieren
  await axios.post('/auth/logout', {}, { withCredentials: true });
  
  // 2. Frontend: Cookies löschen (Browser erledigt via Set-Cookie mit max-age=0)
  //    Die Server-Antwort setzt max-age=0 für beide Cookies
  
  // 3. Redirect zum Login
  window.location.href = '/login';
}
```

#### Protected Routes

```typescript
// frontend/src/components/ProtectedRoute.tsx
import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../api/client';

export function ProtectedRoute({ children, requiredRole }: { children: React.ReactNode; requiredRole?: string }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  
  useEffect(() => {
    // Prüfe Auth-Status via /auth/me
    api.get('/auth/me')
      .then(res => {
        if (requiredRole && res.data.role !== requiredRole) {
          // 403 – nicht unauthenticated
          setIsAuthenticated(false);
        } else {
          setIsAuthenticated(true);
        }
      })
      .catch(() => setIsAuthenticated(false));
  }, [requiredRole]);
  
  if (isAuthenticated === null) return <div>Lade...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  return <>{children}</>;
}
```

---

## 4. Rollen-Modell (REQ-4020)

### 4.1 Drei Rollen: Admin/Editor/Viewer

| Rolle | Berechtigungen | Beschreibung |
|---|---|---|
| **Admin** | Vollzugriff + Nutzerverwaltung | Kann Nutzer erstellen/löschen, Rollen ändern, alle Projekte bearbeiten |
| **Editor** | Projekte erstellen/bearbeiten/löschen | Kann Kategorien, Werte, Regeln, Generierungen verwalten |
| **Viewer** | Nur lesen | Kann Projekte, Kategorien, Testfälle ansehen, aber nichts ändern |

**Sind 3 Rollen ausreichend? JA.**

**Begründung:**
- Teams bis 10 Personen – keine komplexe Berechtigungsstruktur nötig
- Admin: Team-Lead / Admin
- Editor: Tester:innen die aktiv arbeiten
- Viewer: Stakeholder / Management / neue Teammitglieder (Lernphase)
- Mehr Rollen würden die UX unnötig komplex machen
- Bei Bedarf später erweiterbar (z.B. "Project-Owner" als vierte Rolle)

### 4.2 Serverseitige Rollenprüfung

**JEDER schreibende Endpunkt muss eine Rollenprüfung haben:**

| Endpunkt | Methode | Benötigte Rolle |
|---|---|---|
| `/api/projects` | POST, PUT, DELETE | Editor+ |
| `/api/projects/{id}/categories` | POST, PUT, DELETE | Editor+ |
| `/api/projects/{id}/values` | POST, PUT, DELETE | Editor+ |
| `/api/projects/{id}/rules` | POST, PUT, DELETE | Editor+ |
| `/api/projects/{id}/generations` | POST, PUT, DELETE | Editor+ |
| `/api/projects/{id}/testcases` | POST, PUT, DELETE | Editor+ |
| `/api/dataclasses` | POST, PUT, DELETE | Editor+ |
| `/auth/users` | POST, PUT, DELETE | Admin |
| `/auth/users/{id}/role` | PUT | Admin |
| Alle GET-Endpunkte | GET | Viewer+ (alle authentifizierten User) |

**⚠️ CRITICAL: Keine Endpunkte dürfen ohne Auth erreichbar sein (außer `/auth/login`, `/health`, `/docs`)**

### 4.3 403 vs. 404 bei fehlendem Zugriff

| Szenario | HTTP-Code | Begründung |
|---|---|---|
| User nicht authentifiziert | **401 Unauthorized** | Kein Token / ungültiger Token |
| User hat keine Rolle für Aktion | **403 Forbidden** | Authentifiziert, aber keine Berechtigung |
| User hat keinen Zugriff auf Projekt (REQ-4023) | **403 Forbidden** | **NIEMALS 404** – würde Existenz des Projekts verneinen |

**⚠️ Information Disclosure:**
- 404 bei nicht-existentem Projekt ist korrekt (Projekt existiert wirklich nicht)
- 403 bei vorhandenem Projekt ohne Zugriff (vermeidet, dass Angreifer Projekt-Existenz durch 404-Responses ausschließen können)

### 4.4 Erste registrierte Person = Admin

**Race-Condition-Risiko bei gleichzeitiger Registrierung:**

| Problem | Lösung |
|---|---|
| Zwei User registrieren sich gleichzeitig → beide werden Admin | **DB-Transaktion mit SELECT ... FOR UPDATE** (SQLite: Serialisierung via WAL) |
| Kein User existiert → wer wird Admin? | **Atomare Check-and-Insert**: `INSERT ... WHERE NOT EXISTS (SELECT 1 FROM users)` |

**Empfohlene Implementierung:**
```python
@app.post("/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Prüfe: Existiert bereits ein Admin?
    existing_admin = db.query(User).filter(User.role == "admin").first()
    
    if existing_admin:
        # Neuer User wird Editor (Standard)
        role = "editor"
    else:
        # Erster User wird Admin
        # ⚠️ Race-Condition-Schutz: Transaktion + Unique-Constraint
        role = "admin"
    
    # Prüfe: Username bereits existiert?
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=409, detail="Username bereits vergeben")
    
    # Hash Passwort mit argon2id
    hashed_password = argon2.hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    
    # Login und Token zurückgeben
    access_token = create_access_token(new_user.id, new_user.username, role)
    refresh_raw, refresh_hash = create_refresh_token(new_user.id)
    # ...
```

**Zusätzlicher Schutz: Datenbank-Constraint**
```python
# Sicherstellen: Es gibt maximal einen Admin
# Option 1: Application-Level-Check (oben)
# Option 2: DB-Constraint (PostgreSQL: EXCLUDE, SQLite: Trigger)
# Für SQLite: Trigger im Migration-Skript
```

---

## 5. Risiko-Bewertung

| ID | Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|---|
| **RISK-S-001** | Keine Authentifizierung – alle Endpunkte öffentlich | 5 | 4 | **20** | 🔴 | REQ-4001 vor Sprint 11 zwingend abschließen (Blocker) |
| **RISK-S-006** | JWT-Geheimnis unsicher gespeichert | 3 | 5 | **15** | 🔴 | `GREAT_SECRET_KEY` als Umgebungsvariable, min. 32 Byte random, in `.env.example` als Platzhalter |
| **RISK-S-007** | Brute-Force-Angriffe auf Login | 3 | 4 | **12** | 🔴 | Rate-Limiting (5/Min) + Account-Lockout (10 Versuche → 30 Min) |
| **RISK-S-008** | XSS durch Token in localStorage | 2 | 5 | **10** | 🔴 | httpOnly-Cookies verwenden (kein localStorage für Tokens) |
| **RISK-S-009** | CSRF bei Cookie-basierten Tokens | 3 | 3 | **9** | 🟡 | SameSite=Strict + Custom-Header-Prüfung |
| **RISK-S-010** | CORS zu offen (alle Origins) | 3 | 3 | **9** | 🟡 | Whitelist via `GREAT_CORS_ORIGINS` (Default: localhost:5173) |
| **RISK-S-011** | Password-Reset ohne Email | 2 | 3 | **6** | 🟡 | Admin-Reset als Default, Email-Reset optional |
| **RISK-S-012** | Race-Condition bei erstem Admin | 2 | 4 | **8** | 🟡 | Atomare DB-Transaktion + Constraint |
| **RISK-S-013** | Refresh-Token-Diebstahl | 2 | 5 | **10** | 🔴 | Token Rotation + kurze Refresh-Validierung + Path-Restriktion |
| **RISK-S-014** | SQLite-WAL-Locks bei Multi-User | 2 | 4 | **8** | 🟡 | PostgreSQL-Option (REQ-4006), WAL-Mode aktiv |
| **RISK-S-015** | Keine Security-Headers (CSP, X-Frame) | 2 | 3 | **6** | 🟡 | Middleware für Security-Headers hinzufügen |

### Risikozusammenfassung

| Kategorie | Anzahl | Score-Summe | Ampel |
|---|---|---|---|
| 🔴 CRITICAL (Score ≥ 10) | 5 | 67 | 🔴 |
| 🟡 MEDIUM (Score 5-9) | 5 | 37 | 🟡 |
| 🟢 LOW (Score 1-4) | 0 | 0 | 🟢 |
| **GESAMT** | **10** | **104** | **🔴** |

---

## 6. Empfehlungen + ADR-Vorschlag

### 6.1 Zusammenfassung der Empfehlungen

| Entscheidung | Empfehlung | Begründung |
|---|---|---|
| **Auth-Flow** | OAuth2 Password Flow (RFC 6749 §4.3) | Lokale Nutzer, kein Third-Party, einfach zu implementieren |
| **Passwort-Hashing** | argon2id via `argon2-cffi` | OWASP #1-Empfehlung, memory-hard, Raspberry-Pi-kompatibel |
| **Token-Speicherung** | httpOnly-Cookie (Access + Refresh) | XSS-Schutz, automatischer Refresh, SameSite=Strict |
| **Access-Token-Lebensdauer** | 15 Minuten | OWASP-Empfehlung, kurz genug für Schadenbegrenzung |
| **Refresh-Token-Lebensdauer** | 7 Tage | Täglicher Login unnötig, Rotation schützt vor Diebstahl |
| **JWT-Algorithmus** | HS256 (HMAC-SHA256) | Einfach, ausreichend für <=10 User, keine PKI nötig |
| **SECRET_KEY** | Umgebungsvariable `GREAT_SECRET_KEY` (min. 32 Byte) | Niemals im Code, `.env`-Datei nicht in Git |
| **Rollen** | Admin / Editor / Viewer (3 Rollen) | Ausreichend für Teams bis 10, später erweiterbar |
| **Password-Reset** | Admin-Reset (Default), Email-Reset (Optional) | Kein Email-Server garantiert, Admin-Reset ist pragmatisch |
| **CORS** | Whitelist via `GREAT_CORS_ORIGINS` | Default: `http://localhost:5173` (Vite Dev) |
| **Security-Headers** | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy | Middleware in FastAPI |
| **Rate-Limiting** | 5 Login-Versuche/Minute pro IP | In-Memory-Store für SQLite, Redis/DB für PostgreSQL |

### 6.2 Empfohlene Security-Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"  # Modern browsers ignore this, but set for legacy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind JIT
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response
```

### 6.3 Neue Dependencies

| Paket | Version | Lizenz | Zweck |
|---|---|---|---|
| `argon2-cffi` | >=23.1.0 | MIT | Passwort-Hashing |
| `python-jose[cryptography]` | >=1.0.0 | MIT | JWT-Encoding/Decoding |
| `passlib` | >=1.7.4 | BSD | Alternative Hashing (Fallback) |
| `slowapi` | >=0.1.0 | MIT | Rate-Limiting (optional, statt Custom) |

**Alle Lizenzen sind MIT/BSD – kompatibel mit G.R.E.A.T. MIT-Lizenz (ADR-006).**

### 6.4 ADR-015 Vorschlag

```markdown
## ADR-015 – Auth-Schema für EPIC-18 (Multi-User)

**Datum:** 2026-10-05
**Status:** Proposed
**Kontext:** EPIC-18 (Multi-User, Sprint 11-13) erfordert Authentifizierung und Autorisierung.
           RISK-S-001 (Score 20) ist eskalationspflichtig und blockiert alle EPIC-18-Features.
           Teams bis 10 Personen, lokale Nutzer (kein SSO).

**Entscheidung:**
- OAuth2 Password Flow für lokale Nutzer-Authentifizierung
- argon2id für Passwort-Hashing (OWASP #1-Empfehlung)
- JWT Access-Token (15 Min) + Refresh-Token (7 Tage) in httpOnly-Cookies
- Token Rotation bei jedem Refresh
- DB-basierte Refresh-Token-Blacklist für Logout
- Drei Rollen: Admin / Editor / Viewer
- Rate-Limiting: 5 Login-Versuche/Minute pro IP
- CORS-Whitelist via GREAT_CORS_ORIGINS
- Security-Headers via Middleware (CSP, X-Frame-Options, etc.)
- Admin-Reset als Default, Email-Reset optional

**Alternativen (abgelehnt):**
- bcrypt: Älter, nicht memory-hard, argon2id ist OWASP-Standard
- localStorage für Tokens: XSS-angreifbar, httpOnly-Cookies sind sicherer
- Redis-Blacklist: Overkill für <=10 User, SQLite reicht
- Enterprise-SSO: Out of Scope für EPIC-18
- Recovery-Questions: Kryptographisch schwach, von OWASP abgeraten

**Konsequenzen:**
- Neue Dependencies: argon2-cffi, python-jose, slowapi (optional)
- Neue DB-Tabellen: users, refresh_tokens
- Neue Endpunkte: /auth/login, /auth/logout, /auth/refresh, /auth/register, /auth/me
- Alle bestehenden API-Endpunkte benötigen Auth-Dependency
- CORS-Middleware in main.py erforderlich
- Security-Headers-Middleware in main.py erforderlich
- .env-Datei mit GREAT_SECRET_KEY (nicht in Git)
- ADR-012 (HYBRID) bleibt gültig – Auth ist Voraussetzung

**Entscheider:** Security Architect Agent (Proposal), Georg Hartel (Genehmigung)
**Abhängigkeiten:** REQ-4001, REQ-4020, RISK-S-001, ADR-012
```

---

## 7. Go/No-Go Empfehlung für Sprint 11 Start

### 🔴 **NO-GO** – Sprint 11 Start ist **NICHT** freigegeben

**Blocker:**
1. **RISK-S-001 (Score 20)**: Keine Authentifizierung existiert. Alle API-Endpunkte sind öffentlich.
   - **Blockiert:** REQ-4006, REQ-4020, REQ-4021, REQ-4022, REQ-4023, REQ-4024
   - **Maßnahme:** REQ-4001 muss VOR jedem anderen EPIC-18-Feature implementiert und getestet sein

2. **CORS-Konfiguration fehlt**: FastAPI hat keine CORS-Middleware → alle Origins erlaubt
   - **Maßnahme:** CORS-Whitelist in `main.py` implementieren (kann parallel zu REQ-4001)

3. **Keine Security-Headers**: CSP, X-Frame-Options etc. fehlen
   - **Maßnahme:** Security-Headers-Middleware in `main.py` implementieren

### ✅ **Konditionales GO** – unter folgenden Bedingungen:

Sprint 11 kann starten WENN:

1. **REQ-4001 ist als erstes Feature in Sprint 11 implementiert** (keine anderen EPIC-18-Features parallel)
2. **TDD-Pflicht eingehalten**: Tests für Token-Erzeugung/-Validierung vor Implementierung
3. **ADR-015 ist vom Projektinhaber genehmigt**
4. **CORS-Whitelist und Security-Headers sind als Pre-Task implementiert**
5. **Neue Dependencies sind lizenzmäßig geprüft** (alle MIT/BSD – ✅)

### Empfohlene Sprint-11-Reihenfolge:

| Sprint-Tag | Aufgabe | Priorität |
|---|---|---|
| Tag 1-2 | CORS-Whitelist + Security-Headers (Pre-Task) | 🔴 |
| Tag 2-4 | REQ-4001: User-Modell + argon2id-Hashing + JWT-Handler | 🔴 |
| Tag 4-6 | REQ-4001: Login-Endpoint + Token-Generation + Cookie-Setting | 🔴 |
| Tag 6-7 | REQ-4001: Refresh-Token + Rotation + Logout + Blacklist | 🔴 |
| Tag 7-8 | REQ-4001: Rate-Limiting + Account-Lockout | 🔴 |
| Tag 8-9 | REQ-4020: Rollen-Modell + `require_role` Dependency | 🔴 |
| Tag 9-10 | Alle bestehenden Endpunkte mit Auth absichern | 🔴 |
| Tag 10 | Regression-Tests + Security-Review | 🔴 |

---

## 8. Anhang: OWASP Top 10 Abdeckungs-Matrix

| OWASP 2021/2024 | G.R.E.A.T. Status | EPIC-18 Maßnahme | Risiko-Score |
|---|---|---|---|
| **A01: Broken Access Control** | ❌ Nicht implementiert | Rollen-Modell + Auth auf allen Endpunkten | 🔴 15 |
| **A02: Cryptographic Failures** | ❌ Nicht implementiert | argon2id + JWT + SECRET_KEY Management | 🔴 15 |
| **A03: Injection** | ✅ Geschützt (ORM) | Bestehende ORM-Nutzung beibehalten | 🟢 2 |
| **A04: Insecure Design** | ⚠️ Teilweise | Auth-Design in ADR-015 dokumentiert | 🟡 8 |
| **A05: Security Misconfiguration** | ❌ Offen (CORS) | CORS-Whitelist + Security-Headers | 🔴 12 |
| **A06: Vulnerable Components** | ⚠️ Prüfen | Dependencies auf CVEs prüfen | 🟡 6 |
| **A07: Auth Failures** | ❌ Nicht implementiert | Rate-Limiting + Password-Policy + Token Rotation | 🔴 12 |
| **A08: Data Integrity** | ⚠️ Teilweise | argon2id-Hash + Token-Signature | 🟡 6 |
| **A09: Logging Failures** | ⚠️ Teilweise (REQ-4009) | Audit-Trail (REQ-4024) + Auth-Event-Logging | 🟡 8 |
| **A10: SSRF** | ✅ N/A (kein External-Fetch) | Kein SSRF-Risiko identifiziert | 🟢 0 |

**Gesamtrisiko-EPIC-18-Security: 🔴 HIGH (Score-Summe: 84)**

---

*Dieser Security-Review ist eine Analyse und enthält keine Produktivcode-Änderungen.
Alle Empfehlungen sind als ADR-015-Vorschlag für die Genehmigung durch den Projektinhaber vorgesehen.*