"""
REQ-6007: Symbolische Werte fuer lange Strings (>500 Zeichen).

Lange Werte (ueber MAX_VALUE_LENGTH) werden symbolisch gespeichert,
z. B. '<STR len=1001 charset=alnum>'. Die echte Zeichenkette entsteht
beim Export bzw. in der Testdaten-Konkretisierung (REQ-6010).

Symbolisches Format: <STR len=N charset=NAME>
- N: Anzahl Unicode-Codepoints
- NAME: Zeichenvorrat (alpha, alnum, alpha_de, special, unicode)
"""

import re
import string
import random
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_VALUE_LENGTH = 500  # Werte darueber werden symbolisch gespeichert

# Charsets (Zeichenvoerraete)
CHARSET_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
CHARSET_ALNUM = CHARSET_ALPHA + "0123456789"
CHARSET_ALPHA_DE = CHARSET_ALPHA + "äöüÄÖÜß"
CHARSET_SPECIAL = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
CHARSET_UNICODE = "αβγδεζηθικλμνξοπρστυφχψω"  # Griechisch als Unicode-Beispiel

CHARSETS = {
    "alpha": CHARSET_ALPHA,
    "alnum": CHARSET_ALNUM,
    "alpha_de": CHARSET_ALPHA_DE,
    "special": CHARSET_SPECIAL,
    "unicode": CHARSET_UNICODE,
}

# Regex zum Parsen symbolischer Werte
SYMBOLIC_PATTERN = re.compile(
    r"^<STR\s+len=(\d+)\s+charset=([a-z_]+)>$"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SymbolicValue:
    """Repräsentiert einen symbolischen String-Wert."""
    length: int
    charset: str

    def __post_init__(self):
        if self.charset not in CHARSETS:
            raise ValueError(f"Unbekanntes charset: {self.charset!r}. Erlaubt: {list(CHARSETS.keys())}")
        if self.length <= 0:
            raise ValueError(f"Länge muss > 0 sein, nicht {self.length}")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_symbolic_value(text: str) -> Optional[SymbolicValue]:
    """
    Parst einen symbolischen Wert-String.

    Args:
        text: String wie '<STR len=1001 charset=alnum>'

    Returns:
        SymbolicValue oder None, wenn der String kein symbolischer Wert ist.

    Raises:
        ValueError: Bei ungültigem Format.
    """
    if not isinstance(text, str):
        return None

    match = SYMBOLIC_PATTERN.match(text.strip())
    if not match:
        return None

    length = int(match.group(1))
    charset = match.group(2)

    if charset not in CHARSETS:
        raise ValueError(f"Unbekanntes charset in symbolischem Wert: {charset!r}")

    return SymbolicValue(length=length, charset=charset)


def is_symbolic(value: str) -> bool:
    """
    Prueft, ob ein Wert ein symbolischer String ist.

    Args:
        value: Zu pruefender String

    Returns:
        True, wenn der String dem symbolischen Format entspricht.
    """
    return SYMBOLIC_PATTERN.match(value.strip()) is not None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_symbolic_string(length: int, charset: str) -> str:
    """
    Generiert einen symbolischen Wert-String.

    Args:
        length: Anzahl Unicode-Codepoints
        charset: Zeichenvorrat-Name

    Returns:
        String wie '<STR len=1001 charset=alnum>'

    Raises:
        ValueError: Bei ungültigen Parametern.
    """
    sv = SymbolicValue(length=length, charset=charset)
    return f"<STR len={sv.length} charset={sv.charset}>"


def concretize_symbolic(symbolic_str: str, seed: Optional[int] = None) -> str:
    """
    Konkretisiert einen symbolischen Wert zu einem echten String.

    Args:
        symbolic_str: Symbolischer Wert wie '<STR len=1001 charset=alnum>'
        seed: Optionaler Seed fuer Reproduzierbarkeit

    Returns:
        Echter String mit der angegebenen Laenge aus dem Zeichenvorrat.

    Raises:
        ValueError: Bei ungültigem symbolischem Wert.
    """
    sv = parse_symbolic_value(symbolic_str)
    if sv is None:
        raise ValueError(f"Kein gueltiger symbolischer Wert: {symbolic_str!r}")

    charset_chars = CHARSETS[sv.charset]
    if seed is not None:
        rng = random.Random(seed)
        return "".join(rng.choice(charset_chars) for _ in range(sv.length))
    return "".join(random.choice(charset_chars) for _ in range(sv.length))


# ---------------------------------------------------------------------------
# Helper: Decide whether to store symbolically
# ---------------------------------------------------------------------------

def should_be_symbolic(length: int) -> bool:
    """
    Gibt True zurueck, wenn ein Wert mit der gegebenen Laenge
    symbolisch gespeichert werden soll.

    Args:
        length: Anzahl Unicode-Codepoints

    Returns:
        True, wenn length > MAX_VALUE_LENGTH.
    """
    return length > MAX_VALUE_LENGTH


def make_value(length: int, charset: str, fill_char: Optional[str] = None) -> str:
    """
    Erstellt entweder einen echten String (kurz) oder einen symbolischen Wert (lang).

    Args:
        length: Anzahl Unicode-Codepoints
        charset: Zeichenvorrat-Name
        fill_char: Optionaler Fuellcharacter fuer echte Strings.
                   Wenn None, wird der erste Character des charset verwendet.

    Returns:
        Echter String oder symbolischer Wert.
    """
    if should_be_symbolic(length):
        return generate_symbolic_string(length, charset)

    charset_chars = CHARSETS[charset]
    if fill_char is None:
        fill_char = charset_chars[0]

    # Fuehre den fill_char im charset? Wenn nicht, nimm den ersten.
    if fill_char not in charset_chars:
        fill_char = charset_chars[0]

    return fill_char * length


def count_codepoints(s: str) -> int:
    """
    Zaehlt die Anzahl Unicode-Codepoints in einem String.

    In Python 3 ist len(str) bereits die Anzahl Codepoints,
    aber dies dient als explizite Dokumentation.

    Args:
        s: Eingabe-String

    Returns:
        Anzahl Unicode-Codepoints.
    """
    return len(s)