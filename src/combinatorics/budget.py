"""BUG B-03 / K-03: Kooperatives Zeitbudget fuer alle Generierungsalgorithmen.

Der Aufrufer (API-Endpunkt) setzt mit ``time_budget(deadline)`` eine Deadline fuer
den aktuellen Thread. Jede wachsende Schleife in den Generatoren ruft
``checkpoint()`` auf; ist die Deadline ueberschritten, wird ``BudgetExceeded``
geworfen und die Berechnung sofort beendet (statt im Hintergrund weiterzulaufen
und Speicher/CPU zu blockieren).

Ohne gesetztes Budget (z. B. in Unit-Tests oder direkten Aufrufen) ist
``checkpoint()`` wirkungslos.
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from math import prod
from typing import Dict, Iterator, List, Optional

_local = threading.local()


class BudgetExceeded(Exception):
    """Zeitbudget der Generierung ueberschritten."""


@contextmanager
def time_budget(deadline: Optional[float]) -> Iterator[None]:
    """Setzt die Deadline (Unix-Zeit wie time.time()) fuer den aktuellen Thread."""
    previous = getattr(_local, "deadline", None)
    _local.deadline = deadline
    try:
        yield
    finally:
        _local.deadline = previous


def checkpoint() -> None:
    """Bricht mit BudgetExceeded ab, wenn die Deadline des Threads ueberschritten ist."""
    deadline = getattr(_local, "deadline", None)
    if deadline is not None and time.time() > deadline:
        raise BudgetExceeded()


def count_t_tuples(categories: Dict[str, List[str]], t: int) -> int:
    """Anzahl der t-Tupel (Summe ueber alle t-Kombinationen von Kategorien des
    Produkts ihrer Werteanzahlen), berechnet ohne Aufzaehlung.

    Entspricht dem elementarsymmetrischen Polynom e_t der Werteanzahlen.
    """
    sizes = [len(v) for v in categories.values()]
    if t <= 0:
        return 1
    if t >= len(sizes):
        return prod(sizes) if sizes else 0
    e = [1] + [0] * t
    for s in sizes:
        for k in range(t, 0, -1):
            e[k] += e[k - 1] * s
    return e[t]
