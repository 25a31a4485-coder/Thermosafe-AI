import os
import sys

# Ensure backend directory is in sys.path so that 'from app...' imports succeed
# when backend is imported as a package from the project root (e.g. Vercel entrypoint backend.app.main:app)
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
