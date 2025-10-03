-- FleetFix Database Schema
-- PostgreSQL 15+

-- Drop existing tables (careful in production!)
DROP TABLE IF EXISTS fault_codes CASCADE;
DROP TABLE IF EXISTS driver_performance CASCADE;
DROP TABLE IF EXISTS telemetry CASCADE;
DROP TABLE IF EXISTS maintenance_records CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;

-- Drivers table
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    hire_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_driver_status CHECK (status IN ('active', 'inactive', 'suspended'))
);

-- Vehicles table
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) UNIQUE NOT NULL,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    purchase_date DATE NOT NULL,
    current_mileage INTEGER NOT NULL DEFAULT 0,
    last_service_date DATE,
    next_service_due DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_vehicle_status CHECK (status IN ('active', 'maintenance', 'inactive', 'retired')),
    CONSTRAINT chk_vehicle_type CHECK (vehicle_type IN ('cargo_van', 'pickup_truck', 'box_truck', 'sedan', 'suv')),
    CONSTRAINT chk_year CHECK (year >= 2010 AND year <= 2025),
    CONSTRAINT chk_mileage CHECK (current_mileage >= 0)
);

-- Maintenance records table
CREATE TABLE maintenance_records (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    service_date DATE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    description TEXT,
    cost DECIMAL(10, 2) NOT NULL,
    mileage_at_service INTEGER NOT NULL,
    next_service_mileage INTEGER,
    performed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cost CHECK (cost >= 0),
    CONSTRAINT chk_service_type CHECK (service_type IN (
        'oil_change', 'tire_rotation', 'brake_service', 'transmission_service',
        'engine_repair', 'electrical_repair', 'inspection', 'general_maintenance',
        'tire_replacement', 'battery_replacement', 'other'
    ))
);

-- Telemetry table (GPS, speed, fuel, engine data)
CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
    timestamp TIMESTAMP NOT NULL,
    gps_lat DECIMAL(10, 8) NOT NULL,
    gps_lon DECIMAL(11, 8) NOT NULL,
    speed DECIMAL(5, 2) NOT NULL,
    fuel_level DECIMAL(5, 2) NOT NULL,
    engine_temp DECIMAL(5, 2) NOT NULL,
    odometer INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_speed CHECK (speed >= 0 AND speed <= 120),
    CONSTRAINT chk_fuel CHECK (fuel_level >= 0 AND fuel_level <= 100),
    CONSTRAINT chk_engine_temp CHECK (engine_temp >= -20 AND engine_temp <= 250)
);

-- Driver performance table (daily metrics)
CREATE TABLE driver_performance (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    harsh_braking_events INTEGER NOT NULL DEFAULT 0,
    rapid_acceleration_events INTEGER NOT NULL DEFAULT 0,
    speeding_events INTEGER NOT NULL DEFAULT 0,
    idle_time_minutes INTEGER NOT NULL DEFAULT 0,
    hours_driven DECIMAL(5, 2) NOT NULL DEFAULT 0,
    miles_driven DECIMAL(8, 2) NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_score CHECK (score >= 0 AND score <= 100),
    CONSTRAINT chk_events CHECK (
        harsh_braking_events >= 0 AND 
        rapid_acceleration_events >= 0 AND 
        speeding_events >= 0
    ),
    CONSTRAINT unique_driver_vehicle_date UNIQUE (driver_id, vehicle_id, date)
);

-- Fault codes table (diagnostic trouble codes)
CREATE TABLE fault_codes (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_date TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_severity CHECK (severity IN ('critical', 'warning', 'info'))
);

-- Create indexes for common queries
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_next_service ON vehicles(next_service_due);
CREATE INDEX idx_maintenance_vehicle ON maintenance_records(vehicle_id, service_date DESC);
CREATE INDEX idx_telemetry_vehicle_time ON telemetry(vehicle_id, timestamp DESC);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp DESC);
CREATE INDEX idx_driver_perf_driver ON driver_performance(driver_id, date DESC);
CREATE INDEX idx_driver_perf_date ON driver_performance(date DESC);
CREATE INDEX idx_fault_codes_vehicle ON fault_codes(vehicle_id, timestamp DESC);
CREATE INDEX idx_fault_codes_unresolved ON fault_codes(vehicle_id, resolved) WHERE resolved = FALSE;

-- Create views for common analytics
CREATE OR REPLACE VIEW vehicle_health_summary AS
SELECT 
    v.id,
    v.make,
    v.model,
    v.year,
    v.license_plate,
    v.status,
    v.current_mileage,
    v.next_service_due,
    CASE 
        WHEN v.next_service_due < CURRENT_DATE THEN 'overdue'
        WHEN v.next_service_due < CURRENT_DATE + INTERVAL '7 days' THEN 'due_soon'
        ELSE 'ok'
    END as maintenance_status,
    COUNT(DISTINCT fc.id) FILTER (WHERE fc.resolved = FALSE) as active_fault_codes,
    COUNT(DISTINCT fc.id) FILTER (WHERE fc.resolved = FALSE AND fc.severity = 'critical') as critical_faults
FROM vehicles v
LEFT JOIN fault_codes fc ON v.id = fc.vehicle_id
GROUP BY v.id, v.make, v.model, v.year, v.license_plate, v.status, v.current_mileage, v.next_service_due;

CREATE OR REPLACE VIEW driver_performance_summary AS
SELECT 
    d.id,
    d.name,
    d.status,
    AVG(dp.score) as avg_score,
    SUM(dp.miles_driven) as total_miles,
    SUM(dp.hours_driven) as total_hours,
    SUM(dp.harsh_braking_events) as total_harsh_braking,
    SUM(dp.rapid_acceleration_events) as total_rapid_acceleration,
    SUM(dp.speeding_events) as total_speeding,
    COUNT(DISTINCT dp.date) as days_driven
FROM drivers d
LEFT JOIN driver_performance dp ON d.id = dp.driver_id
WHERE dp.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.id, d.name, d.status;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fleetfix_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fleetfix_user;