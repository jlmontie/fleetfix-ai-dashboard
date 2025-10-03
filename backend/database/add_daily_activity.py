"""
FleetFix Daily Activity Generator
Simulates one day of new fleet activity
Optional: Run this daily to keep data feeling fresh
"""

import random
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Driver, Vehicle, Telemetry, DriverPerformance, FaultCode
from dotenv import load_dotenv

load_dotenv()

KC_CENTER_LAT = 39.0997
KC_CENTER_LON = -94.5786


def get_random_coords(center_lat, center_lon, radius_miles=30):
    """Generate random GPS coordinates"""
    lat_degree_miles = 69.0
    lon_degree_miles = 54.6
    
    lat_offset = random.uniform(-radius_miles, radius_miles) / lat_degree_miles
    lon_offset = random.uniform(-radius_miles, radius_miles) / lon_degree_miles
    
    return (
        round(center_lat + lat_offset, 8),
        round(center_lon + lon_offset, 8)
    )


def calculate_driver_score(harsh_braking, rapid_accel, speeding, idle_minutes):
    """Calculate driver performance score (0-100)"""
    score = 100
    score -= harsh_braking * 5
    score -= rapid_accel * 4
    score -= speeding * 8
    score -= (idle_minutes // 30) * 2
    return max(0, min(100, score))


def add_daily_telemetry(session, target_date=None):
    """Add telemetry data for a specific date (defaults to today)"""
    if target_date is None:
        target_date = date.today()
    
    print(f"\n📡 Adding telemetry for {target_date}...")
    
    vehicles = session.query(Vehicle).filter(Vehicle.status == 'active').all()
    drivers = session.query(Driver).filter(Driver.status == 'active').all()
    
    if not vehicles or not drivers:
        print("⚠️  No active vehicles or drivers found")
        return 0
    
    telemetry_records = []
    start_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=6)
    
    for vehicle in vehicles:
        # Skip some vehicles (not all vehicles operate every day)
        if random.random() < 0.15:
            continue
        
        driver = random.choice(drivers)
        
        # Generate 48 readings (every 30 minutes, 6am-6pm)
        for reading in range(48):
            timestamp = start_time + timedelta(minutes=15 * reading)
            
            lat, lon = get_random_coords(KC_CENTER_LAT, KC_CENTER_LON)
            speed = max(0, min(65, random.gauss(35, 15)))
            fuel_level = max(10, 100 - (reading * 1.5) + random.uniform(-5, 5))
            engine_temp = random.uniform(180, 210)
            
            telem = Telemetry(
                vehicle_id=vehicle.id,
                driver_id=driver.id,
                timestamp=timestamp,
                gps_lat=Decimal(str(lat)),
                gps_lon=Decimal(str(lon)),
                speed=Decimal(str(round(speed, 2))),
                fuel_level=Decimal(str(round(fuel_level, 2))),
                engine_temp=Decimal(str(round(engine_temp, 2))),
                odometer=vehicle.current_mileage + reading
            )
            telemetry_records.append(telem)
        
        # Update vehicle mileage
        vehicle.current_mileage += random.randint(40, 80)
    
    session.add_all(telemetry_records)
    session.commit()
    
    print(f"   ✓ Added {len(telemetry_records)} telemetry records")
    return len(telemetry_records)


def add_daily_performance(session, target_date=None):
    """Add driver performance records for a specific date"""
    if target_date is None:
        target_date = date.today()
    
    print(f"\n👤 Adding driver performance for {target_date}...")
    
    vehicles = session.query(Vehicle).filter(Vehicle.status == 'active').all()
    drivers = session.query(Driver).filter(Driver.status == 'active').all()
    
    if not vehicles or not drivers:
        print("⚠️  No active vehicles or drivers found")
        return 0
    
    performance_records = []
    
    for vehicle in vehicles:
        if random.random() < 0.15:
            continue
        
        driver = random.choice(drivers)
        
        # Generate realistic performance metrics
        aggression_level = random.uniform(0, 1)
        harsh_braking = max(0, int(aggression_level * 8) + random.randint(-2, 2))
        rapid_accel = max(0, int(aggression_level * 10) + random.randint(-3, 3))
        speeding = max(0, int(aggression_level * 5) + random.randint(-1, 2))
        idle_time = random.randint(15, 90)
        hours_driven = Decimal(str(round(random.uniform(6, 10), 2)))
        miles_driven = Decimal(str(round(float(hours_driven) * random.uniform(25, 45), 2)))
        score = calculate_driver_score(harsh_braking, rapid_accel, speeding, idle_time)
        
        perf = DriverPerformance(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            date=target_date,
            harsh_braking_events=harsh_braking,
            rapid_acceleration_events=rapid_accel,
            speeding_events=speeding,
            idle_time_minutes=idle_time,
            hours_driven=hours_driven,
            miles_driven=miles_driven,
            score=score
        )
        performance_records.append(perf)
    
    session.add_all(performance_records)
    session.commit()
    
    print(f"   ✓ Added {len(performance_records)} performance records")
    return len(performance_records)


def add_random_events(session, target_date=None):
    """Randomly add fault codes or other events"""
    if target_date is None:
        target_date = date.today()
    
    print(f"\n🔧 Generating random events for {target_date}...")
    
    vehicles = session.query(Vehicle).filter(Vehicle.status == 'active').all()
    
    if not vehicles:
        print("⚠️  No active vehicles found")
        return 0
    
    events_added = 0
    
    # 30% chance of a new fault code
    if random.random() < 0.3:
        vehicle = random.choice(vehicles)
        
        fault_codes = [
            ('P0420', 'Catalyst System Efficiency Below Threshold', 'warning'),
            ('P0300', 'Random/Multiple Cylinder Misfire Detected', 'warning'),
            ('P0455', 'Evaporative Emission System Leak Detected', 'info'),
            ('C1234', 'ABS Wheel Speed Sensor Circuit Failure', 'warning'),
        ]
        
        code, description, severity = random.choice(fault_codes)
        
        fault = FaultCode(
            vehicle_id=vehicle.id,
            timestamp=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=random.randint(8, 17)),
            code=code,
            description=description,
            severity=severity,
            resolved=False
        )
        session.add(fault)
        events_added += 1
        print(f"   ✓ New fault code: {code} on vehicle {vehicle.license_plate}")
    
    # 20% chance to resolve an existing fault
    if random.random() < 0.2:
        unresolved = session.query(FaultCode).filter(
            FaultCode.resolved == False
        ).order_by(FaultCode.timestamp.asc()).first()
        
        if unresolved:
            unresolved.resolved = True
            unresolved.resolved_date = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=random.randint(9, 16))
            unresolved.resolution_notes = random.choice([
                'Replaced faulty sensor',
                'Cleaned and reset system',
                'Software update applied',
                'Component replaced'
            ])
            events_added += 1
            print(f"   ✓ Resolved fault code: {unresolved.code}")
    
    session.commit()
    return events_added


def main():
    """Generate one day of fleet activity"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add daily fleet activity')
    parser.add_argument('--date', type=str, help='Date to generate (YYYY-MM-DD), defaults to today')
    args = parser.parse_args()
    
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print("✗ Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = date.today()
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fleetfix")
    
    print("=" * 60)
    print("FleetFix Daily Activity Generator")
    print("=" * 60)
    print(f"\nTarget date: {target_date}")
    print(f"Connecting to database: {DATABASE_URL}")
    
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
        
        # Check if data already exists for this date
        existing_perf = session.query(DriverPerformance).filter(
            DriverPerformance.date == target_date
        ).count()
        
        if existing_perf > 0:
            print(f"\n⚠️  Warning: {existing_perf} performance records already exist for {target_date}")
            response = input("Continue anyway? This will add duplicate data. (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                sys.exit(0)
        
        print("\n" + "=" * 60)
        print(f"Generating activity for {target_date}")
        print("=" * 60)
        
        telemetry_count = add_daily_telemetry(session, target_date)
        performance_count = add_daily_performance(session, target_date)
        events_count = add_random_events(session, target_date)
        
        print("\n" + "=" * 60)
        print("Daily Activity Summary")
        print("=" * 60)
        print(f"Telemetry records:    {telemetry_count}")
        print(f"Performance records:  {performance_count}")
        print(f"New events:           {events_count}")
        print("=" * 60)
        
        print(f"\n✓ Successfully added activity for {target_date}")
        print("\nNext steps:")
        print("  1. Query the database to see today's data")
        print("  2. Run this daily (or schedule with cron) to keep data fresh")
        print("  3. The AI dashboard will show current insights")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
