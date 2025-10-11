"""
FleetFix API Tests (pytest)
Proper pytest test suite for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

from api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "FleetFix AI Dashboard API"
    assert "version" in data
    assert data["version"] == "1.0.0"
    assert "status" in data
    assert "endpoints" in data


def test_health(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "ai_provider" in data
    assert "timestamp" in data


def test_schema(client):
    """Test schema endpoint"""
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert len(data["tables"]) > 0
    
    # Check first table has expected structure
    table = data["tables"][0]
    assert "name" in table
    assert "columns" in table
    assert "row_count" in table


def test_examples(client):
    """Test examples endpoint"""
    response = client.get("/api/examples")
    assert response.status_code == 200
    data = response.json()
    assert "examples" in data
    assert len(data["examples"]) > 0
    
    # Check first category has structure
    category = data["examples"][0]
    assert "category" in category
    assert "queries" in category


def test_query_valid(client):
    """Test valid query execution"""
    response = client.post(
        "/api/query",
        json={
            "query": "SELECT COUNT(*) as total FROM vehicles",
            "include_insights": False,
            "max_rows": 10
        }
    )

    if response.status_code == 500:
        print(f"Error response: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sql" in data
    assert "results" in data  # Changed from "rows" to "results"
    assert "row_count" in data


def test_query_with_insights(client):
    """Test query with insights generation"""
    response = client.post(
        "/api/query",
        json={
            "query": "Show me vehicles overdue for maintenance",
            "include_insights": True,
            "max_rows": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sql" in data
    assert "explanation" in data
    assert "confidence" in data


def test_query_empty(client):
    """Test empty query is rejected"""
    response = client.post(
        "/api/query",
        json={
            "query": "",
            "include_insights": True,
            "max_rows": 10
        }
    )
    assert response.status_code == 422  # Validation error


def test_query_invalid_max_rows(client):
    """Test invalid max_rows is rejected"""
    response = client.post(
        "/api/query",
        json={
            "query": "test",
            "include_insights": True,
            "max_rows": 0  # Should be >= 1
        }
    )
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
