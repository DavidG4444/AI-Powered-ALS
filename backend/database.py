from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import get_settings
from models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before using
    pool_size=5,          # Number of connections to maintain
    max_overflow=10       # Extra connections if needed
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency for FastAPI routes
    Creates a new database session for each request
    Automatically closes session after request

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database
    Creates all tables defined in models.py
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False

def test_connection():
    """
    Test database connection
    """
    try:
        logger.info("Testing database connection...")
        with engine.connect() as connection:
            logger.info("✅ Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

#def drop_all_tables():
    """
    ⚠️ WARNING: Drops all tables!
    Use only in development for clean slate
    """
    #logger.warning("⚠️ Dropping all database tables...")
    #Base.metadata.drop_all(bind=engine)
    #logger.info("✅ All tables dropped")

# Test connection on import
'''
Only run when explicitly called

if __name__ == "__main__":
    test_connection()
    init_db()
'''
