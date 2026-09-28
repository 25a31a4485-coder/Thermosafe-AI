"""
Vercel Serverless Function Entrypoint Bridge for ThermoSafe AI.
Enables instant discovery by Vercel's default Python runtime locator
while preserving backend/app/main.py configuration.
"""
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend = os.path.join(_root, "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.main import app

# Export app variable explicitly for Vercel
__all__ = ["app"]
