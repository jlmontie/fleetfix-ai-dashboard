"""
FleetFix Database Configuration
Database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseConfig:
    """Database configuration and session management"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def session_scope(self):
        """Context manager for database sessions"""
        from contextlib import contextmanager
        
        @contextmanager
        def _session_scope():
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        
        return _session_scope()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.session_scope() as session:
                result = session.execute(text("SELECT 1")).fetchone()
                return True, "Connection successful"
        except Exception as e:
            return False, str(e)


# Global database config instance
db_config = DatabaseConfig()
