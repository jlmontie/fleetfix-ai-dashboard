"""
FleetFix Database Configuration
Database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/fleetfix"
        )
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,  # Verify connections before using
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries
            poolclass=NullPool if os.getenv("TESTING") else None
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations
        
        Usage:
            with db_config.session_scope() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()


# Global database configuration instance
db_config = DatabaseConfig()


def get_db_connection() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI
    
    Usage in FastAPI endpoint:
        @app.get("/vehicles")
        def get_vehicles(db: Session = Depends(get_db_connection)):
            return db.query(Vehicle).all()
    """
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=db_config.engine)


def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    from database.models import Base
    Base.metadata.drop_all(bind=db_config.engine)


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    print(f"Database URL: {db_config.database_url}")
    
    try:
        with db_config.session_scope() as session:
            result = session.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")