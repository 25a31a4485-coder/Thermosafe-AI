# THERMOSAFE AI (Problem Statement SIH26162)

> **Autonomous Industrial Thermal Anomaly Detection, Multi-Factor Risk Assessment & Disaster Mitigation Platform**
> Developed for **Smart India Hackathon 2026**.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900.svg)](https://leafletjs.com/)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)]()

---

## 1. System Architecture

THERMOSAFE AI is architected as a decoupled, multi-tier industrial intelligence platform:

```mermaid
graph TD
    subgraph Client ["Client Tier (Browser)"]
        Browser["User Browser / Desktop & Mobile Views"]
    end

    subgraph FrontendTier ["Frontend Tier (Static / Edge CDN)"]
        Frontend["Leaflet 1.9.4 GIS Map + Analytical Console (HTML5/CSS3/Vanilla JS)"]
        FrontendEnv["frontend/.env (VITE_API_BASE_URL)"]
    end

    subgraph BackendTier ["Backend Tier (FastAPI Service)"]
        FastAPI["FastAPI REST API Service (:8000)"]
        AuthModule["JWT & Bcrypt Security Layer"]
        RiskEngine["Multi-Factor Industrial Risk Engine"]
        AIEngine["Thermal Anomaly Classification Engine"]
        FirmsClient["NASA FIRMS Satellite Client (MODIS & VIIRS)"]
    end

    subgraph DatabaseTier ["Database Tier (Relational Storage)"]
        SQLite["Development: SQLite (sih26162.db)"]
        Postgres["Production: PostgreSQL 15+ (AWS RDS / GCP Cloud SQL)"]
    end

    subgraph SatelliteAPI ["External Providers"]
        NASA["NASA FIRMS NRT Satellite Telemetry"]
    end

    Browser -->|HTTP/HTTPS| Frontend
    Frontend -->|REST API Requests| FastAPI
    FastAPI --> AuthModule
    FastAPI --> RiskEngine
    FastAPI --> AIEngine
    FastAPI --> FirmsClient
    FirmsClient -.->|Optional Live Mode| NASA
    FastAPI -->|SQLAlchemy 2.0 ORM| Postgres
    FastAPI -.->|Local Dev Fallback| SQLite
```

---

## 2. Directory Structure

```
SIH/
├── .env.example                 # Unified full-stack environment template
├── .gitignore                   # Root gitignore (protects secrets, .env, DBs)
├── README.md                    # Root project documentation (this file)
├── backend/
│   ├── .env.example             # Backend environment template
│   ├── .gitignore               # Backend gitignore
│   ├── README.md                # Dedicated backend documentation
│   ├── requirements.txt         # Python dependencies
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint & middleware
│   │   ├── core/                # Config, database engine, security, seed data
│   │   ├── models/              # SQLAlchemy database ORM models
│   │   ├── schemas/             # Pydantic data validation schemas
│   │   ├── routers/             # API routes (events, facilities, ai, risk, etc.)
│   │   └── services/            # FIRMS telemetry, AI classification, risk engines
│   └── test_*.py                # Automated integration and regression test suites
└── frontend/
    ├── .env.example             # Frontend environment template
    ├── .gitignore               # Frontend gitignore
    └── index.html               # Industrial GIS Map & Analytical Console
```

---

## 3. Quick Start (Local Development)

### 3.1 Backend Setup

1. **Open a terminal in the `backend` folder**:
   ```bash
   cd backend
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   # Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize `.env` from template**:
   ```bash
   cp .env.example .env
   ```

5. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *The backend starts at `http://127.0.0.1:8000`. Database tables and demo data are auto-seeded on first run.*

---

### 3.2 Frontend Setup

1. **Open a second terminal in the `frontend` folder**:
   ```bash
   cd frontend
   ```

2. **Configure `.env`**:
   ```bash
   cp .env.example .env
   ```
   *Default value: `VITE_API_BASE_URL=http://localhost:8000`*

3. **Serve the frontend**:
   ```bash
   # Using Python built-in HTTP server:
   python -m http.server 5173

   # Or using Node http-server / npx serve:
   npx serve -l 5173 .
   ```

4. **Access the application**:
   Open **[http://localhost:5173](http://localhost:5173)** in any modern web browser.

---

## 4. Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Description | Default (Dev) | Production Recommendation |
|---|---|---|---|
| `APP_NAME` | Service Name | `THERMOSAFE AI Backend` | `THERMOSAFE AI Backend` |
| `APP_ENV` | Environment Mode | `development` | `production` |
| `DEBUG` | Verbose logging & debug stack traces | `True` | `False` |
| `HOST` | Bind address | `0.0.0.0` | `0.0.0.0` |
| `PORT` | Service port | `8000` | `8000` |
| `API_PREFIX` | Prefix for API routes | `/api` | `/api` |
| `CORS_ORIGINS` | Allowed frontend domains | `["http://localhost:5173", ...]` | `["https://your-frontend-domain.com"]` |
| `DATABASE_URL` | Database connection string | `sqlite:///./sih26162.db` | `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `SECRET_KEY` | 256-bit JWT secret key | Dev default string | High-entropy hex (`secrets.token_hex(32)`) |
| `JWT_ALGORITHM` | Cryptographic algorithm | `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token session validity | `1440` (24h) | `1440` or customized |
| `SATELLITE_DATA_MODE` | Satellite source mode | `demo` | `live` (with NASA Key) or `demo` |
| `NASA_FIRMS_API_KEY` | NASA FIRMS MAP_KEY | `""` | 32-character key from NASA EOSDIS |
| `NASA_FIRMS_BASE_URL` | NASA FIRMS root URL | `https://firms.modaps.eosdis.nasa.gov` | `https://firms.modaps.eosdis.nasa.gov` |
| `NASA_FIRMS_TIMEOUT_SECONDS` | Request timeout | `10` | `10` |

### Frontend (`frontend/.env`)

| Variable | Description | Development | Production Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | URL of the backend API | `http://localhost:8000` | `https://api.thermosafe.yourdomain.com` |

---

## 5. Production Deployment Guide

### 5.1 Database: PostgreSQL Setup
1. Provision a PostgreSQL 15+ database (e.g. AWS RDS, GCP Cloud SQL, or Supabase).
2. Configure connection URL in `backend/.env`:
   ```ini
   DATABASE_URL="postgresql+psycopg2://<db_user>:<db_password>@<db_host>:5432/<db_name>"
   ```
3. The backend automatically leverages connection pooling (`pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`) and automatically creates all required schemas on startup.

### 5.2 Backend: Container & Server Deployment
For Linux or Docker deployments, run with multiple worker processes:

```bash
# Multi-worker Uvicorn:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log

# Or using Gunicorn process manager:
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 60
```

### 5.3 Frontend: Static Hosting
The frontend consists of zero-dependency static assets (`index.html`):
- **Vercel / Netlify**: Deploy the `frontend/` folder directly. Set `VITE_API_BASE_URL` in project settings.
- **Nginx**: Serve static files and proxy `/api` requests to backend:
  ```nginx
  server {
      listen 80;
      server_name thermosafe.yourdomain.com;
      root /var/www/thermosafe/frontend;
      index index.html;

      location /api/ {
          proxy_pass http://127.0.0.1:8000/api/;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

---

## 6. Authentication Setup

Authentication is handled via JWT tokens:
- **Sign Up**: `POST /api/auth/signup`
  - Validates full name, email, password, and assigned role (`admin`, `analyst`, `operator`, `viewer`).
  - Passwords are encrypted with salted `bcrypt`.
- **Log In**: `POST /api/auth/login`
  - Returns bearer token with expiration.
- **User Profile**: `GET /api/auth/me`
  - Requires `Authorization: Bearer <token>` header.

---

## 7. NASA FIRMS Satellite Telemetry: Demo vs. Live Mode

The platform supports both zero-dependency demonstration and live NASA FIRMS feeds:

- **Demo Mode (`SATELLITE_DATA_MODE=demo`)**:
  - Requires **no internet connection** or API key.
  - Returns realistic telemetry across 5 thermal event types (Critical Fire, High-Risk Anomaly, Gas Flare, Persistent Source, Low-Risk Activity).
- **Live Mode (`SATELLITE_DATA_MODE=live`)**:
  - Connects to NASA FIRMS API via HTTPS.
  - Ingests near real-time VIIRS (375m) and MODIS (1km) hotspot detections for India.
  - Automatically falls back to demo telemetry if the NASA service is offline or rate-limited.
  - Obtain a free API key at [NASA FIRMS Map Key](https://firms.modaps.eosdis.nasa.gov/api/map_key/).

---

## 8. API Documentation

Interactive OpenAPI documentation is hosted directly by the backend:
- **Swagger Interactive UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Technical Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Verification**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 9. Verification & Automated Tests

Run the full verification suite from the `backend/` directory:

```bash
# 1. Verify Map & Live Data Integration (16 verification points across 5 event types)
python test_map_integration.py

# 2. Verify Thermal Events CRUD & Spatial Queries
python test_thermal_events.py

# 3. Verify End-to-End System Integration
python test_integration_flow.py

# 4. Verify Authentication & Role Access
python test_auth.py
```

---

## 10. Pre-Deployment Security Checklist

Before deploying to production, confirm the following:
- [x] `.env` files are excluded via `.gitignore` and never committed to version control.
- [x] `SECRET_KEY` has been generated with a high-entropy random value.
- [x] `DEBUG` is set to `False`.
- [x] `CORS_ORIGINS` is restricted to authorized frontend domains.
- [x] `DATABASE_URL` points to an authenticated, managed PostgreSQL instance.
- [x] `VITE_API_BASE_URL` in the frontend points to the production backend API URL.
