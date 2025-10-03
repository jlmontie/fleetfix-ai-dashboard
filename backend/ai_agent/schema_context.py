"""
FleetFix Schema Context Builder
Introspects database schema and creates LLM-friendly descriptions
"""

import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, MetaData, text
from sqlalchemy.orm import Session
from database.config import db_config
from database.models import Base


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional[str] = None
    description: Optional[str] = None


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo]
    row_count: int
    description: Optional[str] = None


class SchemaContextBuilder:
    """
    Builds context about database schema for LLM consumption
    """
    
    # Business context descriptions for tables
    TABLE_DESCRIPTIONS = {
        'drivers': 'Fleet drivers with license information and employment status',
        'vehicles': 'Fleet vehicles including make, model, mileage, and maintenance schedule',
        'maintenance_records': 'Historical maintenance and service records for vehicles',
        'telemetry': 'Real-time vehicle data including GPS location, speed, fuel level, and engine temperature',
        'driver_performance': 'Daily driver behavior metrics including harsh braking, speeding, and safety scores',
        'fault_codes': 'Diagnostic trouble codes (DTCs) from vehicle onboard diagnostics'
    }
    
    # Business context for columns
    COLUMN_DESCRIPTIONS = {
        'drivers': {
            'license_number': 'Unique driver license identifier',
            'hire_date': 'Date driver was hired by FleetFix',
            'status': 'Employment status: active, inactive, or suspended'
        },
        'vehicles': {
            'vin': 'Vehicle identification number (unique)',
            'license_plate': 'Vehicle license plate number',
            'vehicle_type': 'Type: cargo_van, pickup_truck, box_truck, sedan, or suv',
            'current_mileage': 'Total odometer reading in miles',
            'next_service_due': 'Date when next maintenance is scheduled',
            'status': 'Vehicle status: active, maintenance, inactive, or retired'
        },
        'maintenance_records': {
            'service_type': 'Type of service: oil_change, tire_rotation, brake_service, etc.',
            'cost': 'Service cost in USD',
            'mileage_at_service': 'Vehicle mileage when service was performed',
            'next_service_mileage': 'Recommended mileage for next service'
        },
        'telemetry': {
            'timestamp': 'Date and time of reading (recorded every 15-30 minutes)',
            'gps_lat': 'GPS latitude coordinate',
            'gps_lon': 'GPS longitude coordinate',
            'speed': 'Vehicle speed in miles per hour',
            'fuel_level': 'Fuel tank level as percentage (0-100)',
            'engine_temp': 'Engine temperature in Fahrenheit',
            'odometer': 'Odometer reading at time of telemetry'
        },
        'driver_performance': {
            'date': 'Date of performance record (one record per driver per vehicle per day)',
            'harsh_braking_events': 'Number of sudden/hard braking incidents',
            'rapid_acceleration_events': 'Number of aggressive acceleration incidents',
            'speeding_events': 'Number of times driver exceeded speed limit',
            'idle_time_minutes': 'Total minutes vehicle was idling',
            'score': 'Overall driver safety score (0-100, higher is better)'
        },
        'fault_codes': {
            'code': 'OBD-II diagnostic trouble code (e.g., P0301, C1234)',
            'severity': 'Fault severity: critical, warning, or info',
            'resolved': 'Whether the fault has been fixed',
            'timestamp': 'When the fault code was triggered'
        }
    }
    
    def __init__(self, session: Session = None):
        """Initialize with optional database session"""
        self.session = session or db_config.get_session()
        self.inspector = inspect(db_config.engine)
        self._close_session = session is None
    
    def __del__(self):
        """Close session if we created it"""
        if self._close_session and self.session:
            self.session.close()
    
    def get_table_info(self, table_name: str) -> TableInfo:
        """Get detailed information about a specific table"""
        columns = []
        
        # Get column information
        for column in self.inspector.get_columns(table_name):
            col_name = column['name']
            col_type = str(column['type'])
            
            # Check if primary key
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            is_primary = col_name in pk_constraint.get('constrained_columns', [])
            
            # Check for foreign keys
            foreign_key = None
            for fk in self.inspector.get_foreign_keys(table_name):
                if col_name in fk['constrained_columns']:
                    ref_table = fk['referred_table']
                    ref_column = fk['referred_columns'][0]
                    foreign_key = f"{ref_table}.{ref_column}"
                    break
            
            # Get description if available
            description = self.COLUMN_DESCRIPTIONS.get(table_name, {}).get(col_name)
            
            col_info = ColumnInfo(
                name=col_name,
                type=col_type,
                nullable=column['nullable'],
                primary_key=is_primary,
                foreign_key=foreign_key,
                description=description
            )
            columns.append(col_info)
        
        # Get row count
        try:
            row_count = self.session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()
        except Exception:
            row_count = 0
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count,
            description=self.TABLE_DESCRIPTIONS.get(table_name)
        )
    
    def get_all_tables(self) -> List[TableInfo]:
        """Get information about all tables in the database"""
        table_names = self.inspector.get_table_names()
        return [self.get_table_info(name) for name in table_names]
    
    def build_schema_context(self, include_samples: bool = False) -> str:
        """
        Build a comprehensive schema context for LLM
        
        Args:
            include_samples: Whether to include sample data (increases token count)
        
        Returns:
            Formatted schema description
        """
        tables = self.get_all_tables()
        
        context_parts = [
            "# FleetFix Database Schema\n",
            "This is a PostgreSQL database for a fleet management system called FleetFix.",
            "FleetFix tracks vehicles, drivers, maintenance, real-time telemetry, and performance metrics.\n"
        ]
        
        # Add table summaries
        context_parts.append("\n## Tables Overview\n")
        for table in tables:
            context_parts.append(
                f"- **{table.name}** ({table.row_count:,} rows): {table.description or 'No description'}"
            )
        
        # Add detailed table information
        context_parts.append("\n## Detailed Schema\n")
        for table in tables:
            context_parts.append(f"\n### {table.name}")
            if table.description:
                context_parts.append(f"{table.description}\n")
            
            context_parts.append("**Columns:**")
            for col in table.columns:
                # Build column description
                col_desc = f"- `{col.name}` ({col.type})"
                
                # Add attributes
                attrs = []
                if col.primary_key:
                    attrs.append("PRIMARY KEY")
                if col.foreign_key:
                    attrs.append(f"FOREIGN KEY -> {col.foreign_key}")
                if not col.nullable:
                    attrs.append("NOT NULL")
                
                if attrs:
                    col_desc += f" [{', '.join(attrs)}]"
                
                # Add description if available
                if col.description:
                    col_desc += f"\n  {col.description}"
                
                context_parts.append(col_desc)
        
        # Add relationships
        context_parts.append("\n## Key Relationships\n")
        relationships = [
            "- drivers → driver_performance (one-to-many)",
            "- drivers → telemetry (one-to-many)",
            "- vehicles → maintenance_records (one-to-many)",
            "- vehicles → telemetry (one-to-many)",
            "- vehicles → driver_performance (one-to-many)",
            "- vehicles → fault_codes (one-to-many)"
        ]
        context_parts.extend(relationships)
        
        # Add important notes
        context_parts.append("\n## Important Notes\n")
        notes = [
            "- All timestamps are in UTC",
            "- Telemetry data is recorded every 15-30 minutes during work hours (6am-6pm)",
            "- Driver performance is recorded daily (one record per driver per vehicle per day)",
            "- Use CURRENT_DATE for queries about 'today' or 'yesterday'",
            "- Vehicle status values: 'active', 'maintenance', 'inactive', 'retired'",
            "- Driver status values: 'active', 'inactive', 'suspended'",
            "- Fault code severity values: 'critical', 'warning', 'info'",
            "- Service type values: 'oil_change', 'tire_rotation', 'brake_service', etc."
        ]
        context_parts.extend([f"- {note}" for note in notes])
        
        # Add sample queries
        context_parts.append("\n## Example Query Patterns\n")
        examples = [
            "```sql\n-- Vehicles overdue for maintenance\nSELECT * FROM vehicles WHERE next_service_due < CURRENT_DATE;\n```",
            "```sql\n-- Driver performance in last 7 days\nSELECT * FROM driver_performance WHERE date >= CURRENT_DATE - INTERVAL '7 days';\n```",
            "```sql\n-- Active unresolved fault codes\nSELECT * FROM fault_codes WHERE resolved = FALSE;\n```"
        ]
        context_parts.extend(examples)
        
        return "\n".join(context_parts)
    
    def build_concise_context(self) -> str:
        """
        Build a concise schema context (optimized for token efficiency)
        Use this when you need to minimize LLM token usage
        """
        tables = self.get_all_tables()
        
        lines = ["FleetFix Database Schema (PostgreSQL):\n"]
        
        for table in tables:
            lines.append(f"\n{table.name} ({table.row_count:,} rows):")
            
            # Only include key columns
            key_columns = [col for col in table.columns if col.primary_key or col.foreign_key or not col.nullable]
            for col in key_columns:
                fk_info = f" -> {col.foreign_key}" if col.foreign_key else ""
                pk_info = " (PK)" if col.primary_key else ""
                lines.append(f"  - {col.name}: {col.type}{pk_info}{fk_info}")
        
        return "\n".join(lines)
    
    def get_table_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """
        Get sample rows from a table
        Useful for understanding data format
        """
        try:
            result = self.session.execute(
                text(f"SELECT * FROM {table_name} LIMIT {limit}")
            )
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return [{"error": str(e)}]


def main():
    """Test the schema context builder"""
    print("=" * 70)
    print("FleetFix Schema Context Builder - Test")
    print("=" * 70)
    
    builder = SchemaContextBuilder()
    
    # Test 1: Get all tables
    print("\n1. All Tables:")
    tables = builder.get_all_tables()
    for table in tables:
        print(f"   - {table.name}: {table.row_count:,} rows")
    
    # Test 2: Detailed info for one table
    print("\n2. Detailed Info - vehicles table:")
    vehicles_info = builder.get_table_info('vehicles')
    print(f"   Description: {vehicles_info.description}")
    print(f"   Columns: {len(vehicles_info.columns)}")
    for col in vehicles_info.columns[:5]:  # Show first 5
        print(f"     - {col.name} ({col.type})")
    
    # Test 3: Full context
    print("\n3. Full Schema Context (first 500 chars):")
    full_context = builder.build_schema_context()
    print(full_context[:500] + "...\n")
    
    # Test 4: Concise context
    print("4. Concise Schema Context:")
    concise_context = builder.build_concise_context()
    print(concise_context)
    
    # Test 5: Sample data
    print("\n5. Sample Data - drivers table:")
    samples = builder.get_table_sample_data('drivers', limit=2)
    for i, sample in enumerate(samples, 1):
        print(f"   Row {i}: {sample.get('name', 'N/A')} - {sample.get('status', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("Schema context ready for LLM integration!")
    print("=" * 70)
    
    # Save full context to file for inspection
    output_path = "schema_context_output.txt"
    with open(output_path, 'w') as f:
        f.write(builder.build_schema_context())
    print(f"\nFull context saved to: {output_path}")


if __name__ == "__main__":
    main()