"""Tests for Plotly generator."""

import pytest
from backend.visualizer.plotly_generator import PlotlyGenerator


def test_metric_card():
    """Test metric card generation."""
    generator = PlotlyGenerator()
    
    chart_config = {
        'type': 'metric',
        'title': 'Total Vehicles',
        'y_columns': ['count']
    }
    results = [{'count': 25}]
    columns = ['count']
    
    chart = generator.generate(chart_config, results, columns)
    
    assert chart['type'] == 'metric'
    assert chart['value'] == '25'
    assert chart['label'] == 'Total Vehicles'


def test_bar_chart():
    """Test bar chart generation."""
    generator = PlotlyGenerator()
    
    chart_config = {
        'type': 'bar',
        'title': 'Vehicles by Type',
        'category_column': 'vehicle_type',
        'value_column': 'count'
    }
    results = [
        {'vehicle_type': 'Van', 'count': 10},
        {'vehicle_type': 'Truck', 'count': 15}
    ]
    columns = ['vehicle_type', 'count']
    
    chart = generator.generate(chart_config, results, columns)
    
    assert 'data' in chart
    assert 'layout' in chart
    assert chart['data'][0]['type'] == 'bar'
    assert len(chart['data'][0]['x']) == 2


def test_line_chart():
    """Test line chart generation."""
    generator = PlotlyGenerator()
    
    chart_config = {
        'type': 'line',
        'title': 'Fuel Efficiency Over Time',
        'x_column': 'date',
        'y_columns': ['avg_mpg']
    }
    results = [
        {'date': '2024-01-01', 'avg_mpg': 25.5},
        {'date': '2024-01-02', 'avg_mpg': 26.2}
    ]
    columns = ['date', 'avg_mpg']
    
    chart = generator.generate(chart_config, results, columns)
    
    assert 'data' in chart
    assert chart['data'][0]['type'] == 'scatter'
    assert chart['data'][0]['mode'] == 'lines+markers'


def test_table():
    """Test table generation."""
    generator = PlotlyGenerator()
    
    chart_config = {'type': 'table', 'title': 'Vehicle Details'}
    results = [
        {'vehicle_id': 'V001', 'make': 'Ford', 'mileage': 45000},
        {'vehicle_id': 'V002', 'make': 'Chevy', 'mileage': 32000}
    ]
    columns = ['vehicle_id', 'make', 'mileage']
    
    chart = generator.generate(chart_config, results, columns)
    
    assert 'data' in chart
    assert chart['data'][0]['type'] == 'table'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
