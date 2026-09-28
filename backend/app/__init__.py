"""
SIH26162 Backend Application Package.
"""
import os
import sys

# Ensure backend directory is in sys.path for direct 'app.*' imports
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

__version__ = "1.0.0"

