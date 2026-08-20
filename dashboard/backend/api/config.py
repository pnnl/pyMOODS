"""
Central configuration.
Imported first by react_api.py to set up sys.path before any heavy imports.
"""
import os
import sys

from dotenv import load_dotenv

# Load .env from the project root (four levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

_HERE = os.path.dirname(os.path.abspath(__file__))   # …/backend/api/

# Paths for internal packages that live outside this directory
_DASHBOARD_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))          # dashlib/ lives here
_PYMOODS_ROOT   = os.path.abspath(os.path.join(_HERE, '..', '..', '..', 'pymoods'))

for _p in (_DASHBOARD_ROOT, _PYMOODS_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Absolute path to the demo_data directory
DEMO_DATA_DIR = os.path.join(_DASHBOARD_ROOT, 'demo_data')

# ── PNNL AI Incubator ─────────────────────────────────────────────────────────
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL    = os.getenv("AI_MODEL")
