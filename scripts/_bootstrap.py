"""Permite ejecutar los scripts con `python scripts/x.py` además de `python -m scripts.x`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
