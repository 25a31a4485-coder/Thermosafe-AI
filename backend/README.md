# SIH26162 — THERMOSAFE AI Backend API

Production-ready backend API service for **THERMOSAFE AI: Autonomous Industrial Thermal Anomaly & Disaster Mitigation Intelligence Platform** (Smart India Hackathon 2026 — Problem Statement SIH26162).

---

## 1. Architecture Overview

The backend is built with **FastAPI** and **SQLAlchemy**, providing a stateless, horizontally scalable REST API architecture:
- **FastAPI**: Asynchronous web framework with automatic OpenAPI documentation.
- **SQLAlchemy 2.0**: Relational ORM supporting SQLite (development) and PostgreSQL 15+ (production).
- **Pydantic v2**: High-performance request/response data validation and type enforcement.
- **PyJWT & Bcrypt**: RFC 7519 compliant JSON Web Token authentication with salted cryptographic password hashing.
- **AI Classification Engine**: Rule-based heuristic and multi-factor thermal risk assessment engine.
- **NASA FIRMS Service**: Near real-time satellite hotspot telemetry (VIIRS and MODIS) with fault-tolerant offline fallback.

---

## 2. Installation & Local Setup

### Prerequisites
- **Python 3.12+**
- **pip** and **virtualenv**
- (Optional for production) **PostgreSQL 15+**

### Step-by-Step Installation

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
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
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Windows (PowerShell):
   Copy-Item .env.example .env

   # Linux / macOS:
   cp .env.example .env
   ```

5. **Generate a cryptographically secure JWT secret**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Paste the generated value into `SECRET_KEY` inside `.env`.

---

## 3. Database Setup & Persistence

The platform supports both SQLite and PostgreSQL without code changes:

### Development: Local SQLite (Default)
In `backend/.env`:
```ini
DATABASE_URL="sqlite:///./sih26162.db"
```
The database schema and initial demonstration industrial facilities and thermal events are automatically created on first startup via `init_db()` and `seed_demo_thermal_events()`.

### Production: Managed PostgreSQL
1. Create a dedicated database and user on your PostgreSQL instance:
   ```sql
   CREATE DATABASE sih26162_db;
   CREATE USER thermosafe_user WITH ENCRYPTED PASSWORD 'YourStrongPassword2026!';
   GRANT ALL PRIVILEGES ON DATABASE sih26162_db TO thermosafe_user;
   ```

2. In `backend/.env`, set:
   ```ini
   DATABASE_URL="postgresql+psycopg2://thermosafe_user:YourStrongPassword2026!@postgres-host:5432/sih26162_db"
   ```

3. The connection pool automatically enables `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`, and `pool_recycle=1800`.

---

## 4. Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | String | `THERMOSAFE AI Backend` | Application display name |
| `APP_ENV` | String | `development` | Environment mode (`development`, `staging`, `production`) |
| `DEBUG` | Boolean | `True` | Debug mode. **MUST be `False` in production** to disable SQL logs |
| `HOST` | String | `0.0.0.0` | IP interface binding |
| `PORT` | Integer | `8000` | Port number |
| `API_PREFIX` | String | `/api` | Base routing prefix |
| `CORS_ORIGINS` | JSON / String | `["http://localhost:5173", ...]` | Allowed client origins for browser requests |
| `DATABASE_URL` | String | `sqlite:///./sih26162.db` | SQLAlchemy connection URI |
| `SECRET_KEY` | String | *(required)* | 256-bit secret key used to sign JWT tokens |
| `JWT_ALGORITHM` | String | `HS256` | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `1440` | Token lifetime (1440 min = 24 hours) |
| `SATELLITE_DATA_MODE` | String | `demo` | Telemetry mode: `demo` (synthetic) or `live` (NASA FIRMS) |
| `NASA_FIRMS_API_KEY` | String | `""` | 32-character Map Key from NASA FIRMS |
| `NASA_FIRMS_BASE_URL` | String | `https://firms.modaps.eosdis.nasa.gov` | NASA FIRMS API root |
| `NASA_FIRMS_TIMEOUT_SECONDS` | Integer | `10` | NASA FIRMS HTTP request timeout |

---

## 5. Development & Production Run Commands

### Development Server (Auto-reload)
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Production Execution (Uvicorn / Multi-Worker)
```bash
# Recommended for production containers or Linux servers:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
```

### Production Execution with Gunicorn (Process Manager)
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 60
```

### Systemd Service Template (`/etc/systemd/system/thermosafe.service`)
```ini
[Unit]
Description=THERMOSAFE AI Backend API Service
After=network.target postgresql.service

[Service]
User=thermosafe
WorkingDirectory=/var/www/thermosafe/backend
EnvironmentFile=/var/www/thermosafe/backend/.env
ExecStart=/var/www/thermosafe/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 6. Authentication Setup

Authentication uses stateless JWT tokens:
- **Sign Up**: `POST /api/auth/signup`
  - Body: `{"full_name": "...", "email": "...", "password": "...", "role": "analyst"}`
  - Supported roles: `admin`, `analyst`, `operator`, `viewer`.
  - Passwords are encrypted using salted `bcrypt` hashes.
- **Login**: `POST /api/auth/login`
  - Body: `{"email": "...", "password": "..."}`
  - Returns: `{"access_token": "<jwt>", "token_type": "bearer", "user": {...}}`
- **Current User Profile**: `GET /api/auth/me`
  - Header: `Authorization: Bearer <access_token>`

---

## 7. NASA FIRMS Satellite Telemetry Configuration

### Demo Mode vs. Live Mode

| Feature | Demo Mode (`SATELLITE_DATA_MODE=demo`) | Live Mode (`SATELLITE_DATA_MODE=live`) |
|---|---|---|
| **Internet Dependency** | Zero — works completely offline | Requires outbound HTTPS access to NASA EOSDIS |
| **API Key Required** | No | Yes (free 32-character Map Key) |
| **Data Source** | Realistic industrial demo events & telemetry | NASA FIRMS NRT VIIRS / MODIS active fire pixels |
| **Failure Behavior** | Deterministic synthetic events | Automatic fallback to demo data if rate-limited or offline |

### Obtaining a Live NASA FIRMS Key
1. Register at [NASA Earthdata FIRMS Map Key](https://firms.modaps.eosdis.nasa.gov/api/map_key/).
2. A 32-character key will be emailed to you.
3. Configure in `backend/.env`:
   ```ini
   SATELLITE_DATA_MODE="live"
   NASA_FIRMS_API_KEY="your_32_char_key_here"
   ```

---

## 8. API Documentation & Endpoints

Interactive documentation is automatically generated:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: `GET /api/health`

### Key API Router Prefixes

| Router | Prefix | Description |
|---|---|---|
| **Auth** | `/api/auth` | User registration, login, JWT token issuance |
| **Thermal Events** | `/api/thermal-events` | Spatial query, filtering, GeoJSON, bounding box, sorting |
| **Facilities** | `/api/facilities` | Industrial asset inventory, proximity queries |
| **AI Classification** | `/api/ai` | Autonomous thermal pattern and anomaly classification |
| **Risk Assessment** | `/api/risk` | Multi-factor risk scoring engine |
| **Satellite** | `/api/satellite` | NASA FIRMS integration & telemetry ingestion |
| **Alerts** | `/api/alerts` | Critical incident notifications & read status |
| **Analytics** | `/api/analytics` | Statistical aggregates, risk distribution, trends |
| **Reports** | `/api/reports` | Incident reporting, JSON & CSV export |

---

## 9. Testing & Quality Verification

Run the automated integration and unit test suites:
```bash
# Run map and data integration test
python test_map_integration.py

# Run thermal events API test suite
python test_thermal_events.py

# Run end-to-end integration flow
python test_integration_flow.py

# Run authentication test
python test_auth.py
```
