"""
templates_config.py – G.R.E.A.T. Jinja2-Templates-Singleton
Einmaliges Initialisieren – importierbar aus allen Routern.
"""
import os
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
