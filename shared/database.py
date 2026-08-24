import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)

# Connect to Postgres container or fallback to local SQLite for 100% uptime
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = None

# Try to use PostgreSQL if configured
if SQLALCHEMY_DATABASE_URL:
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, echo=False)
        # Test connection
        with engine.connect() as conn:
            logger.info("✓ PostgreSQL connection successful")
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
        engine = None

# Use SQLite for bulletproof local reliability
if engine is None:
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "swiply.db"))
        SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False},
            echo=False
        )
        logger.info(f"✓ Using SQLite database at {db_path}")
    except Exception as e:
        logger.error(f"Failed to create SQLite engine: {e}")
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

