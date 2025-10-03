## Why Rolling Time Windows Matter

### Traditional Approach (Static Dates)
```python
# Data is frozen in time
telemetry_date = datetime(2024, 3, 15)  # Always March 15, 2024
```
**Problem:** "Show me yesterday's issues" returns data from months ago!

### Our Approach (Dynamic Dates)
```python
# Data is always relative to NOW
telemetry_date = datetime.now() - timedelta(days=1)  # Yesterday
```
**Result:** "Show me yesterday's issues" actually returns yesterday's data!

### Impact on Your AI Dashboard

**What the AI can say on October 3, 2025:**
- ✅ "Yesterday, vehicle KC-7392 triggered a critical fault code"
- ✅ "Driver performance dropped 40% over the last 3 days"
- ✅ "You have 2 vehicles overdue for maintenance as of today"
- ✅ "Fleet fuel efficiency declined 8% this week"

**What the AI can say on October 10, 2025 (same database!):**
- ✅ "Yesterday, a different vehicle had issues" ← Data "moved forward"
- ✅ "Performance trends from last week" ← Always current
- ✅ "Current maintenance status" ← Always today

**This makes your portfolio project feel production-ready!**

---

## Testing Rolling Windows

Try these queries to verify the dynamic data:

```sql
-- Connect to database
psql -U fleetfix_user -d fleetfix

-- Events from yesterday (always returns yesterday's data!)
SELECT v.license_plate, fc.code, fc.severity, fc.timestamp
FROM fault_codes fc
JOIN vehicles v ON fc.vehicle_id = v.id
WHERE DATE(fc.timestamp) = CURRENT_DATE - INTERVAL '1 day'
  AND fc.resolved = FALSE;

-- Driver performance from last 7 days (rolling window)
SELECT d.name, 
       AVG(dp.score) as avg_score,
       SUM(dp.harsh_braking_events) as total_harsh_braking
FROM drivers d
JOIN driver_performance dp ON d.id = dp.driver_id
WHERE dp.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY d.name
ORDER BY avg_score ASC
LIMIT 5;

-- Vehicles currently overdue (changes daily!)
SELECT license_plate, make, model,
       CURRENT_DATE - next_service_due as days_overdue
FROM vehicles
WHERE next_service_due < CURRENT_DATE
ORDER BY days_overdue DESC;

-- Telemetry from today (yes, TODAY!)
SELECT v.license_plate, t.timestamp, t.speed, t.fuel_level
FROM telemetry t
JOIN vehicles v ON t.vehicle_id = v.id
WHERE DATE(t.timestamp) = CURRENT_DATE
ORDER BY t.timestamp DESC
LIMIT 10;
```

---

## Keeping Data Fresh (Optional)

### Option 1: Run Seed Script Periodically
```bash
# Every few weeks, regenerate with fresh dates
python database/seed_data.py --reset --inject-events
```
**Pro:** Fresh data with new patterns  
**Con:** Loses any custom changes

### Option 2: Add Daily Activity
```bash
# Add just today's activity (keeps existing data)
python database/add_daily_activity.py
```
**Pro:** Incremental updates, keeps history  
**Con:** Requires regular execution

### Option 3: Do Nothing!
The rolling time windows mean the data stays relevant automatically. You only need to regenerate if:
- You haven't used it in 3+ months
- You want completely different patterns
- You're recording a demo video

---

## Commands Reference

### Initial Setup
```bash
# Full setup with recent events (recommended)
python database/seed_data.py --reset --inject-events

# Just base data (no recent events)
python database/seed_data.py --reset

# Add events to existing data
python database/inject_recent_events.py
```

### Ongoing Updates
```bash
# Add today's activity
python database/add_daily_activity.py

# Add activity for specific date
python database/add_daily_activity.py --date 2025-10-05

# Verify data
python database/test_connection.py
```

### Data Management
```bash
# Clear and regenerate everything
python database/seed_data.py --reset --inject-events

# Just inject new events (keeps existing data)
python database/inject_recent_events.py
```

---

## What Your AI Agent Will Highlight

With the injected recent events, your daily digest will show things like:

```
FleetFix Daily Digest - October 3, 2025

CRITICAL ITEMS (3)
• Vehicle KC-7392: New critical fault code P0301 detected yesterday
  → Cylinder 1 misfire - schedule diagnostic immediately
  Impact: Vehicle downtime risk, potential $500-2000 repair
  
• Vehicle KC-1847: Now 5 days overdue for maintenance
  → Risk of breakdown increasing daily
  Impact: 3x higher breakdown probability
  
• Driver Mike Chen: Performance score dropped to 45 (usual: 82)
  → 15 harsh braking events yesterday vs. usual 2-3
  Impact: Safety risk, increased vehicle wear

⚠️  WARNINGS (4)  
• Fleet fuel efficiency down 8% this week
  → 5 vehicles showing unusual consumption patterns
  Impact: ~$200/week in excess fuel costs
  
• Driver speeding incidents: 12 events today (Sarah Johnson)
  → Highest daily count in 90 days
  
• 2 additional vehicles due for maintenance within 7 days
  
• Warning fault code P0420 on vehicle KC-9284

✅ POSITIVE TRENDS (2)
• Driver James Smith: 5-day streak of 95+ scores
  → Best performance in fleet this month
  
• Vehicle KC-4729: Completed maintenance, returned to service
  → Back to full fleet capacity
```

---

## Data Characteristics

**Realistic Patterns:**
- ✓ Telemetry timestamps through current date/time
- ✓ Performance records through today
- ✓ Older vehicles have higher mileage and more issues
- ✓ Some drivers are consistently better/worse
- ✓ Fuel levels decrease throughout each day
- ✓ GPS coordinates centered around Kansas City

**Intentional Recent Events (for AI insights):**
- ✓ Critical fault codes from yesterday
- ✓ Driver performance drop over last 3 days
- ✓ Vehicles overdue for maintenance
- ✓ Unusual fuel consumption yesterday
- ✓ Speeding incidents today
- ✓ Fleet-wide efficiency trends

**This gives your AI agent compelling material to work with!**

---

## Configuration Options

Edit `seed_data.py` to customize data volume:

```python
# Line 19-22: Adjust data volume
NUM_DRIVERS = 25              # Number of drivers
NUM_VEHICLES = 30             # Number of vehicles
HISTORICAL_MONTHS = 9         # Months of history (ends today)
TELEMETRY_READINGS_PER_DAY = 48  # Readings per day
```

**For faster generation:**
```python
HISTORICAL_MONTHS = 3         # 3 months instead of 9
TELEMETRY_READINGS_PER_DAY = 24  # Every hour instead of 30 min
```

**This reduces generation time from ~3 minutes to ~1 minute**

---# Phase 1: Database Foundation ✓ (with Rolling Time Windows)

This directory contains the FleetFix database implementation with **dynamic rolling time windows** - data is always relative to the current date, making the database feel "live" even though it's seeded.

## Key Innovation: Rolling Time Windows

Unlike typical static demo databases, this implementation uses **relative timestamps**:
- Historical data spans from **9 months ago → TODAY**
- "Yesterday's events" are always relative to the current date
- "Last 7 days" queries return rolling windows
- Data automatically "ages forward" with time

**Result:** Your AI dashboard will show fresh, relevant insights every time you demo it!

## File Structure

```
backend/
├── database/
│   ├── schema.sql                # PostgreSQL database schema
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── config.py                 # Database configuration
│   ├── seed_data.py              # Base data with rolling dates ⭐
│   ├── inject_recent_events.py  # Recent compelling events ⭐
│   ├── add_daily_activity.py    # Optional daily updates ⭐
│   └── test_connection.py        # Verification script
├── requirements.txt
├── .env.example
└── SETUP.md
```

⭐ = New dynamic data scripts

## Quick Start (10 Minutes)

### 1. Install PostgreSQL
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database
```bash
psql -U postgres
```
```sql
CREATE DATABASE fleetfix;
CREATE USER fleetfix_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fleetfix TO fleetfix_user;
\q
```

### 3. Set Up Python Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 5. Generate Data with Recent Events
```bash
# Create schema, generate base data, AND inject recent interesting events
cd database
python seed_data.py --reset --inject-events
```

**Expected output:**
```
FleetFix Data Generator (Rolling Time Windows)
Current date: 2025-10-03
Data will span: 2025-01-03 to 2025-10-03

Generating drivers...
Created 25 drivers
...
Injecting recent interesting events...
  Event 1: New critical fault code (yesterday)
  Event 2: Driver performance drop (last 3 days)
  Event 3: Vehicle overdue for maintenance
  ...
✓ Injected 100+ recent events
```

### 6. Verify Installation
```bash
python test_connection.py
```

Should show:
```
✓ Connected to PostgreSQL
✓ All tests passed! Your database is ready.
```

## What Gets Created

### Base Data (Rolling Time Windows)
| Table | Records | Time Span |
|-------|---------|-----------|
| **drivers** | 25 | Hired 6mo - 5yrs ago |
| **vehicles** | 30 | Purchased based on year |
| **maintenance_records** | ~200 | Throughout vehicle lifetime → today |
| **telemetry** | ~130,000 | **9 months ago → TODAY** ⭐ |
| **driver_performance** | ~6,000 | **9 months ago → TODAY** ⭐ |
| **fault_codes** | ~50 | 30+ days ago (resolved) |

### Recent Events (Injected with --inject-events)
| Event Type | Count | Timeframe |
|------------|-------|-----------|
| **Critical fault codes** | 1-2 | Yesterday |
| **Driver performance drops** | 1 driver, 3 days | Last 3 days |
| **Overdue maintenance** | 2-3 vehicles | Today |
| **Fuel consumption anomalies** | 1 vehicle | Yesterday |
| **Speeding incidents** | 1 driver | Today |
| **Warning fault codes** | 1-2 | Yesterday |
| **Fleet trends** | 5 vehicles | Last 3 days |
| **Excellent performance** | 1 driver | Last 5 days |
| **Completed maintenance** | 1 vehicle | Yesterday |

**Total recent events:** 100+ compelling data points for AI to analyze!

### Data Characteristics

**Realistic Patterns:**
- ✓ Older vehicles have higher mileage and more issues
- ✓ Some drivers are consistently better/worse performers
- ✓ 15% of vehicles are overdue for maintenance
- ✓ Fuel levels decrease throughout the day
- ✓ GPS coordinates centered around Kansas City
- ✓ Service costs vary by type (oil change vs engine repair)

**Intentional Anomalies:**
- ⚠️ 2-3 vehicles overdue for maintenance by 20+ days
- ⚠️ A few drivers with declining performance scores
- ⚠️ Several unresolved critical fault codes
- ⚠️ Some vehicles with high downtime

These anomalies make the AI agent's insights more interesting!

## Database Schema Overview

```
┌─────────────────────┐
│     drivers         │
├─────────────────────┤
│ id (PK)             │
│ name                │
│ license_number      │
│ hire_date           │
│ status              │
└─────────┬───────────┘
          │
          │ 1:N
          │
┌─────────▼───────────┐         ┌──────────────────┐
│ driver_performance  │         │    vehicles      │
├─────────────────────┤         ├──────────────────┤
│ id (PK)             │         │ id (PK)          │
│ driver_id (FK)      │         │ make, model      │
│ vehicle_id (FK)     │◄────────┤ year, vin        │
│ date                │   N:1   │ current_mileage  │
│ score               │         │ next_service_due │
│ harsh_braking       │         └────────┬─────────┘
│ miles_driven        │                  │
└─────────────────────┘                  │ 1:N
                                         │
         ┌───────────────────────────────┼─────────────────┐
         │                               │                 │
         │ 1:N                           │ 1:N             │ 1:N
         │                               │                 │
┌────────▼──────────┐      ┌─────────────▼────┐   ┌───────▼─────────┐
│   telemetry       │      │ maintenance_recs │   │  fault_codes    │
├───────────────────┤      ├──────────────────┤   ├─────────────────┤
│ id (PK)           │      │ id (PK)          │   │ id (PK)         │
│ vehicle_id (FK)   │      │ vehicle_id (FK)  │   │ vehicle_id (FK) │
│ timestamp         │      │ service_date     │   │ code            │
│ gps_lat, gps_lon  │      │ service_type     │   │ severity        │
│ speed, fuel_level │      │ cost             │   │ resolved        │
└───────────────────┘      └──────────────────┘   └─────────────────┘
```

## Sample Queries to Test

Try these queries in psql to explore the data:

```sql
-- Connect to database
psql -U fleetfix_user -d fleetfix

-- Vehicles overdue for maintenance
SELECT make, model, license_plate, 
       CURRENT_DATE - next_service_due as days_overdue
FROM vehicles 
WHERE next_service_due < CURRENT_DATE
ORDER BY days_overdue DESC;

-- Driver performance leaderboard (last 30 days)
SELECT d.name, 
       ROUND(AVG(dp.score)) as avg_score,
       SUM(dp.harsh_braking_events) as total_harsh_braking,
       SUM(dp.miles_driven) as total_miles
FROM drivers d
JOIN driver_performance dp ON d.id = dp.driver_id
WHERE dp.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.name
ORDER BY avg_score DESC
LIMIT 10;

-- Active critical fault codes
SELECT v.license_plate, v.make, v.model,
       fc.code, fc.description, fc.timestamp
FROM vehicles v
JOIN fault_codes fc ON v.id = fc.vehicle_id
WHERE fc.resolved = FALSE 
  AND fc.severity = 'critical'
ORDER BY fc.timestamp DESC;

-- Fleet utilization (avg miles per vehicle per day)
SELECT v.license_plate,
       AVG(dp.miles_driven) as avg_daily_miles,
       AVG(dp.hours_driven) as avg_daily_hours
FROM vehicles v
JOIN driver_performance dp ON v.id = dp.vehicle_id
WHERE dp.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY v.license_plate
ORDER BY avg_daily_miles DESC;

-- Maintenance costs by vehicle
SELECT v.license_plate, v.make, v.model,
       COUNT(mr.id) as service_count,
       SUM(mr.cost) as total_cost,
       AVG(mr.cost) as avg_cost
FROM vehicles v
JOIN maintenance_records mr ON v.id = mr.vehicle_id
GROUP BY v.license_plate, v.make, v.model
ORDER BY total_cost DESC;
```

## Configuration Options

Edit `seed_data.py` to customize data generation:

```python
# Line 19-22: Adjust data volume
NUM_DRIVERS = 25              # Number of drivers
NUM_VEHICLES = 30             # Number of vehicles
HISTORICAL_MONTHS = 9         # Months of history
TELEMETRY_READINGS_PER_DAY = 48  # Readings per day (every 30 min)
```

**For faster generation:**
```python
HISTORICAL_MONTHS = 3         # 3 months instead of 9
TELEMETRY_READINGS_PER_DAY = 24  # Every hour instead of 30 min
```

## Troubleshooting

### "Could not connect to server"
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Start PostgreSQL
brew services start postgresql@15     # macOS
sudo systemctl start postgresql       # Linux
```

### "Permission denied for database"
```sql
-- Connect as postgres superuser
psql -U postgres

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE fleetfix TO fleetfix_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fleetfix_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fleetfix_user;
```

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Data generation is slow
This is normal! Generating ~130k telemetry records takes 2-3 minutes. To speed up:
1. Reduce `HISTORICAL_MONTHS` to 3
2. Reduce `TELEMETRY_READINGS_PER_DAY` to 24
3. Reduce `NUM_VEHICLES` to 20

## Next Steps

Once your database is set up and verified:

1. **Phase 1 Complete!** You have a working database with realistic data
2. **Phase 2**: Build the AI Agent (text-to-SQL conversion)
3. **Phase 3**: Create the visualization service
4. **Phase 4**: Build the dashboard frontend

## Notes

- **Database size**: ~150 MB with full data
- **Generation time**: 2-3 minutes on modern hardware
- **PostgreSQL version**: Tested on PostgreSQL 15+
- **Python version**: Requires Python 3.9+

## Security Notes

- Change default passwords in production
- Never commit `.env` file to git (it's in `.gitignore`)
- Use environment-specific credentials
- Implement proper access controls for production deployment

---

**Questions?** See the main project README or SETUP.md for detailed instructions.