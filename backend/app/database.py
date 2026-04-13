"""PostgreSQL connection via SQLAlchemy (sync mode with psycopg)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings


settings = get_settings()

# Use psycopg v3 dialect explicitly
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(db_url, echo=settings.DEBUG, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully")

        # Auto-migrate: add missing columns to existing tables
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        migrations = [
            ("deals", "won_at", "TIMESTAMP"),
        ]
        with engine.begin() as conn:
            for table, column, col_type in migrations:
                existing_cols = [c["name"] for c in inspector.get_columns(table)]
                if column not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    print(f"Migration: added {table}.{column} ({col_type})")

    except Exception as e:
        print(f"Warning: Database init failed: {e}")
        print("App will start, but DB features won't work until connection is available")
