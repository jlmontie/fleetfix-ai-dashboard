"""
FleetFix Sample Data Generator with Rolling Time Windows
Generates realistic fleet management data that's always relative to current date
"""

import random
import os
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Driver, Vehicle, MaintenanceRecord, Telemetry, DriverPerformance, FaultCode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Faker
fake = Faker()

# Configuration
NUM_DRIVERS = 25
NUM_VEHICLES = 30
HISTORICAL_MONTHS = 9
TELEMETRY_READINGS_PER_DAY = 48  # Every 30 minutes during work hours

# Kansas City center coordinates
KC_CENTER_LAT = 39.0997
KC_CENTER_LON = -94.5786


def get_random_coords(center_lat, center_lon, radius_miles=30):
    """Generate random GPS coordinates within radius of center"""
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


def generate_drivers(session):
    """Generate driver records"""
    print("Generating drivers...")
    drivers = []
    
    for i in range(NUM_DRIVERS):
        # Hire date is in the past (1-5 years ago)
        hire_date = fake.date_between(start_date='-5y', end_date='-6m')
        driver = Driver(
            name=fake.name(),
            license_number=fake.bothify(text='??######', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            hire_date=hire_date,
            status=random.choices(['active', 'inactive'], weights=[95, 5])[0],
            phone=fake.phone_number()
        )
        drivers.append(driver)
    
    session.add_all(drivers)
    session.commit()
    print(f"Created {len(drivers)} drivers")
    return drivers


def generate_vehicles(session):
    """Generate vehicle records with rolling time windows"""
    print("Generating vehicles...")
    vehicles = []
    
    vehicle_configs = [
        ('cargo_van', 'Ford', ['Transit', 'Transit Connect'], (25000, 45000)),
        ('cargo_van', 'Mercedes-Benz', ['Sprinter'], (20000, 40000)),
        ('cargo_van', 'Ram', ['ProMaster'], (22000, 42000)),
        ('pickup_truck', 'Ford', ['F-150', 'F-250'], (18000, 35000)),
        ('pickup_truck', 'Chevrolet', ['Silverado 1500'], (19000, 36000)),
        ('pickup_truck', 'Ram', ['1500', '2500'], (18000, 34000)),
        ('box_truck', 'Isuzu', ['NPR', 'NQR'], (15000, 30000)),
        ('box_truck', 'Freightliner', ['M2'], (14000, 28000)),
        ('sedan', 'Toyota', ['Camry'], (12000, 25000)),
        ('suv', 'Chevrolet', ['Tahoe'], (15000, 28000)),
    ]
    
    for i in range(NUM_VEHICLES):
        vehicle_type, make, models, mileage_range = random.choice(vehicle_configs)
        model = random.choice(models)
        year = random.randint(2018, 2024)
        
        # Purchase date is relative to vehicle age
        purchase_date = fake.date_between(start_date=f'-{2025-year}y', end_date='-6m')
        
        # Calculate realistic current mileage based on age
        vehicle_age_days = (date.today() - purchase_date).days
        annual_mileage = random.randint(*mileage_range)
        current_mileage = int((annual_mileage / 365) * vehicle_age_days)
        
        # Service scheduling relative to today
        miles_since_last_service = random.randint(0, 6000)
        last_service_mileage = current_mileage - miles_since_last_service
        days_since_service = int(miles_since_last_service / (annual_mileage / 365))
        last_service_date = date.today() - timedelta(days=days_since_service)
        
        # Next service due (5000 miles or ~120 days from last service)
        next_service_mileage = last_service_mileage + 5000
        days_until_service = int((next_service_mileage - current_mileage) / (annual_mileage / 365))
        next_service_due = date.today() + timedelta(days=days_until_service)
        
        # DON'T make vehicles overdue yet - we'll do this in inject_recent_events
        # This ensures clean base data
        
        vehicle = Vehicle(
            make=make,
            model=model,
            year=year,
            vin=fake.bothify(text='?????????????????', letters='ABCDEFGHJKLMNPRSTUVWXYZ123456789'),
            license_plate=fake.bothify(text='???####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ').upper(),
            vehicle_type=vehicle_type,
            status=random.choices(['active', 'maintenance', 'inactive'], weights=[92, 6, 2])[0],
            purchase_date=purchase_date,
            current_mileage=current_mileage,
            last_service_date=last_service_date,
            next_service_due=next_service_due
        )
        vehicles.append(vehicle)
    
    session.add_all(vehicles)
    session.commit()
    print(f"Created {len(vehicles)} vehicles")
    return vehicles


def generate_maintenance_records(session, vehicles):
    """Generate historical maintenance records"""
    print("Generating maintenance records...")
    records = []
    
    service_types_costs = {
        'oil_change': (35, 75),
        'tire_rotation': (25, 50),
        'brake_service': (150, 400),
        'transmission_service': (200, 500),
        'engine_repair': (500, 2500),
        'electrical_repair': (100, 800),
        'inspection': (20, 50),
        'general_maintenance': (80, 250),
        'tire_replacement': (400, 1200),
        'battery_replacement': (100, 250),
    }
    
    for vehicle in vehicles:
        num_services = random.randint(6, 12)
        vehicle_age_days = (date.today() - vehicle.purchase_date).days
        
        for i in range(num_services):
            days_ago = random.randint(i * (vehicle_age_days // num_services), 
                                     (i + 1) * (vehicle_age_days // num_services))
            service_date = date.today() - timedelta(days=days_ago)
            
            daily_mileage = vehicle.current_mileage / vehicle_age_days if vehicle_age_days > 0 else 0
            mileage_at_service = int(daily_mileage * (vehicle_age_days - days_ago))
            
            service_type = random.choices(
                list(service_types_costs.keys()),
                weights=[25, 15, 10, 5, 3, 5, 20, 8, 4, 5]
            )[0]
            
            cost_min, cost_max = service_types_costs[service_type]
            cost = Decimal(str(round(random.uniform(cost_min, cost_max), 2)))
            
            record = MaintenanceRecord(
                vehicle_id=vehicle.id,
                service_date=service_date,
                service_type=service_type,
                description=f"{service_type.replace('_', ' ').title()} performed",
                cost=cost,
                mileage_at_service=mileage_at_service,
                next_service_mileage=mileage_at_service + 5000,
                performed_by=random.choice(['Joe\'s Auto', 'FleetFix Service Center', 'Quick Lube', 'Main Street Garage'])
            )
            records.append(record)
    
    session.add_all(records)
    session.commit()
    print(f"Created {len(records)} maintenance records")
    return records


def generate_telemetry_data(session, vehicles, drivers):
    """Generate telemetry data with rolling time window (ends TODAY)"""
    print("Generating telemetry data (this may take a minute)...")
    telemetry = []
    
    # CRITICAL: Start date is relative to NOW, end date is NOW
    start_date = datetime.now() - timedelta(days=HISTORICAL_MONTHS * 30)
    end_date = datetime.now()
    
    print(f"  Telemetry date range: {start_date.date()} to {end_date.date()}")
    
    for vehicle in vehicles:
        if vehicle.status == 'inactive':
            continue
            
        primary_driver = random.choice(drivers)
        
        current_date = start_date
        vehicle_mileage_tracker = vehicle.current_mileage - int((end_date - start_date).days * (vehicle.current_mileage / 365))
        
        while current_date <= end_date:
            # Skip some days (weekends, days off)
            if random.random() < 0.15:
                current_date += timedelta(days=1)
                continue
            
            work_start = current_date.replace(hour=6, minute=0, second=0)
            
            for reading in range(TELEMETRY_READINGS_PER_DAY):
                timestamp = work_start + timedelta(minutes=15 * reading)
                
                # Don't generate future data
                if timestamp > end_date:
                    break
                
                lat, lon = get_random_coords(KC_CENTER_LAT, KC_CENTER_LON)
                speed = max(0, min(65, random.gauss(35, 15)))
                fuel_level = max(10, 100 - (reading * 1.5) + random.uniform(-5, 5))
                engine_temp = random.uniform(180, 210)
                
                telemetry_record = Telemetry(
                    vehicle_id=vehicle.id,
                    driver_id=primary_driver.id,
                    timestamp=timestamp,
                    gps_lat=Decimal(str(lat)),
                    gps_lon=Decimal(str(lon)),
                    speed=Decimal(str(round(speed, 2))),
                    fuel_level=Decimal(str(round(fuel_level, 2))),
                    engine_temp=Decimal(str(round(engine_temp, 2))),
                    odometer=vehicle_mileage_tracker
                )
                telemetry.append(telemetry_record)
                
                vehicle_mileage_tracker += random.randint(0, 1)
            
            current_date += timedelta(days=1)
    
    # Batch insert for performance
    batch_size = 1000
    for i in range(0, len(telemetry), batch_size):
        session.add_all(telemetry[i:i+batch_size])
        session.commit()
        print(f"  Inserted {min(i+batch_size, len(telemetry))}/{len(telemetry)} telemetry records")
    
    print(f"Created {len(telemetry)} telemetry records")
    return telemetry


def generate_driver_performance(session, vehicles, drivers):
    """Generate daily driver performance metrics through TODAY"""
    print("Generating driver performance data...")
    performance = []
    
    # CRITICAL: End date is TODAY
    start_date = date.today() - timedelta(days=HISTORICAL_MONTHS * 30)
    end_date = date.today()
    
    print(f"  Performance date range: {start_date} to {end_date}")
    
    # Create driver profiles
    driver_profiles = {}
    for driver in drivers:
        driver_profiles[driver.id] = {
            'aggression_level': random.uniform(0, 1),
            'consistency': random.uniform(0.7, 1.0)
        }
    
    for vehicle in vehicles:
        if vehicle.status == 'inactive':
            continue
        
        assigned_drivers = random.sample(drivers, k=min(random.randint(1, 2), len(drivers)))
        
        current_date = start_date
        while current_date <= end_date:
            if random.random() < 0.15:
                current_date += timedelta(days=1)
                continue
            
            driver = random.choice(assigned_drivers)
            profile = driver_profiles[driver.id]
            
            base_harsh_braking = int(profile['aggression_level'] * 8)
            harsh_braking = max(0, base_harsh_braking + random.randint(-2, 2))
            
            base_rapid_accel = int(profile['aggression_level'] * 10)
            rapid_accel = max(0, base_rapid_accel + random.randint(-3, 3))
            
            base_speeding = int(profile['aggression_level'] * 5)
            speeding = max(0, base_speeding + random.randint(-1, 2))
            
            idle_time = random.randint(15, 90)
            hours_driven = Decimal(str(round(random.uniform(6, 10), 2)))
            miles_driven = Decimal(str(round(float(hours_driven) * random.uniform(25, 45), 2)))
            
            score = calculate_driver_score(harsh_braking, rapid_accel, speeding, idle_time)
            
            perf = DriverPerformance(
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                date=current_date,
                harsh_braking_events=harsh_braking,
                rapid_acceleration_events=rapid_accel,
                speeding_events=speeding,
                idle_time_minutes=idle_time,
                hours_driven=hours_driven,
                miles_driven=miles_driven,
                score=score
            )
            performance.append(perf)
            
            current_date += timedelta(days=1)
    
    session.add_all(performance)
    session.commit()
    print(f"Created {len(performance)} driver performance records")
    return performance


def generate_fault_codes(session, vehicles):
    """Generate diagnostic fault codes"""
    print("Generating fault codes...")
    fault_codes = []
    
    common_faults = [
        ('P0300', 'Random/Multiple Cylinder Misfire Detected', 'warning'),
        ('P0420', 'Catalyst System Efficiency Below Threshold', 'warning'),
        ('P0171', 'System Too Lean (Bank 1)', 'warning'),
        ('P0455', 'Evaporative Emission System Leak Detected (Large Leak)', 'info'),
        ('P0128', 'Coolant Thermostat Temperature Issue', 'info'),
        ('P0442', 'Evaporative Emission System Leak Detected (Small Leak)', 'info'),
        ('P0401', 'Exhaust Gas Recirculation Flow Insufficient', 'warning'),
        ('P0133', 'O2 Sensor Circuit Slow Response', 'info'),
        ('P0306', 'Cylinder 6 Misfire Detected', 'critical'),
        ('P0017', 'Crankshaft Position - Camshaft Position Correlation Issue', 'critical'),
        ('P0301', 'Cylinder 1 Misfire Detected', 'critical'),
        ('C1234', 'ABS Wheel Speed Sensor Front Right Circuit Failure', 'warning'),
        ('U0100', 'Lost Communication With ECM/PCM', 'critical'),
        ('B1342', 'ECM Is Defective', 'critical'),
    ]
    
    start_date = date.today() - timedelta(days=HISTORICAL_MONTHS * 30)
    
    for vehicle in vehicles:
        vehicle_age = (date.today() - vehicle.purchase_date).days / 365
        fault_likelihood = min(0.4, 0.05 + (vehicle_age * 0.05) + (vehicle.current_mileage / 200000))
        
        num_faults = int(random.uniform(0, 8) * fault_likelihood)
        
        for _ in range(num_faults):
            code, description, severity = random.choice(common_faults)
            
            days_ago = random.randint(30, HISTORICAL_MONTHS * 30)  # Don't generate recent faults yet
            timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Most historical faults are resolved
            resolved = random.random() < 0.85  # Higher resolution rate for historical data
            resolved_date = None
            resolution_notes = None
            
            if resolved:
                resolved_date = timestamp + timedelta(days=random.randint(1, 10))
                resolution_notes = random.choice([
                    'Replaced faulty sensor',
                    'Cleaned and reset system',
                    'Replaced component during scheduled maintenance',
                    'Software update applied',
                    'Part replaced under warranty'
                ])
            
            fault = FaultCode(
                vehicle_id=vehicle.id,
                timestamp=timestamp,
                code=code,
                description=description,
                severity=severity,
                resolved=resolved,
                resolved_date=resolved_date,
                resolution_notes=resolution_notes
            )
            fault_codes.append(fault)
    
    session.add_all(fault_codes)
    session.commit()
    print(f"Created {len(fault_codes)} fault codes")
    return fault_codes


def clear_existing_data(session):
    """Clear all existing data from tables"""
    print("\nClearing existing data...")
    try:
        session.query(FaultCode).delete()
        session.query(DriverPerformance).delete()
        session.query(Telemetry).delete()
        session.query(MaintenanceRecord).delete()
        session.query(Vehicle).delete()
        session.query(Driver).delete()
        session.commit()
        print("✓ Existing data cleared")
    except Exception as e:
        print(f"✗ Error clearing data: {e}")
        session.rollback()
        raise


def main():
    """Main data generation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample data for FleetFix')
    parser.add_argument('--reset', action='store_true', 
                       help='Clear existing data before generating new data')
    parser.add_argument('--inject-events', action='store_true',
                       help='Inject recent interesting events after data generation')
    args = parser.parse_args()
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fleetfix")
    
    print("=" * 60)
    print("FleetFix Data Generator (Rolling Time Windows)")
    print("=" * 60)
    print(f"\nConnecting to database: {DATABASE_URL}")
    print(f"Current date: {date.today()}")
    print(f"Data will span: {date.today() - timedelta(days=HISTORICAL_MONTHS * 30)} to {date.today()}")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        session.execute("SELECT 1")
        print("✓ Database connection successful")
        
    except Exception as e:
        print(f"\n✗ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check your DATABASE_URL in .env file")
        print("  3. Verify database 'fleetfix' exists")
        sys.exit(1)
    
    try:
        print("\nCreating database tables...")
        Base.metadata.create_all(engine)
        print("✓ Tables created successfully")
        
        if args.reset:
            clear_existing_data(session)
        else:
            existing_vehicles = session.query(Vehicle).count()
            if existing_vehicles > 0:
                print(f"\n⚠️  Warning: Database already contains {existing_vehicles} vehicles")
                print("    Running this script will ADD MORE data (duplicates)")
                print("    Use --reset flag to clear existing data first:")
                print("    python database/seed_data.py --reset")
                response = input("\nContinue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    sys.exit(0)
        
        print("\n" + "=" * 60)
        print("Starting data generation...")
        print("=" * 60 + "\n")
        
        drivers = generate_drivers(session)
        vehicles = generate_vehicles(session)
        maintenance_records = generate_maintenance_records(session, vehicles)
        telemetry = generate_telemetry_data(session, vehicles, drivers)
        performance = generate_driver_performance(session, vehicles, drivers)
        fault_codes = generate_fault_codes(session, vehicles)
        
        print("\n" + "=" * 60)
        print("Data Generation Summary")
        print("=" * 60)
        print(f"Drivers:              {len(drivers)}")
        print(f"Vehicles:             {len(vehicles)}")
        print(f"Maintenance Records:  {len(maintenance_records)}")
        print(f"Telemetry Records:    {len(telemetry)}")
        print(f"Performance Records:  {len(performance)}")
        print(f"Fault Codes:          {len(fault_codes)}")
        print("=" * 60)
        
        # Inject recent events if requested
        if args.inject_events:
            print("\n" + "=" * 60)
            print("Injecting Recent Events...")
            print("=" * 60)
            from database.inject_recent_events import inject_recent_events
            inject_recent_events(session)
        
        print("\n✓ Data generation completed successfully!")
        print("\nNext steps:")
        if not args.inject_events:
            print("  1. Run with --inject-events flag for interesting recent data:")
            print("     python database/seed_data.py --inject-events")
        print("  2. Verify: python database/test_connection.py")
        print("  3. Query 'yesterday' events to see rolling time windows in action")
        
    except Exception as e:
        print(f"\n✗ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()