"""BUG A-16 (REQ-6005): Serverseitige Fehlermeldungen mit Code und Sprache.

Jede feste Meldung eines HTTPException erhaelt einen sprachneutralen `code`
und wird nach `Accept-Language` uebersetzt (de/en). Ohne Header bleibt Deutsch.
Meldungen, die selbst schon ein Code sind (z. B. "password_change_required"),
bleiben unveraendert, weil das Frontend sie auswertet.

Der Vergleich ist normalisiert (Gross-/Kleinschreibung, Umlaut-Schreibweise,
Punkt am Ende), damit Schreibvarianten im Code dieselbe Meldung treffen.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# code -> (deutsch, englisch). Die deutsche Fassung ist zugleich der Suchschluessel.
MESSAGES: dict[str, Tuple[str, str]] = {
    "api_token_blocked_endpoint": ("API-Tokens duerfen nicht fuer diesen Endpunkt verwendet werden",
                                   "API tokens must not be used for this endpoint"),
    "bugmagnet_load_failed": ("BugMagnet JSON konnte nicht geladen werden", "BugMagnet JSON could not be loaded"),
    "combine_rule_needs_target": ("Combine-Regel benötigt mindestens einen Zielwert",
                                  "Combine rule needs at least one target value"),
    "constraint_not_found": ("Constraint nicht gefunden", "Constraint not found"),
    "invalid_export_format": ("Unbekanntes Exportformat", "Unknown export format"),
    "model_not_utf8": ("Die Modelldatei muss UTF-8-kodiert sein", "The model file must be UTF-8 encoded"),
    "persist_requires_export": ("persist=false ist nur zusammen mit export moeglich",
                                "persist=false is only possible together with export"),
    "insufficient_scope_export": ("API-Token hat nicht den erforderlichen Scope: export",
                                  "The API token lacks the required scope: export"),
    "model_content_type": ("Content-Type muss 'text/yaml' oder 'application/json' sein",
                           "Content-Type must be 'text/yaml' or 'application/json'"),
    "constraint_reference_invalid": (
        "Das Constraint verweist auf Kategorien oder Werte, die es in diesem Projekt nicht gibt",
        "The constraint refers to categories or values that do not exist in this project"),
    "password_in_url": ("Das Passwort darf nicht in der URL uebergeben werden",
                        "The password must not be passed in the URL"),
    "password_in_url_backup": ("Das Passwort darf nicht in der URL uebergeben werden. Nutze POST /api/backup mit JSON-Body",
                               "The password must not be passed in the URL. Use POST /api/backup with a JSON body"),
    "database_reset_failed": ("Datenbank konnte nicht zurueckgesetzt werden", "Database could not be reset"),
    "dataclass_name_exists": ("Datenklasse mit diesem Namen existiert bereits", "A data class with this name already exists"),
    "dataclass_not_found": ("Datenklasse nicht gefunden", "Data class not found"),
    "user_deactivated": ("Der Nutzer ist deaktiviert", "The user is deactivated"),
    "rule_exists": ("Diese Regel existiert bereits", "This rule already exists"),
    "version_conflict": ("Diese Ressource wurde zwischenzeitlich geaendert", "This resource has been changed in the meantime"),
    "cannot_change_own_role": ("Du kannst deine eigene Rolle nicht aendern", "You cannot change your own role"),
    "cannot_deactivate_self": ("Du kannst dich selbst nicht deaktivieren", "You cannot deactivate yourself"),
    "cannot_delete_self": ("Du kannst dich selbst nicht loeschen", "You cannot delete yourself"),
    "datanode_cycle": ("Ein Knoten kann nicht unter sich selbst oder einem seiner Unterknoten eingeordnet werden",
                       "A node cannot be placed below itself or one of its descendants"),
    "parent_node_not_found": ("Elternknoten nicht gefunden", "Parent node not found"),
    "seeds_required": ("Entweder seed_set_id oder seeds erforderlich", "Either seed_set_id or seeds is required"),
    "rule_needs_then_value": ("Exclude-/Dependency-Regel benötigt einen Zielwert (then_value)",
                              "Exclude/dependency rule needs a target value (then_value)"),
    "backup_password_or_file": ("Falsches Passwort oder beschadigte Datei", "Wrong password or damaged file"),
    "generation_not_found": ("Generierung nicht gefunden", "Generation not found"),
    "rule_same_category": ("IF- und THEN-Kategorie dürfen nicht identisch sein",
                           "IF and THEN category must not be identical"),
    "category_not_in_project": ("Kategorie gehört nicht zu diesem Projekt", "Category does not belong to this project"),
    "category_not_found": ("Kategorie nicht gefunden", "Category not found"),
    "no_refresh_token": ("Kein Refresh-Token", "No refresh token"),
    "generation_access_denied": ("Kein Zugriff auf diese Generierung", "No access to this generation"),
    "project_access_denied": ("Kein Zugriff auf dieses Projekt", "No access to this project"),
    "invalid_zip": ("Keine gueltige ZIP-Datei", "Not a valid ZIP file"),
    "account_deactivated": ("Konto ist deaktiviert", "Account is deactivated"),
    "hierarchy_max_depth": ("Maximale Hierarchie-Tiefe (3 Ebenen) erreicht", "Maximum hierarchy depth (3 levels) reached"),
    "membership_not_found": ("Mitgliedschaft nicht gefunden", "Membership not found"),
    "rule_targets_not_found": ("Nicht alle Zielwerte gefunden", "Not all target values found"),
    "tokens_for_others_admin_only": ("Nur Admins duerfen Tokens fuer andere Nutzer anlegen",
                                     "Only admins may create tokens for other users"),
    "member_remove_forbidden": ("Nur Projekt-Editor oder Admin koennen Mitglieder entfernen",
                                "Only project editors or admins can remove members"),
    "member_add_forbidden": ("Nur Projekt-Editor oder Admin koennen Mitglieder hinzufuegen",
                             "Only project editors or admins can add members"),
    "member_exists": ("Nutzer ist bereits Mitglied dieses Projekts", "User is already a member of this project"),
    "user_not_found": ("Nutzer nicht gefunden", "User not found"),
    "password_required": ("Passwort erforderlich", "Password required"),
    "project_has_generations": ("Project has generations. Use force=true to delete",
                                "Project has generations. Use force=true to delete"),
    "project_not_found": ("Projekt nicht gefunden", "Project not found"),
    "project_not_found_en": ("Project not found", "Project not found"),
    "project_without_categories": ("Projekt hat keine Kategorien", "Project has no categories"),
    "project_needs_values": ("Projekt muss Kategorien und Werte enthalten", "Project must contain categories and values"),
    "rate_limit_exceeded": ("Rate-Limit fuer API-Token ueberschritten", "Rate limit for API token exceeded"),
    "refresh_token_expired": ("Refresh-Token abgelaufen", "Refresh token expired"),
    "rule_not_found": ("Regel nicht gefunden", "Rule not found"),
    "not_found": ("Ressource nicht gefunden", "Resource not found"),
    "restore_failed": ("Restore fehlgeschlagen. Datenbank wurde nicht geaendert",
                       "Restore failed. The database was not changed"),
    "seed_set_not_found": ("Seed-Satz nicht gefunden", "Seed set not found"),
    "session_expired": ("Sitzung abgelaufen, bitte neu anmelden", "Session expired, please log in again"),
    "system_dataclass_delete": ("System-Datenklassen koennen nicht geloescht werden", "System data classes cannot be deleted"),
    "system_dataclass_admin_only": ("System-Datenklassen koennen nur von Admins geaendert werden",
                                    "System data classes can only be changed by admins"),
    "testcase_not_found": ("Testfall nicht gefunden", "Test case not found"),
    "token_not_found": ("Token nicht gefunden", "Token not found"),
    "tokens_for_others_api_user_only": (
        "Tokens fuer andere Nutzer sind nur fuer technische Nutzer (Rolle api_user) erlaubt",
        "Tokens for other users are only allowed for technical users (role api_user)"),
    "invalid_backup": ("Ungueltige Backup-Datei", "Invalid backup file"),
    "invalid_json": ("Ungueltige JSON-Datei", "Invalid JSON file"),
    "invalid_constraint_type": ("Ungueltiger Constraint-Typ. Gueltige Typen: E, O, I, R, M",
                                "Invalid constraint type. Valid types: E, O, I, R, M"),
    "invalid_constraint_ast": ("Ungueltiges Constraint-AST", "Invalid constraint AST"),
    "invalid_credentials": ("Ungültige Anmeldedaten", "Invalid credentials"),
    "invalid_refresh_token": ("Ungültiger Refresh-Token", "Invalid refresh token"),
    "invalid_token_type": ("Ungültiger Token-Typ", "Invalid token type"),
    "encryption_unavailable": ("Verschluesselung nicht verfuegbar", "Encryption not available"),
    "encryption_unavailable_install": ("Verschluesselung nicht verfuegbar. Installiere 'cryptography'",
                                       "Encryption not available. Install 'cryptography'"),
    "viewer_read_only": ("Viewer-Rolle erlaubt keine Schreiboperationen", "The viewer role does not allow write operations"),
    "value_not_found": ("Wert nicht gefunden", "Value not found"),
    "login_rate_limited": ("Zu viele Login-Versuche. Bitte versuche es spaeter erneut",
                           "Too many login attempts. Please try again later"),
    "api_user_no_ui_login": ("api_user kann sich nicht per Oberflaeche anmelden. Verwende ein API-Token",
                             "api_user cannot log in via the user interface. Use an API token"),
    "combine_rule_no_targets": ("combine-Regel hat keine Zielwerte", "Combine rule has no target values"),
    "forbid_without_consequence": ("forbid-Constraints duerfen kein 'consequence'-Feld haben",
                                   "forbid constraints must not have a 'consequence' field"),
    "model_format": ("format muss 'yaml' oder 'json' sein", "format must be 'yaml' or 'json'"),
    "invalid_format": ("format muss json oder csv sein", "format must be json or csv"),
    "implies_needs_consequence": ("implies-Constraints brauchen ein 'consequence'-Feld",
                                  "implies constraints need a 'consequence' field"),
    "openpyxl_missing": ("openpyxl nicht installiert", "openpyxl is not installed"),
    "values_order_incomplete": ("order muss genau alle Werte der Kategorie enthalten",
                                "order must contain exactly all values of the category"),
    "parent_value_wrong_category": ("parent_value_id gehoert nicht zu dieser Kategorie",
                                    "parent_value_id does not belong to this category"),
    "value_ids_not_list": ("value_ids must be a list", "value_ids must be a list"),
    "internal_error": ("Interner Serverfehler", "Internal server error"),
    "not_authenticated": ("Nicht authentifiziert", "Not authenticated"),
    "token_expired": ("Token abgelaufen", "Token expired"),
    "invalid_token": ("Ungultiges Token", "Invalid token"),
}

_CODE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _normalize(text: str) -> str:
    t = text.strip().casefold()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"\s+", " ", t)
    return t.rstrip(". ")


_BY_TEXT: dict[str, str] = {_normalize(de): code for code, (de, _en) in MESSAGES.items()}
# Gaengige Schreibvariante ohne Umlaut-Ersatz (z. B. "Ungultiges" statt "Ungueltiges")
_BY_TEXT.update({_normalize(de).replace("ue", "u"): code for code, (de, _en) in MESSAGES.items()
                 if _normalize(de).replace("ue", "u") not in _BY_TEXT})


def lookup(text: str) -> Optional[str]:
    """Code zu einer festen Meldung (None, wenn unbekannt)."""
    return _BY_TEXT.get(_normalize(text))


def is_code(text: str) -> bool:
    return bool(_CODE_RE.match(text))


def detect_language(accept_language: str | None) -> str:
    """Erste unterstuetzte Sprache aus Accept-Language (de/en), sonst de."""
    for part in (accept_language or "").split(","):
        tag = part.split(";")[0].strip().lower()
        if tag.startswith("en"):
            return "en"
        if tag.startswith("de"):
            return "de"
    return "de"


def localize_text(text: str, lang: str) -> Tuple[str, Optional[str]]:
    """(Text in der Sprache, Code) fuer eine Meldung; unbekannte Texte bleiben unveraendert."""
    if is_code(text):
        return text, None  # ist selbst der Code; Antwort bleibt unveraendert (z. B. REQ-4028)
    code = lookup(text)
    if code is None:
        return text, None
    return (MESSAGES[code][1] if lang == "en" else text), code


def localize_detail(detail, lang: str):
    """(detail, code) fuer eine HTTPException-Detailangabe (Text oder Objekt)."""
    if isinstance(detail, str):
        return localize_text(detail, lang)
    if isinstance(detail, dict):
        out = dict(detail)
        code = out.get("code")
        for key in ("detail", "message"):
            if isinstance(out.get(key), str):
                text, found = localize_text(out[key], lang)
                out[key] = text
                code = code or found
        return out, code
    return detail, None
