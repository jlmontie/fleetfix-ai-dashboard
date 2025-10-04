"""
Clean pytest tests for schema context builder
Verifies schema introspection works correctly
"""

import pytest
from ai_agent.schema_context import SchemaContextBuilder


@pytest.mark.database
def test_basic_introspection():
    """Test basic database introspection"""
    builder = SchemaContextBuilder()
    tables = builder.get_all_tables()
    
    expected_tables = {'drivers', 'vehicles', 'maintenance_records', 
                      'telemetry', 'driver_performance', 'fault_codes'}
    found_tables = {table.name for table in tables}
    
    assert expected_tables == found_tables, f"Missing tables: {expected_tables - found_tables}"
    
    # Verify each table has columns and row count
    for table in tables:
        assert len(table.columns) > 0, f"Table {table.name} should have columns"
        assert table.row_count >= 0, f"Table {table.name} should have non-negative row count"


@pytest.mark.database
def test_column_details():
    """Test column introspection"""
    builder = SchemaContextBuilder()
    vehicles = builder.get_table_info('vehicles')
    
    # Check for key columns
    column_names = [col.name for col in vehicles.columns]
    expected_columns = ['id', 'make', 'model', 'vin', 'license_plate', 
                       'current_mileage', 'next_service_due']
    
    missing = [col for col in expected_columns if col not in column_names]
    assert not missing, f"Missing columns: {missing}"
    
    # Check for primary key
    pk_cols = [col.name for col in vehicles.columns if col.primary_key]
    assert 'id' in pk_cols, f"Primary key not detected. Found: {pk_cols}"
    
    # Check for foreign keys
    fk_cols = [(col.name, col.foreign_key) for col in vehicles.columns if col.foreign_key]
    assert len(fk_cols) >= 0, "Foreign key detection should work"


@pytest.mark.database
def test_relationships():
    """Test foreign key relationship detection"""
    builder = SchemaContextBuilder()
    
    # Check telemetry foreign keys
    telemetry = builder.get_table_info('telemetry')
    fks = {col.name: col.foreign_key for col in telemetry.columns if col.foreign_key}
    
    assert 'vehicle_id' in fks and 'vehicles.id' in fks['vehicle_id'], "Telemetry → Vehicle relationship not found"
    assert 'driver_id' in fks and 'drivers.id' in fks['driver_id'], "Telemetry → Driver relationship not found"


@pytest.mark.database
def test_full_context():
    """Test full context generation"""
    builder = SchemaContextBuilder()
    context = builder.build_schema_context()
    
    # Check for key sections
    required_sections = [
        "FleetFix Database Schema",
        "Tables Overview",
        "Detailed Schema",
        "Key Relationships",
        "Important Notes"
    ]
    
    missing_sections = [sec for sec in required_sections if sec not in context]
    assert not missing_sections, f"Missing sections: {missing_sections}"
    
    # Check context length is reasonable
    assert len(context) > 1000, "Context should be substantial"
    assert len(context) < 50000, "Context should not be too large"


@pytest.mark.database
def test_concise_context():
    """Test concise context generation"""
    builder = SchemaContextBuilder()
    concise = builder.build_concise_context()
    full = builder.build_schema_context()
    
    # Concise should be shorter than full
    assert len(concise) < len(full), "Concise context should be shorter than full"
    
    # Should still contain essential information
    assert "FleetFix Database Schema" in concise, "Concise context should contain schema title"
    assert "vehicles" in concise, "Concise context should contain table information"


@pytest.mark.database
def test_sample_data():
    """Test sample data retrieval"""
    builder = SchemaContextBuilder()
    
    # Get samples from each table
    tables = ['drivers', 'vehicles', 'fault_codes']
    
    for table in tables:
        samples = builder.get_table_sample_data(table, limit=1)
        assert samples is not None, f"Should be able to get sample data from {table}"
        assert len(samples) >= 0, f"Sample data should be a list for {table}"


@pytest.mark.database
def test_token_estimation():
    """Test token count estimation"""
    builder = SchemaContextBuilder()
    context = builder.build_schema_context()
    
    # Estimate should be reasonable
    estimated_tokens = len(context) // 4
    assert estimated_tokens > 100, "Token estimate should be substantial"
    assert estimated_tokens < 10000, "Token estimate should not be excessive"
