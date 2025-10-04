"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require API keys"
    )
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require database connection"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location/name"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "pipeline" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark tests requiring database
        if "test_database" in item.nodeid or "test_schema" in item.nodeid:
            item.add_marker(pytest.mark.requires_db)
        
        # Mark tests requiring API keys
        if "text_to_sql" in item.nodeid or "insight" in item.nodeid:
            item.add_marker(pytest.mark.requires_api)


@pytest.fixture(scope="session")
def check_environment():
    """Check that required environment is available"""
    issues = []
    
    # Check for API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not (has_anthropic or has_openai):
        issues.append("No API key found (set ANTHROPIC_API_KEY or OPENAI_API_KEY)")
    
    # Check for database connection
    if not os.getenv("DATABASE_URL"):
        issues.append("DATABASE_URL not set")
    
    if issues:
        pytest.skip(f"Environment not configured: {'; '.join(issues)}")
    
    return {
        "has_anthropic": has_anthropic,
        "has_openai": has_openai,
        "has_db": bool(os.getenv("DATABASE_URL"))
    }


@pytest.fixture(scope="session")
def test_database_connection():
    """Verify database connection before running tests"""
    try:
        from database.config import db_config
        from sqlalchemy import text
        
        with db_config.session_scope() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


# Fixture to suppress verbose output during tests
@pytest.fixture(autouse=True)
def suppress_output(request):
    """Suppress print statements during tests unless verbose mode"""
    if not request.config.getoption("verbose"):
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        yield
        
        sys.stdout = old_stdout
    else:
        yield
