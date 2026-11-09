"""Auth-Logik fuer Passwortwechsel und Erststart-Hinweis (REQ-4027, REQ-4028).

Router -> auth_service -> Models/DB. Keine HTTP-Konzepte in dieser Schicht.
Passwoerter werden nie zurueckgegeben oder geloggt (REQ-4028 AK-9).
"""
from sqlalchemy.orm import Session

from .models.auth import User
from .password_policy import ERROR_CURRENT_PASSWORD_INVALID, PasswordError, validate_new_password


def apply_new_password(user: User, new_password: str) -> None:
    """Validiert und setzt ein neues Passwort.

    REQ-4028 AK-6 / REQ-4027 AK-10: Ein erfolgreicher Wechsel auf einen Nicht-Default-Wert
    loescht das Flag default_password_active. Die Policy garantiert, dass der Wert kein
    Standardpasswort ist.
    """
    validate_new_password(new_password)
    user.set_password(new_password)
    user.default_password_active = False


def change_own_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    """REQ-4028 AK-3: Selbst-Wechsel. Aktuelles Passwort muss stimmen."""
    if not user.check_password(current_password):
        raise PasswordError(ERROR_CURRENT_PASSWORD_INVALID)
    apply_new_password(user, new_password)
    db.commit()


def admin_set_password(db: Session, target: User, new_password: str) -> None:
    """REQ-4025 / REQ-4028 AK-4/AK-5: Admin setzt das Passwort eines Nutzers."""
    apply_new_password(target, new_password)
    db.commit()


def is_first_start_hint_active(db: Session) -> bool:
    """REQ-4027 AK-2/AK-4/AK-10: Es existiert ein aktiver Nutzer mit gesetztem Flag."""
    return (
        db.query(User.id)
        .filter(User.is_active == True, User.default_password_active == True)  # noqa: E712
        .first()
        is not None
    )
