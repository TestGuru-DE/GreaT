"""Seed: Beispielprojekt Portoberechnung – REQ-4017."""
from sqlalchemy.orm import Session
from app.models import Project, Category, Value


EXAMPLE_PROJECT_NAME = "Portoberechnung (Beispiel)"


def seed_example_project(db: Session) -> None:
    """
    Legt das Beispielprojekt an falls es nicht existiert.
    Wird beim App-Start aufgerufen.
    """
    existing = db.query(Project).filter(Project.name == EXAMPLE_PROJECT_NAME).first()
    if existing:
        return  # Bereits vorhanden

    project = Project(name=EXAMPLE_PROJECT_NAME)
    db.add(project)
    db.flush()

    categories = [
        {
            "name": "Gewicht",
            "values": [
                {"value": "0–500g", "allowed": True, "risk_weight": 1},
                {"value": "501g–1kg", "allowed": True, "risk_weight": 2},
                {"value": "1kg–2kg", "allowed": True, "risk_weight": 2},
                {"value": "über 2kg", "allowed": True, "risk_weight": 3},
            ]
        },
        {
            "name": "Größe",
            "values": [
                {"value": "Briefumschlag", "allowed": True, "risk_weight": 1},
                {"value": "Großbrief", "allowed": True, "risk_weight": 1},
                {"value": "Päckchen", "allowed": True, "risk_weight": 2},
                {"value": "Paket", "allowed": True, "risk_weight": 3},
            ]
        },
        {
            "name": "Transportart",
            "values": [
                {"value": "Standard", "allowed": True, "risk_weight": 1},
                {"value": "Express", "allowed": True, "risk_weight": 2},
                {"value": "Overnight", "allowed": True, "risk_weight": 3},
            ]
        },
        {
            "name": "Zielland",
            "values": [
                {"value": "Deutschland", "allowed": True, "risk_weight": 1},
                {"value": "EU", "allowed": True, "risk_weight": 2},
                {"value": "Weltweit", "allowed": True, "risk_weight": 3},
            ]
        },
        {
            "name": "Portopreis (Ergebnis)",
            "values": [
                {"value": "0,85 €", "allowed": True, "risk_weight": 1},
                {"value": "1,55 €", "allowed": True, "risk_weight": 1},
                {"value": "2,70 €", "allowed": True, "risk_weight": 1},
                {"value": "4,00 €", "allowed": True, "risk_weight": 1},
                {"value": "6,90 €", "allowed": True, "risk_weight": 1},
                {"value": "14,90 €", "allowed": True, "risk_weight": 1},
            ]
        },
    ]

    for cat_data in categories:
        cat = Category(name=cat_data["name"], project_id=project.id)
        db.add(cat)
        db.flush()
        for val_data in cat_data["values"]:
            val = Value(
                value=val_data["value"],
                category_id=cat.id,
                allowed=val_data["allowed"],
                risk_weight=val_data["risk_weight"],
            )
            db.add(val)

    db.commit()
