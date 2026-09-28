import logging
from sqlalchemy import inspect
from app.core.database import Base, engine
import app.models  # Ensures all models are registered in Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")


def init_db() -> list[str]:
    """
    Safely creates all database tables and indexes registered in Base.metadata.
    Applies non-destructive column additions for local development databases.
    Returns the list of table names present in the database.
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Migrate alerts table columns if not present
    if "alerts" in tables:
        existing_cols = {c["name"] for c in inspector.get_columns("alerts")}
        columns_to_add = [
            ("event_id", "VARCHAR(100)"),
            ("risk_score", "FLOAT"),
            ("risk_priority", "VARCHAR(50)"),
            ("latitude", "FLOAT"),
            ("longitude", "FLOAT"),
            ("event_type", "VARCHAR(100)"),
            ("is_acknowledged", "BOOLEAN DEFAULT 0"),
            ("acknowledged_at", "DATETIME"),
            ("acknowledged_by", "VARCHAR(255)"),
            ("acknowledged_by_user_id", "INTEGER"),
            ("assigned_team_id", "INTEGER"),
            ("status", "VARCHAR(50) DEFAULT 'ACTIVE'"),
            ("delivery_status", "VARCHAR(50) DEFAULT 'SENT'"),
        ]
        with engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                if col_name not in existing_cols:
                    logger.info(f"Migrating alerts table: Adding column {col_name} ({col_type})")
                    from sqlalchemy import text
                    conn.execute(text(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_type}"))
            conn.commit()

    # Migrate reports table columns if not present
    if "reports" in tables:
        existing_report_cols = {c["name"] for c in inspector.get_columns("reports")}
        report_columns_to_add = [
            ("summary", "JSON"),
            ("content", "JSON"),
            ("status", "VARCHAR(50) DEFAULT 'completed'"),
        ]
        with engine.connect() as conn:
            from sqlalchemy import text
            for col_name, col_type in report_columns_to_add:
                if col_name not in existing_report_cols:
                    logger.info(f"Migrating reports table: Adding column {col_name} ({col_type})")
                    conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}"))
            conn.commit()

    # Migrate users table columns if not present
    if "users" in tables:
        existing_user_cols = {c["name"] for c in inspector.get_columns("users")}
        if "operator_team_id" not in existing_user_cols:
            logger.info("Migrating users table: Adding column operator_team_id (INTEGER)")
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN operator_team_id INTEGER"))
                conn.commit()

    # Migrate emergency_response_teams table columns if not present
    if "emergency_response_teams" in tables:
        existing_team_cols = {c["name"] for c in inspector.get_columns("emergency_response_teams")}
        team_columns_to_add = [
            ("team_name", "VARCHAR(255)"),
            ("organization_name", "VARCHAR(255)"),
            ("industry_type", "VARCHAR(100)"),
            ("phone", "VARCHAR(50)"),
            ("email", "VARCHAR(255)"),
            ("response_radius_km", "FLOAT"),
            ("notification_enabled", "BOOLEAN DEFAULT 1"),
            ("call_escalation_enabled", "BOOLEAN DEFAULT 1"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("updated_at", "DATETIME"),
        ]
        with engine.connect() as conn:
            from sqlalchemy import text
            for col_name, col_type in team_columns_to_add:
                if col_name not in existing_team_cols:
                    logger.info(f"Migrating emergency_response_teams table: Adding column {col_name} ({col_type})")
                    conn.execute(text(f"ALTER TABLE emergency_response_teams ADD COLUMN {col_name} {col_type}"))
            conn.commit()

    # Migrate risk_assessments table columns if not present
    if "risk_assessments" in tables:
        existing_risk_cols = {c["name"] for c in inspector.get_columns("risk_assessments")}
        if "methodology" not in existing_risk_cols:
            logger.info("Migrating risk_assessments table: Adding column methodology (VARCHAR(255))")
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE risk_assessments ADD COLUMN methodology VARCHAR(255)"))
                conn.commit()

    logger.info(f"Database schema initialized successfully. Active tables: {tables}")
    return tables


if __name__ == "__main__":
    tables = init_db()
    print("=" * 60)
    print("DATABASE INITIALIZATION COMPLETE")
    print("Tables created:")
    for t in tables:
        print(f"  - {t}")
    print("=" * 60)
