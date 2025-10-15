"""
Schema context builder tests
"""

import pytest
from backend.ai_agent.schema_context import SchemaContextBuilder


@pytest.fixture(scope="module")
def builder():
    """Create a schema context builder instance"""
    return SchemaContextBuilder()


class TestBasicIntrospection:
    """Test database introspection capabilities"""
    
    def test_get_all_tables(self, builder):
        """Verify all expected tables are found"""
        tables = builder.get_all_tables()
        
        expected_tables = {
            'drivers', 'vehicles', 'maintenance_records',
            'telemetry', 'driver_performance', 'fault_codes'
        }
        found_tables = {table.name for table in tables}
        
        assert expected_tables == found_tables, \
            f"Missing tables: {expected_tables - found_tables}"
    
    def test_tables_have_row_counts(self, builder):
        """Verify all tables have row counts"""
        tables = builder.get_all_tables()
        
        for table in tables:
            assert hasattr(table, 'row_count')
            assert table.row_count >= 0
    
    def test_tables_have_columns(self, builder):
        """Verify all tables have column information"""
        tables = builder.get_all_tables()
        
        for table in tables:
            assert hasattr(table, 'columns')
            assert len(table.columns) > 0


class TestColumnDetails:
    """Test column introspection"""
    
    def test_vehicles_table_structure(self, builder):
        """Verify vehicles table has expected columns"""
        vehicles = builder.get_table_info('vehicles')
        column_names = [col.name for col in vehicles.columns]
        
        expected_columns = [
            'id', 'make', 'model', 'vin', 'license_plate',
            'current_mileage', 'next_service_due'
        ]
        
        for col in expected_columns:
            assert col in column_names, f"Missing column: {col}"
    
    def test_primary_key_detection(self, builder):
        """Verify primary keys are detected"""
        vehicles = builder.get_table_info('vehicles')
        pk_cols = [col.name for col in vehicles.columns if col.primary_key]
        
        assert 'id' in pk_cols, "Primary key 'id' not detected"
    
    def test_column_types_detected(self, builder):
        """Verify column types are captured"""
        vehicles = builder.get_table_info('vehicles')
        
        for col in vehicles.columns:
            assert hasattr(col, 'type')
            assert col.type is not None


class TestRelationships:
    """Test foreign key relationship detection"""
    
    def test_telemetry_foreign_keys(self, builder):
        """Verify telemetry foreign keys are detected"""
        telemetry = builder.get_table_info('telemetry')
        fks = {col.name: col.foreign_key 
               for col in telemetry.columns if col.foreign_key}
        
        assert 'vehicle_id' in fks, "vehicle_id foreign key not found"
        assert 'vehicles.id' in fks['vehicle_id'], \
            "vehicle_id doesn't reference vehicles.id"
        
        assert 'driver_id' in fks, "driver_id foreign key not found"
        assert 'drivers.id' in fks['driver_id'], \
            "driver_id doesn't reference drivers.id"
    
    def test_maintenance_foreign_keys(self, builder):
        """Verify maintenance_records foreign keys are detected"""
        maintenance = builder.get_table_info('maintenance_records')
        fks = {col.name: col.foreign_key 
               for col in maintenance.columns if col.foreign_key}
        
        assert 'vehicle_id' in fks, "vehicle_id foreign key not found"


class TestContextGeneration:
    """Test schema context generation"""
    
    def test_full_context_generation(self, builder):
        """Verify full context is generated with all sections"""
        context = builder.build_schema_context()
        
        required_sections = [
            "FleetFix Database Schema",
            "Tables Overview",
            "Detailed Schema",
            "Key Relationships",
            "Important Notes"
        ]
        
        for section in required_sections:
            assert section in context, f"Missing section: {section}"
    
    def test_context_is_substantial(self, builder):
        """Verify context has substantial content"""
        context = builder.build_schema_context()
        
        # Should be at least 1000 characters
        assert len(context) > 1000, "Context is too short"
        
        # Should contain all table names
        for table in ['drivers', 'vehicles', 'telemetry']:
            assert table in context.lower(), f"Table {table} not in context"
    
    def test_concise_context_is_shorter(self, builder):
        """Verify concise context is actually more concise"""
        full = builder.build_schema_context()
        concise = builder.build_concise_context()
        
        assert len(concise) < len(full), \
            "Concise context is not shorter than full context"
        
        # But should still have key information
        assert 'vehicles' in concise.lower()
        assert 'drivers' in concise.lower()


class TestSampleData:
    """Test sample data retrieval"""
    
    def test_get_sample_data_drivers(self, builder):
        """Verify can retrieve sample driver data"""
        samples = builder.get_table_sample_data('drivers', limit=1)
        
        assert len(samples) > 0, "No sample data returned"
        assert 'error' not in samples[0], "Error in sample data"
        assert 'id' in samples[0], "Missing id field"
    
    def test_get_sample_data_vehicles(self, builder):
        """Verify can retrieve sample vehicle data"""
        samples = builder.get_table_sample_data('vehicles', limit=1)
        
        assert len(samples) > 0, "No sample data returned"
        assert 'error' not in samples[0], "Error in sample data"
        assert 'license_plate' in samples[0], "Missing license_plate field"
    
    def test_sample_data_limit_works(self, builder):
        """Verify limit parameter works"""
        samples = builder.get_table_sample_data('vehicles', limit=3)
        
        assert len(samples) <= 3, "Returned more samples than limit"


class TestTokenEstimation:
    """Test token usage estimation"""
    
    def test_full_context_token_estimate(self, builder):
        """Verify token estimation for full context"""
        context = builder.build_schema_context()
        
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = len(context) // 4
        
        # Should be reasonable for LLM context window
        assert estimated_tokens < 10000, \
            "Context too large for typical LLM usage"
    
    def test_concise_context_saves_tokens(self, builder):
        """Verify concise context uses fewer tokens"""
        full = builder.build_schema_context()
        concise = builder.build_concise_context()
        
        full_tokens = len(full) // 4
        concise_tokens = len(concise) // 4
        
        # Should save at least 20% tokens
        savings = (full_tokens - concise_tokens) / full_tokens
        assert savings > 0.2, \
            f"Concise context only saves {savings:.1%} tokens"
