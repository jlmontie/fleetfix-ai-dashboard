"""
Basic Database Tests for FleetFix AI Dashboard
Tests database connection, table existence, and data quality
"""

import pytest
from database.config import db_config
from database.models import Driver, Vehicle, MaintenanceRecord, Telemetry, DriverPerformance, FaultCode
from sqlalchemy import func, text


@pytest.mark.database
def test_database_connection():
    """Test basic database connection"""
    with db_config.session_scope() as session:
        result = session.execute(text("SELECT version()")).fetchone()
        assert result is not None
        assert "PostgreSQL" in result[0]


@pytest.mark.database
def test_tables_exist():
    """Check if all required tables exist"""
    tables = ['drivers', 'vehicles', 'maintenance_records', 'telemetry', 
              'driver_performance', 'fault_codes']
    
    with db_config.session_scope() as session:
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            assert count >= 0, f"Table {table} should exist and have non-negative count"


@pytest.mark.database
def test_data_quality_vehicles():
    """Test vehicle data quality"""
    with db_config.session_scope() as session:
        # All vehicles should have valid mileage
        invalid_mileage = session.query(Vehicle).filter(Vehicle.current_mileage < 0).count()
        assert invalid_mileage == 0, "Found vehicles with negative mileage"
        
        # All vehicles should have valid status
        invalid_status = session.query(Vehicle).filter(
            ~Vehicle.status.in_(['active', 'inactive', 'maintenance'])
        ).count()
        assert invalid_status == 0, "Found vehicles with invalid status"


@pytest.mark.database
def test_data_quality_maintenance():
    """Test maintenance record data quality"""
    with db_config.session_scope() as session:
        # All maintenance records should have valid costs
        invalid_costs = session.query(MaintenanceRecord).filter(MaintenanceRecord.cost < 0).count()
        assert invalid_costs == 0, "Found maintenance records with negative costs"


@pytest.mark.database
def test_data_quality_driver_performance():
    """Test driver performance data quality"""
    with db_config.session_scope() as session:
        # All driver scores should be between 0-100
        invalid_scores = session.query(DriverPerformance).filter(
            (DriverPerformance.score < 0) | (DriverPerformance.score > 100)
        ).count()
        assert invalid_scores == 0, "Found driver scores outside 0-100 range"


@pytest.mark.database
def test_data_quality_telemetry():
    """Test telemetry data quality"""
    with db_config.session_scope() as session:
        # All telemetry should have realistic speed values
        invalid_speed = session.query(Telemetry).filter(
            (Telemetry.speed < 0) | (Telemetry.speed > 120)
        ).count()
        assert invalid_speed == 0, "Found telemetry with unrealistic speed"
        
        # All telemetry should have valid fuel levels
        invalid_fuel = session.query(Telemetry).filter(
            (Telemetry.fuel_level < 0) | (Telemetry.fuel_level > 100)
        ).count()
        assert invalid_fuel == 0, "Found telemetry with invalid fuel levels"


@pytest.mark.database
def test_sample_data_exists():
    """Test that sample data exists in all tables"""
    with db_config.session_scope() as session:
        # Check that we have some data in each table
        driver_count = session.query(Driver).count()
        vehicle_count = session.query(Vehicle).count()
        maintenance_count = session.query(MaintenanceRecord).count()
        telemetry_count = session.query(Telemetry).count()
        performance_count = session.query(DriverPerformance).count()
        fault_count = session.query(FaultCode).count()
        
        assert driver_count > 0, "No drivers found in database"
        assert vehicle_count > 0, "No vehicles found in database"
        assert maintenance_count > 0, "No maintenance records found in database"
        assert telemetry_count > 0, "No telemetry data found in database"
        assert performance_count > 0, "No driver performance data found in database"
        assert fault_count >= 0, "Fault codes table should exist"
