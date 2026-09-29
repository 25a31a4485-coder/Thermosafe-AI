import os
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    """
    APP_NAME: str = "SIH26162 Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api"

    # CORS origins
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database Configuration (Defaults to SQLite for local development)
    DATABASE_URL: str = "sqlite:///./sih26162.db"

    # JWT & Security Configuration
    SECRET_KEY: str = "sih26162_super_secret_jwt_key_thermalwatch_ai_2026_dev_env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Satellite & NASA FIRMS Telemetry Settings
    SATELLITE_DATA_MODE: str = "live"  # Primary default is now "live"
    FIRMS_MAP_KEY: Optional[str] = None
    NASA_FIRMS_API_KEY: Optional[str] = None
    NASA_FIRMS_MAP_KEY: Optional[str] = None
    FIRMS_API_KEY: Optional[str] = None
    MAP_KEY: Optional[str] = None
    NASA_FIRMS_BASE_URL: str = "https://firms.modaps.eosdis.nasa.gov"
    NASA_FIRMS_TIMEOUT_SECONDS: int = 30
    FIRMS_REFRESH_INTERVAL_SECONDS: int = 900  # 15 minutes default background refresh
    FIRMS_RETENTION_DAYS: int = 2  # Live event retention window (days)
    FIRMS_CIRCUIT_BREAKER_FAILURES: int = 3  # Consecutive failures before circuit breaker trips
    FIRMS_CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = 180  # Cooldown window in seconds
    FIRMS_PREFERRED_SENSOR: str = "VIIRS_NOAA21_NRT"
    FIRMS_FALLBACK_SENSOR: str = "VIIRS_NOAA20_NRT"
    FIRMS_DEFAULT_AREA: str = "IND"

    @property
    def effective_firms_map_key(self) -> Optional[str]:
        """
        Resolves the NASA FIRMS Map Key with strict canonical precedence:
        1. FIRMS_MAP_KEY (canonical primary variable)
        2. NASA_FIRMS_API_KEY (backward-compatible fallback)
        3. NASA_FIRMS_MAP_KEY
        4. FIRMS_API_KEY
        5. MAP_KEY
        Also directly inspects os.environ for immediate visibility on cloud runtimes like Render.
        """
        candidates = [
            self.FIRMS_MAP_KEY,
            self.NASA_FIRMS_API_KEY,
            self.NASA_FIRMS_MAP_KEY,
            self.FIRMS_API_KEY,
            self.MAP_KEY,
            os.environ.get("FIRMS_MAP_KEY"),
            os.environ.get("NASA_FIRMS_API_KEY"),
            os.environ.get("NASA_FIRMS_MAP_KEY"),
            os.environ.get("FIRMS_API_KEY"),
            os.environ.get("MAP_KEY"),
        ]
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                cleaned = candidate.strip().strip('"').strip("'")
                if cleaned and cleaned not in ["your-nasa-firms-map-key", '""', "''", "none", "null"]:
                    return cleaned
        return None

    # Firebase Cloud Messaging & Push Notification Settings
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = "thermosafe-ai-sih26162"
    FIREBASE_API_KEY: Optional[str] = None
    FIREBASE_APP_ID: Optional[str] = None
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
