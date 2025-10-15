"""Test the complete query pipeline with visualization."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_query_returns_plotly_chart():
    """Test that query endpoint returns Plotly chart."""
    response = client.post(
        "/api/query",
        json={"query": "How many vehicles do we have?"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data['success'] is True
    assert data['sql'] is not None
    assert data['chart_config'] is not None
    assert data['plotly_chart'] is not None
    
    # Check Plotly chart structure
    plotly_chart = data['plotly_chart']
    if data['chart_config']['type'] == 'metric':
        assert 'value' in plotly_chart
        assert 'label' in plotly_chart
    else:
        assert 'data' in plotly_chart
        assert 'layout' in plotly_chart


def test_visualize_endpoint():
    """Test standalone visualization endpoint."""
    response = client.post(
        "/api/visualize",
        json={
            "chart_config": {
                "type": "bar",
                "category_column": "type",
                "value_column": "count"
            },
            "results": [
                {"type": "Van", "count": 10},
                {"type": "Truck", "count": 15}
            ],
            "columns": ["type", "count"]
        }
    )
    print(f"test_visualize_endpoint response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    
    assert data['success'] is True
    assert data['chart'] is not None
    assert 'data' in data['chart']
    assert 'layout' in data['chart']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])