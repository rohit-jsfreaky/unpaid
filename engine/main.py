"""Vercel entrypoint: the engine's FastAPI app (see vercel.json). The code lives in src/, so src/ goes on the path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from unpaid.api import app

__all__ = ["app"]
