import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# Configure connection arguments and pooling based on database dialect
# Normalize database URL for cloud PostgreSQL providers (Render, Supabase, Neon, etc.)
raw_db_url = settings.DATABASE_URL.strip()
if raw_db_url.startswith("postgres://"):
    db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
    db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    db_url = raw_db_url

# On serverless platforms like Vercel, the root deployment directory is read-only.
# Redirect local SQLite file to the system temp directory so database initialization and writes succeed.
if os.environ.get("VERCEL") and db_url.startswith("sqlite:///"):
    import shutil
    import tempfile
    db_filename = os.path.basename(db_url.replace("sqlite:///", "").replace("\\", "/"))
    tmp_db_path = os.path.join(tempfile.gettempdir(), db_filename).replace("\\", "/")
    if not os.path.exists(tmp_db_path):
        for candidate in [
            db_filename,
            os.path.join("backend", db_filename),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), db_filename),
        ]:
            if os.path.exists(candidate):
                try:
                    shutil.copy2(candidate, tmp_db_path)
                    break
                except Exception:
                    pass
    db_url = f"sqlite:///{tmp_db_path}"



connect_args = {}
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "postgresql" in db_url:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator that yields a database session and ensures it is closed afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
