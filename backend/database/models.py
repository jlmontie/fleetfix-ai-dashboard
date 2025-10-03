"""
FleetFix Database Models
SQLAlchemy ORM models for the FleetFix database
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Boolean, Text,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Driver(Base):
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='active')
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    performance_records = relationship('DriverPerformance', back_populates='driver', cascade='all, delete-orphan')
    telemetry_records = relationship('Telemetry', back_populates='driver')
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name='chk_driver_status'),
    )
    
    def __repr__(self):
        return f"<Driver(id={self.id}, name='{self.name}', status='{self.status}')>"


class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    vin = Column(String(17), unique=True, nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False)
    vehicle_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default='active')
    purchase_date = Column(Date, nullable=False)
    current_mileage = Column(Integer, nullable=False, default=0)
    last_service_date = Column(Date)
    next_service_due = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    maintenance_records = relationship('MaintenanceRecord', back_populates='vehicle', cascade='all, delete-orphan')
    telemetry_records = relationship('Telemetry', back_populates='vehicle', cascade='all, delete-orphan')
    driver_performance = relationship('DriverPerformance', back_populates='vehicle', cascade='all, delete-orphan')
    fault_codes = relationship('FaultCode', back_populates='vehicle', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'maintenance', 'inactive', 'retired')", name='chk_vehicle_status'),
        CheckConstraint("vehicle_type IN ('cargo_van', 'pickup_truck', 'box_truck', 'sedan', 'suv')", name='chk_vehicle_type'),
        CheckConstraint('year >= 2010 AND year <= 2025', name='chk_year'),
        CheckConstraint('current_mileage >= 0', name='chk_mileage'),
    )
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, {self.year} {self.make} {self.model}, plate='{self.license_plate}')>"


class MaintenanceRecord(Base):
    __tablename__ = 'maintenance_records'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    service_date = Column(Date, nullable=False)
    service_type = Column(String(50), nullable=False)
    description = Column(Text)
    cost = Column(Numeric(10, 2), nullable=False)
    mileage_at_service = Column(Integer, nullable=False)
    next_service_mileage = Column(Integer)
    performed_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship('Vehicle', back_populates='maintenance_records')
    
    __table_args__ = (
        CheckConstraint('cost >= 0', name='chk_cost'),
        CheckConstraint(
            "service_type IN ('oil_change', 'tire_rotation', 'brake_service', 'transmission_service', "
            "'engine_repair', 'electrical_repair', 'inspection', 'general_maintenance', "
            "'tire_replacement', 'battery_replacement', 'other')",
            name='chk_service_type'
        ),
    )
    
    def __repr__(self):
        return f"<MaintenanceRecord(id={self.id}, vehicle_id={self.vehicle_id}, type='{self.service_type}', date={self.service_date})>"


class Telemetry(Base):
    __tablename__ = 'telemetry'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id', ondelete='SET NULL'))
    timestamp = Column(DateTime, nullable=False)
    gps_lat = Column(Numeric(10, 8), nullable=False)
    gps_lon = Column(Numeric(11, 8), nullable=False)
    speed = Column(Numeric(5, 2), nullable=False)
    fuel_level = Column(Numeric(5, 2), nullable=False)
    engine_temp = Column(Numeric(5, 2), nullable=False)
    odometer = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship('Vehicle', back_populates='telemetry_records')
    driver = relationship('Driver', back_populates='telemetry_records')
    
    __table_args__ = (
        CheckConstraint('speed >= 0 AND speed <= 120', name='chk_speed'),
        CheckConstraint('fuel_level >= 0 AND fuel_level <= 100', name='chk_fuel'),
        CheckConstraint('engine_temp >= -20 AND engine_temp <= 250', name='chk_engine_temp'),
    )
    
    def __repr__(self):
        return f"<Telemetry(id={self.id}, vehicle_id={self.vehicle_id}, timestamp={self.timestamp})>"


class DriverPerformance(Base):
    __tablename__ = 'driver_performance'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    harsh_braking_events = Column(Integer, nullable=False, default=0)
    rapid_acceleration_events = Column(Integer, nullable=False, default=0)
    speeding_events = Column(Integer, nullable=False, default=0)
    idle_time_minutes = Column(Integer, nullable=False, default=0)
    hours_driven = Column(Numeric(5, 2), nullable=False, default=0)
    miles_driven = Column(Numeric(8, 2), nullable=False, default=0)
    score = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    driver = relationship('Driver', back_populates='performance_records')
    vehicle = relationship('Vehicle', back_populates='driver_performance')
    
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='chk_score'),
        CheckConstraint(
            'harsh_braking_events >= 0 AND rapid_acceleration_events >= 0 AND speeding_events >= 0',
            name='chk_events'
        ),
        UniqueConstraint('driver_id', 'vehicle_id', 'date', name='unique_driver_vehicle_date'),
    )
    
    def __repr__(self):
        return f"<DriverPerformance(id={self.id}, driver_id={self.driver_id}, date={self.date}, score={self.score})>"


class FaultCode(Base):
    __tablename__ = 'fault_codes'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    code = Column(String(10), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_date = Column(DateTime)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship('Vehicle', back_populates='fault_codes')
    
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'warning', 'info')", name='chk_severity'),
    )
    
    def __repr__(self):
        return f"<FaultCode(id={self.id}, vehicle_id={self.vehicle_id}, code='{self.code}', severity='{self.severity}')>"