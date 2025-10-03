"""
FleetFix Recent Event Injector
Injects interesting events from the last 24-72 hours
Ensures the AI dashboard always has compelling insights to highlight
"""

import random
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Driver, Vehicle, MaintenanceRecord, Telemetry, DriverPerformance, FaultCode
from dotenv import load_dotenv

load_dotenv()


def inject_recent_events(session):
    """
    Inject compelling events from the last 24-72 hours
    These ensure the AI agent always has something interesting to highlight
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    three_days_ago = today - timedelta(days=3)
    
    print("\nInjecting recent interesting events...")
    
    # Get some vehicles and drivers to work with
    vehicles = session.query(Vehicle).filter(Vehicle.status == 'active').limit(10).all()
    drivers = session.query(Driver).filter(Driver.status == 'active').limit(10).all()
    
    if not vehicles or not drivers:
        print("No active vehicles or drivers found. Run seed_data.py first.")
        return
    
    events_added = 0
    
    # ====================================================================
    # EVENT 1: Critical fault code appeared yesterday
    # ====================================================================
    print("\n  Event 1: New critical fault code (yesterday)")
    vehicle1 = random.choice(vehicles)
    
    critical_faults = [
        ('P0301', 'Cylinder 1 Misfire Detected'),
        ('P0306', 'Cylinder 6 Misfire Detected'),
        ('U0100', 'Lost Communication With ECM/PCM'),
        ('P0017', 'Crankshaft Position - Camshaft Position Correlation Issue'),
    ]
    
    fault_code, fault_desc = random.choice(critical_faults)
    
    fault = FaultCode(
        vehicle_id=vehicle1.id,
        timestamp=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=random.randint(8, 16)),
        code=fault_code,
        description=fault_desc,
        severity='critical',
        resolved=False
    )
    session.add(fault)
    events_added += 1
    print(f"     → Vehicle {vehicle1.license_plate}: {fault_code} detected yesterday")
    
    # ====================================================================
    # EVENT 2: Driver performance suddenly dropped (last 3 days)
    # ====================================================================
    print("\n  Event 2: Driver performance drop (last 3 days)")
    driver1 = random.choice(drivers)
    vehicle2 = random.choice(vehicles)
    
    # Get driver's typical score
    avg_score = session.query(func.avg(DriverPerformance.score)).filter(
        DriverPerformance.driver_id == driver1.id,
        DriverPerformance.date < three_days_ago
    ).scalar()
    
    typical_score = int(avg_score) if avg_score else 80
    
    # Add three days of poor performance
    for days_back in [3, 2, 1]:
        perf_date = today - timedelta(days=days_back)
        
        # Much worse performance than usual
        poor_score = random.randint(40, 55)
        harsh_braking = random.randint(12, 20)
        rapid_accel = random.randint(10, 18)
        speeding = random.randint(5, 10)
        
        perf = DriverPerformance(
            driver_id=driver1.id,
            vehicle_id=vehicle2.id,
            date=perf_date,
            harsh_braking_events=harsh_braking,
            rapid_acceleration_events=rapid_accel,
            speeding_events=speeding,
            idle_time_minutes=random.randint(60, 120),
            hours_driven=Decimal(str(round(random.uniform(7, 9), 2))),
            miles_driven=Decimal(str(round(random.uniform(150, 200), 2))),
            score=poor_score
        )
        session.add(perf)
        events_added += 1
    
    print(f"     → Driver {driver1.name}: Score dropped from ~{typical_score} to ~45")
    
    # ====================================================================
    # EVENT 3: Vehicle just went overdue for maintenance (today or yesterday)
    # ====================================================================
    print("\n  Event 3: Vehicle overdue for maintenance")
    vehicle3 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle2.id]])
    
    # Make it overdue by 3-10 days
    days_overdue = random.randint(3, 10)
    vehicle3.next_service_due = today - timedelta(days=days_overdue)
    events_added += 1
    print(f"     → Vehicle {vehicle3.license_plate}: {days_overdue} days overdue")
    
    # ====================================================================
    # EVENT 4: Unusual fuel consumption spike (yesterday)
    # ====================================================================
    print("\n  Event 4: Unusual fuel consumption pattern (yesterday)")
    vehicle4 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle2.id, vehicle3.id]])
    driver2 = random.choice([d for d in drivers if d.id != driver1.id])
    
    # Add telemetry for yesterday showing rapid fuel decrease
    yesterday_start = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=6)
    
    for i in range(24):  # Hourly readings for yesterday
        timestamp = yesterday_start + timedelta(hours=i)
        
        # Fuel drops much faster than normal (simulating leak or excessive idling)
        fuel_level = max(5, 100 - (i * 5) - random.uniform(0, 3))
        
        telem = Telemetry(
            vehicle_id=vehicle4.id,
            driver_id=driver2.id,
            timestamp=timestamp,
            gps_lat=Decimal('39.0997'),
            gps_lon=Decimal('-94.5786'),
            speed=Decimal(str(round(random.uniform(20, 50), 2))),
            fuel_level=Decimal(str(round(fuel_level, 2))),
            engine_temp=Decimal(str(round(random.uniform(180, 210), 2))),
            odometer=vehicle4.current_mileage + i
        )
        session.add(telem)
        events_added += 1
    
    print(f"     → Vehicle {vehicle4.license_plate}: Abnormal fuel consumption yesterday")
    
    # ====================================================================
    # EVENT 5: Multiple speeding events from one driver (today)
    # ====================================================================
    print("\n  Event 5: Driver speeding incidents (today)")
    driver3 = random.choice([d for d in drivers if d.id not in [driver1.id, driver2.id]])
    vehicle5 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle2.id, vehicle3.id, vehicle4.id]])
    
    # Add today's performance record with many speeding events
    perf_today = DriverPerformance(
        driver_id=driver3.id,
        vehicle_id=vehicle5.id,
        date=today,
        harsh_braking_events=random.randint(3, 6),
        rapid_acceleration_events=random.randint(4, 8),
        speeding_events=12,  # Very high!
        idle_time_minutes=random.randint(20, 45),
        hours_driven=Decimal(str(round(random.uniform(6, 8), 2))),
        miles_driven=Decimal(str(round(random.uniform(140, 180), 2))),
        score=55  # Low score due to speeding
    )
    session.add(perf_today)
    events_added += 1
    print(f"     → Driver {driver3.name}: 12 speeding incidents today")
    
    # ====================================================================
    # EVENT 6: Second vehicle overdue (different severity)
    # ====================================================================
    print("\n  Event 6: Another vehicle approaching critical maintenance")
    vehicle6 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle2.id, vehicle3.id, vehicle4.id, vehicle5.id]])
    
    # Due within next 2 days (urgency)
    vehicle6.next_service_due = today + timedelta(days=random.randint(1, 2))
    events_added += 1
    print(f"     → Vehicle {vehicle6.license_plate}: Maintenance due in 1-2 days")
    
    # ====================================================================
    # EVENT 7: Warning-level fault code (yesterday evening)
    # ====================================================================
    print("\n  Event 7: Warning fault code detected")
    vehicle7 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle3.id]])
    
    warning_faults = [
        ('P0420', 'Catalyst System Efficiency Below Threshold'),
        ('P0300', 'Random/Multiple Cylinder Misfire Detected'),
        ('C1234', 'ABS Wheel Speed Sensor Front Right Circuit Failure'),
    ]
    
    fault_code, fault_desc = random.choice(warning_faults)
    
    fault = FaultCode(
        vehicle_id=vehicle7.id,
        timestamp=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=17, minutes=random.randint(0, 59)),
        code=fault_code,
        description=fault_desc,
        severity='warning',
        resolved=False
    )
    session.add(fault)
    events_added += 1
    print(f"     → Vehicle {vehicle7.license_plate}: {fault_code} (warning)")
    
    # ====================================================================
    # EVENT 8: Fleet-wide fuel efficiency drop (last 3 days)
    # ====================================================================
    print("\n  Event 8: Fleet fuel efficiency declining")
    
    # Add telemetry for multiple vehicles showing lower fuel efficiency
    for vehicle in vehicles[:5]:  # 5 vehicles showing the trend
        for days_back in [3, 2, 1]:
            event_date = today - timedelta(days=days_back)
            event_start = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=6)
            
            for hour in range(0, 12, 2):  # Every 2 hours
                timestamp = event_start + timedelta(hours=hour)
                
                # Slightly higher fuel consumption than normal
                base_fuel = 100 - (hour * 7)
                fuel_level = max(20, base_fuel - random.uniform(5, 10))
                
                telem = Telemetry(
                    vehicle_id=vehicle.id,
                    driver_id=random.choice(drivers).id,
                    timestamp=timestamp,
                    gps_lat=Decimal(str(round(39.0997 + random.uniform(-0.1, 0.1), 8))),
                    gps_lon=Decimal(str(round(-94.5786 + random.uniform(-0.1, 0.1), 8))),
                    speed=Decimal(str(round(random.uniform(30, 55), 2))),
                    fuel_level=Decimal(str(round(fuel_level, 2))),
                    engine_temp=Decimal(str(round(random.uniform(185, 215), 2))),
                    odometer=vehicle.current_mileage + (days_back * 50) + (hour * 5)
                )
                session.add(telem)
                events_added += 1
    
    print(f"     → Fleet-wide: 5 vehicles showing decreased fuel efficiency")
    
    # ====================================================================
    # EVENT 9: Excellent driver performance streak (positive event)
    # ====================================================================
    print("\n  Event 9: Driver with excellent performance (positive)")
    driver4 = random.choice([d for d in drivers if d.id not in [driver1.id, driver3.id]])
    vehicle8 = random.choice(vehicles)
    
    # Add 5 days of excellent performance
    for days_back in range(5, 0, -1):
        perf_date = today - timedelta(days=days_back)
        
        excellent_perf = DriverPerformance(
            driver_id=driver4.id,
            vehicle_id=vehicle8.id,
            date=perf_date,
            harsh_braking_events=random.randint(0, 1),
            rapid_acceleration_events=random.randint(0, 2),
            speeding_events=0,
            idle_time_minutes=random.randint(10, 25),
            hours_driven=Decimal(str(round(random.uniform(7, 9), 2))),
            miles_driven=Decimal(str(round(random.uniform(160, 200), 2))),
            score=random.randint(95, 100)
        )
        session.add(excellent_perf)
        events_added += 1
    
    print(f"     → Driver {driver4.name}: 5-day streak of 95+ scores")
    
    # ====================================================================
    # EVENT 10: Vehicle returned to service (from maintenance)
    # ====================================================================
    print("\n  Event 10: Vehicle completed maintenance")
    
    # Find a vehicle that was in maintenance or create the scenario
    maintenance_vehicles = session.query(Vehicle).filter(Vehicle.status == 'maintenance').first()
    if maintenance_vehicles:
        vehicle9 = maintenance_vehicles
    else:
        vehicle9 = random.choice([v for v in vehicles if v.id not in [vehicle1.id, vehicle3.id, vehicle6.id]])
        vehicle9.status = 'maintenance'
    
    # Add maintenance record from yesterday
    maintenance = MaintenanceRecord(
        vehicle_id=vehicle9.id,
        service_date=yesterday,
        service_type='general_maintenance',
        description='Scheduled maintenance completed - vehicle returned to service',
        cost=Decimal('285.50'),
        mileage_at_service=vehicle9.current_mileage - random.randint(50, 150),
        next_service_mileage=vehicle9.current_mileage + 5000,
        performed_by='FleetFix Service Center'
    )
    session.add(maintenance)
    
    # Update vehicle status back to active
    vehicle9.status = 'active'
    vehicle9.last_service_date = yesterday
    vehicle9.next_service_due = today + timedelta(days=120)
    
    events_added += 1
    print(f"     → Vehicle {vehicle9.license_plate}: Returned to service yesterday")
    
    # Commit all events
    session.commit()
    
    print("\n" + "=" * 60)
    print(f"✓ Injected {events_added} recent events")
    print("=" * 60)
    print("\nThese events ensure your AI agent will have compelling insights:")
    print("  • Critical issues requiring immediate attention")
    print("  • Performance trends (both positive and negative)")
    print("  • Maintenance schedules and overdue items")
    print("  • Fleet-wide patterns")
    print("  • Individual driver behavior")
    print("\nThe dashboard will highlight these in the daily digest!")


def main():
    """Standalone script to inject events into existing database"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fleetfix")
    
    print("=" * 60)
    print("FleetFix Recent Event Injector")
    print("=" * 60)
    print(f"\nConnecting to database: {DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        session.execute("SELECT 1")
        print("✓ Database connection successful")
        
        # Check if base data exists
        vehicle_count = session.query(Vehicle).count()
        if vehicle_count == 0:
            print("\n✗ No vehicles found in database!")
            print("   Run seed_data.py first to generate base data")
            sys.exit(1)
        
        print(f"✓ Found {vehicle_count} vehicles in database")
        
        inject_recent_events(session)
        
        print("\n✓ Event injection completed!")
        print("\nNext steps:")
        print("  1. Run test_connection.py to see the new events")
        print("  2. Query for 'yesterday' or 'today' events in your dashboard")
        print("  3. The AI agent will highlight these in the daily digest")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
