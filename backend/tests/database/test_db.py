"""
Database connection and data quality tests
"""

import pytest
from sqlalchemy import func, text
from datetime import date, timedelta

from backend.database.config import db_config
from backend.database.models import (
    Driver, Vehicle, MaintenanceRecord, 
    Telemetry, DriverPerformance, FaultCode
)


class TestDatabaseConnection:
    """Test database connectivity"""
    
    def test_connection(self):
        """Test basic database connection"""
        with db_config.session_scope() as session:
            result = session.execute(text("SELECT version()")).fetchone()
            assert result is not None
            assert "PostgreSQL" in result[0]
    
    def test_all_tables_exist(self):
        """Check if all required tables exist and have data"""
        tables = [
            'drivers', 'vehicles', 'maintenance_records', 
            'telemetry', 'driver_performance', 'fault_codes'
        ]
        
        with db_config.session_scope() as session:
            for table in tables:
                count = session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).fetchone()[0]
                assert count > 0, f"Table {table} is empty"


class TestDataQuality:
    """Test data integrity and quality"""
    
    def test_vehicles_have_valid_mileage(self):
        """Verify all vehicles have non-negative mileage"""
        with db_config.session_scope() as session:
            invalid_count = session.query(Vehicle).filter(
                Vehicle.current_mileage < 0
            ).count()
            assert invalid_count == 0, "Found vehicles with negative mileage"
    
    def test_maintenance_records_have_valid_costs(self):
        """Verify all maintenance costs are non-negative"""
        with db_config.session_scope() as session:
            invalid_count = session.query(MaintenanceRecord).filter(
                MaintenanceRecord.cost < 0
            ).count()
            assert invalid_count == 0, "Found negative maintenance costs"
    
    def test_driver_scores_are_valid(self):
        """Verify all driver scores are between 0-100"""
        with db_config.session_scope() as session:
            invalid_count = session.query(DriverPerformance).filter(
                (DriverPerformance.score < 0) | (DriverPerformance.score > 100)
            ).count()
            assert invalid_count == 0, "Found invalid driver scores"
    
    def test_telemetry_speed_is_realistic(self):
        """Verify telemetry speed values are realistic"""
        with db_config.session_scope() as session:
            invalid_count = session.query(Telemetry).filter(
                (Telemetry.speed < 0) | (Telemetry.speed > 120)
            ).count()
            assert invalid_count == 0, "Found unrealistic speed values"


class TestDataRelationships:
    """Test foreign key relationships"""
    
    def test_telemetry_has_valid_vehicle_references(self):
        """Verify all telemetry records reference valid vehicles"""
        with db_config.session_scope() as session:
            orphaned = session.query(Telemetry).outerjoin(
                Vehicle, Telemetry.vehicle_id == Vehicle.id
            ).filter(Vehicle.id.is_(None)).count()
            assert orphaned == 0, "Found telemetry with invalid vehicle_id"
    
    def test_maintenance_records_have_valid_vehicle_references(self):
        """Verify all maintenance records reference valid vehicles"""
        with db_config.session_scope() as session:
            orphaned = session.query(MaintenanceRecord).outerjoin(
                Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id
            ).filter(Vehicle.id.is_(None)).count()
            assert orphaned == 0, "Found maintenance records with invalid vehicle_id"
    
    def test_driver_performance_has_valid_driver_references(self):
        """Verify all performance records reference valid drivers"""
        with db_config.session_scope() as session:
            orphaned = session.query(DriverPerformance).outerjoin(
                Driver, DriverPerformance.driver_id == Driver.id
            ).filter(Driver.id.is_(None)).count()
            assert orphaned == 0, "Found performance records with invalid driver_id"


class TestFleetStatistics:
    """Test fleet-level statistics and aggregations"""
    
    def test_fleet_has_vehicles(self):
        """Verify fleet has vehicles"""
        with db_config.session_scope() as session:
            total = session.query(Vehicle).count()
            assert total > 0, "No vehicles in fleet"
    
    def test_fleet_has_active_vehicles(self):
        """Verify fleet has active vehicles"""
        with db_config.session_scope() as session:
            active = session.query(Vehicle).filter(
                Vehicle.status == 'active'
            ).count()
            assert active > 0, "No active vehicles"
    
    def test_fleet_mileage_is_reasonable(self):
        """Verify fleet mileage statistics are reasonable"""
        with db_config.session_scope() as session:
            total_mileage = session.query(
                func.sum(Vehicle.current_mileage)
            ).scalar()
            avg_mileage = session.query(
                func.avg(Vehicle.current_mileage)
            ).scalar()
            
            assert total_mileage > 0, "Total fleet mileage is zero"
            assert avg_mileage > 0, "Average vehicle mileage is zero"
            assert avg_mileage < 500000, "Average mileage unrealistically high"
