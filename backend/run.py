import os
import sys
import uvicorn

# Ensure app package is importable
cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting ThermoSafe AI Production Server on {host}:{port}...")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
