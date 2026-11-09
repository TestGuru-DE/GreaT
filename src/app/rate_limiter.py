"""Rate Limiter fuer Login-Endpoint.

REQ-EPIC18-PRE: RISK-S-007 (Brute-Force-Schutz)
Max attempts pro IP pro time_window Sekunden.
In-Memory Implementation (fuer MVP; in Production: Redis-basiert).
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple


class RateLimiter:
    """In-Memory Rate Limiter.
    
    Args:
        max_attempts: Maximale Anzahl Versuche im Zeitfenster
        time_window: Zeitfenster in Sekunden
    """
    
    def __init__(self, max_attempts: int = 5, time_window: int = 60):
        self.max_attempts = max_attempts
        self.time_window = time_window
        self._requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """Prueft ob key (z.B. IP-Adresse) rate-limited ist.
        
        Args:
            key: Identifier (z.B. Client-IP)
            
        Returns:
            (is_limited, retry_after_seconds)
            - is_limited: True wenn Rate-Limit erreicht
            - retry_after_seconds: Sekunden bis naechster Versuch moeglich (0 wenn nicht limited)
        """
        now = time.time()
        
        # Alte Eintraege auerraumen (außerhalb des Zeitfensters)
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self.time_window
        ]
        
        if len(self._requests[key]) >= self.max_attempts:
            # Retry-After: Sekunden bis altester Eintrag im Fenster ablaeuft
            oldest = self._requests[key][0]
            retry_after = int(self.time_window - (now - oldest)) + 1
            return True, max(1, retry_after)
        
        # Neuen Request aufzeichnen
        self._requests[key].append(now)
        return False, 0


# Globale Instanz fuer Login-Endpoint (fuer MVP)
# In Production: Redis-basiert mit shared state zwischen Worker-Instances
login_rate_limiter = RateLimiter(max_attempts=5, time_window=60)

# REQ-4027 AK-11: Statusendpunkt GET /auth/first-start-hint, 10 Anfragen/Minute/IP
first_start_hint_rate_limiter = RateLimiter(max_attempts=10, time_window=60)
# REQ-4028 AK-8: Fehlversuche Selbst-Passwortwechsel, 10 Versuche/Minute/Konto
password_change_rate_limiter = RateLimiter(max_attempts=10, time_window=60)