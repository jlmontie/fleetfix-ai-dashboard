"""Test the integrated SQL + Chart generation."""

import pytest
import os
from ai_agent.text_to_sql import TextToSQLAgent


@pytest.fixture
def schema_context():
    """Load schema context for testing."""
    schema_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..",
        "schema_context_full.txt"
    )
    with open(schema_path, 'r') as f:
        return f.read()


def test_single_metric_query(schema_context):
    """Test that single metric queries get metric card."""
    agent = TextToSQLAgent(schema_context)
    result = agent.generate_sql_and_chart("How many vehicles do we have?")
    print(f"Single metric query result: {result}")
    assert result['chart_config']['type'] == 'metric'
    assert result['sql'] is not None
    assert 'confidence' in result['chart_config']


def test_time_series_query(schema_context):
    """Test that time series queries get line chart."""
    agent = TextToSQLAgent(schema_context)
    result = agent.generate_sql_and_chart(
        "Show me average fuel efficiency over the last 30 days"
    )
    
    assert result['chart_config']['type'] == 'line'
    assert result['chart_config'].get('x_column') is not None
    assert len(result['chart_config'].get('y_columns', [])) > 0


def test_categorical_comparison(schema_context):
    """Test that categorical queries get bar chart."""
    agent = TextToSQLAgent(schema_context)
    result = agent.generate_sql_and_chart(
        "Compare total miles driven by vehicle type"
    )
    
    assert result['chart_config']['type'] in ['bar', 'grouped_bar']
    assert result['sql'] is not None


def test_geographic_query(schema_context):
    """Test that location queries get map."""
    agent = TextToSQLAgent(schema_context)
    result = agent.generate_sql_and_chart(
        "Show me current locations of all vehicles"
    )
    
    # Fast path should catch this
    assert result['chart_config']['type'] == 'map'
    assert result.get('fast_path') == True


def test_chart_has_title(schema_context):
    """Test that chart config includes title."""
    agent = TextToSQLAgent(schema_context)
    result = agent.generate_sql_and_chart(
        "What's the average driver score by driver?"
    )
    
    assert 'title' in result['chart_config']
    assert result['chart_config']['title'] != ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])