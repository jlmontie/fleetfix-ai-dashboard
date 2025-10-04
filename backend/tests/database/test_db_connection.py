"""
FleetFix Database Connection Test
Quick script to verify database setup and sample data
"""

import pytest
from database.config import db_config
from database.models import Driver, Vehicle, MaintenanceRecord, Telemetry, DriverPerformance, FaultCode
from datetime import date, timedelta
from sqlalchemy import func, text


@pytest.mark.database
def test_connection():
    """Test basic database connection"""
    with db_config.session_scope() as session:
        result = session.execute(text("SELECT version()")).fetchone()
        assert result is not None
        assert "PostgreSQL" in result[0]


@pytest.mark.database
def test_tables_exist():
    """Check if all tables exist"""
    tables = ['drivers', 'vehicles', 'maintenance_records', 'telemetry', 
              'driver_performance', 'fault_codes']
    
    with db_config.session_scope() as session:
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            assert count >= 0, f"Table {table} should exist and have non-negative count"


@pytest.mark.database
def test_data_quality():
    """Run some data quality checks"""
    with db_config.session_scope() as session:
        # Check 1: All vehicles have valid mileage
        invalid_mileage = session.query(Vehicle).filter(Vehicle.current_mileage < 0).count()
        assert invalid_mileage == 0, "Found vehicles with negative mileage"
        
        # Check 2: All maintenance records have valid costs
        invalid_costs = session.query(MaintenanceRecord).filter(MaintenanceRecord.cost < 0).count()
        assert invalid_costs == 0, "Found maintenance records with negative costs"
        
        # Check 3: All driver scores are between 0-100
        invalid_scores = session.query(DriverPerformance).filter(
            (DriverPerformance.score < 0) | (DriverPerformance.score > 100)
        ).count()
        assert invalid_scores == 0, "Found driver scores outside 0-100 range"
        
        # Check 4: All telemetry has realistic speed values
        invalid_speed = session.query(Telemetry).filter(
            (Telemetry.speed < 0) | (Telemetry.speed > 120)
        ).count()
        assert invalid_speed == 0, "Found telemetry with unrealistic speed"


def show_sample_data():
    """Display sample data for verification"""
    print("\n" + "=" * 70)
    print("SAMPLE DATA PREVIEW")
    print("=" * 70)
    
    try:
        with db_config.session_scope() as session:
            # Sample vehicles
            print("\nSample Vehicles:")
            vehicles = session.query(Vehicle).limit(5).all()
            for v in vehicles:
                print(f"  • {v.year} {v.make} {v.model} ({v.license_plate})")
                print(f"    Status: {v.status}, Mileage: {v.current_mileage:,} miles")
                print(f"    Next service: {v.next_service_due}")
            
            # Overdue maintenance
            print("\nVehicles with Overdue Maintenance:")
            overdue = session.query(Vehicle).filter(
                Vehicle.next_service_due < date.today()
            ).limit(5).all()
            if overdue:
                for v in overdue:
                    days_overdue = (date.today() - v.next_service_due).days
                    print(f"  • {v.license_plate}: {days_overdue} days overdue")
            else:
                print("  No vehicles overdue for maintenance")
            
            # Active fault codes
            print("\nActive Fault Codes:")
            faults = session.query(FaultCode, Vehicle).join(
                Vehicle, FaultCode.vehicle_id == Vehicle.id
            ).filter(
                FaultCode.resolved == False
            ).limit(5).all()
            if faults:
                for fault, vehicle in faults:
                    print(f"  • {vehicle.license_plate}: {fault.code} ({fault.severity})")
                    print(f"    {fault.description}")
            else:
                print("  No active fault codes")
            
            # Driver performance
            print("\nRecent Driver Performance (Last 7 Days):")
            recent_date = date.today() - timedelta(days=7)
            performance = session.query(
                Driver.name,
                func.avg(DriverPerformance.score).label('avg_score'),
                func.sum(DriverPerformance.harsh_braking_events).label('harsh_braking'),
                func.sum(DriverPerformance.miles_driven).label('miles')
            ).join(
                DriverPerformance, Driver.id == DriverPerformance.driver_id
            ).filter(
                DriverPerformance.date >= recent_date
            ).group_by(
                Driver.name
            ).order_by(
                func.avg(DriverPerformance.score).desc()
            ).limit(5).all()
            
            for name, avg_score, harsh_braking, miles in performance:
                print(f"  • {name}: Score {int(avg_score)}, "
                      f"Harsh braking: {harsh_braking}, Miles: {int(miles)}")
            
            # Fleet statistics
            print("\nFleet Statistics:")
            total_vehicles = session.query(Vehicle).count()
            active_vehicles = session.query(Vehicle).filter(Vehicle.status == 'active').count()
            total_mileage = session.query(func.sum(Vehicle.current_mileage)).scalar()
            avg_mileage = session.query(func.avg(Vehicle.current_mileage)).scalar()
            
            print(f"  Total vehicles: {total_vehicles}")
            print(f"  Active vehicles: {active_vehicles}")
            print(f"  Total fleet mileage: {int(total_mileage):,} miles")
            print(f"  Average vehicle mileage: {int(avg_mileage):,} miles")
            
            # Maintenance costs
            print("\nMaintenance Cost Analysis:")
            total_maintenance_cost = session.query(func.sum(MaintenanceRecord.cost)).scalar()
            avg_maintenance_cost = session.query(func.avg(MaintenanceRecord.cost)).scalar()
            
            print(f"  Total maintenance costs: ${float(total_maintenance_cost):,.2f}")
            print(f"  Average service cost: ${float(avg_maintenance_cost):,.2f}")
            
            # Recent telemetry
            print("\nRecent Telemetry Sample:")
            recent_telemetry = session.query(Telemetry, Vehicle).join(
                Vehicle, Telemetry.vehicle_id == Vehicle.id
            ).order_by(
                Telemetry.timestamp.desc()
            ).limit(3).all()
            
            for telem, vehicle in recent_telemetry:
                print(f"  • {vehicle.license_plate} @ {telem.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print(f"    Speed: {float(telem.speed):.1f} mph, "
                      f"Fuel: {float(telem.fuel_level):.1f}%, "
                      f"Temp: {float(telem.engine_temp):.1f}°F")
            
            return True
            
    except Exception as e:
        print(f"✗ Error displaying sample data: {e}")
        return False


def show_useful_queries():
    """Show some useful queries for testing"""
    print("\n" + "=" * 70)
    print("USEFUL TEST QUERIES")
    print("=" * 70)
    
    queries = [
        ("Vehicles needing maintenance soon (next 7 days)",
         "SELECT make, model, license_plate, next_service_due "
         "FROM vehicles "
         "WHERE next_service_due BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days' "
         "ORDER BY next_service_due;"),
        
        ("Top 5 drivers by average score (last 30 days)",
         "SELECT d.name, AVG(dp.score) as avg_score, COUNT(*) as days_driven "
         "FROM drivers d "
         "JOIN driver_performance dp ON d.id = dp.driver_id "
         "WHERE dp.date >= CURRENT_DATE - INTERVAL '30 days' "
         "GROUP BY d.name "
         "ORDER BY avg_score DESC "
         "LIMIT 5;"),
        
        ("Fleet fuel efficiency trend (last 7 days)",
         "SELECT DATE(timestamp) as date, AVG(fuel_level) as avg_fuel "
         "FROM telemetry "
         "WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days' "
         "GROUP BY DATE(timestamp) "
         "ORDER BY date;"),
        
        ("Vehicles with critical unresolved fault codes",
         "SELECT v.license_plate, fc.code, fc.description, fc.timestamp "
         "FROM vehicles v "
         "JOIN fault_codes fc ON v.id = fc.vehicle_id "
         "WHERE fc.resolved = FALSE AND fc.severity = 'critical' "
         "ORDER BY fc.timestamp DESC;"),
        
        ("Maintenance cost by vehicle type (last 6 months)",
         "SELECT v.vehicle_type, COUNT(*) as service_count, SUM(mr.cost) as total_cost "
         "FROM vehicles v "
         "JOIN maintenance_records mr ON v.id = mr.vehicle_id "
         "WHERE mr.service_date >= CURRENT_DATE - INTERVAL '6 months' "
         "GROUP BY v.vehicle_type "
         "ORDER BY total_cost DESC;"),
    ]
    
    for title, query in queries:
        print(f"\n{title}:")
        print("```sql")
        print(query)
        print("```")


def main():
    """Run all tests"""
    print("=" * 70)
    print("FLEETFIX DATABASE TEST SUITE")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 4
    
    # Run tests
    if test_connection():
        tests_passed += 1
    
    if test_tables_exist():
        tests_passed += 1
    
    if test_data_quality():
        tests_passed += 1
    
    if show_sample_data():
        tests_passed += 1
    
    # Show useful queries
    show_useful_queries()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✓ All tests passed! Your database is ready.")
        print("\nNext steps:")
        print("  1. Review the sample queries above")
        print("  2. Test queries in psql or pgAdmin")
        print("  3. Move to Phase 2: Building the AI agent")
    else:
        print(f"\n✗ {tests_total - tests_passed} test(s) failed. Please review errors above.")
        print("\nTroubleshooting:")
        print("  1. Check DATABASE_URL in .env file")
        print("  2. Verify PostgreSQL is running")
        print("  3. Re-run: python database/seed_data.py")
    
    print("=" * 70)


if __name__ == "__main__":
    main()