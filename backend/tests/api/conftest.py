"""
Test configuration for API tests
"""
import pytest
import os
from fastapi.testclient import TestClient

# Set testing flag
os.environ["TESTING"] = "true"

from backend.api.main import app, startup_event


@pytest.fixture(scope="session", autouse=True)
async def initialize_app():
    """Initialize app components before any tests run"""
    await startup_event()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)
