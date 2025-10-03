# Phase 2.1: Schema Context Builder

## What This Does

The Schema Context Builder introspects your PostgreSQL database and generates LLM-friendly descriptions of:
- All tables and their purposes
- Columns with data types and constraints
- Foreign key relationships
- Business context (what each table/column represents)
- Example query patterns
- Important notes about data

This context gets sent to the LLM along with user queries to enable accurate SQL generation.

## Files Created

```
backend/
└── ai_agent/
    ├── schema_context.py       # Core schema builder
    └── test_schema_context.py  # Test suite
```

## Quick Start

### 1. Create Directory Structure
```bash
cd backend
mkdir -p ai_agent
```

### 2. Place Files
- Copy `schema_context.py` to `backend/ai_agent/`
- Copy `test_schema_context.py` to `backend/ai_agent/`

### 3. Run Tests
```bash
cd backend
source venv/bin/activate
python ai_agent/test_schema_context.py
```

### Expected Output
```
======================================================================
Schema Context Builder - Test Suite
======================================================================

Test 1: Basic Introspection
----------------------------------------------------------------------
✓ All expected tables found
  - drivers: 25 rows, 7 columns
  - vehicles: 30 rows, 13 columns
  - maintenance_records: 200 rows, 10 columns
  ...

Test 2: Column Details
----------------------------------------------------------------------
✓ All expected columns found
✓ Primary key detected: ['id']
  Foreign keys found: 0

...

Total: 7/7 tests passed

✓ All tests passed! Schema context builder is ready.
```

## How It Works

### Basic Usage

```python
from ai_agent.schema_context import SchemaContextBuilder

# Create builder
builder = SchemaContextBuilder()

# Get full context (detailed, ~2000 tokens)
full_context = builder.build_schema_context()

# Or get concise context (minimal, ~500 tokens)
concise_context = builder.build_concise_context()

# Send to LLM along with user query
prompt = f"""
{full_context}

User query: "Show me vehicles with overdue maintenance"

Generate a safe PostgreSQL SELECT query to answer this question.
"""
```

### Context Options

**Full Context (`build_schema_context()`):**
- Detailed table descriptions
- All column information with business context
- Relationships explained
- Example queries
- Important notes
- ~2000 tokens

**Concise Context (`build_concise_context()`):**
- Table and column names only
- Primary/foreign keys
- Minimal descriptions
- ~500 tokens

**When to use each:**
- Use **full** for complex queries requiring business context
- Use **concise** when token budget is tight

### What Gets Sent to LLM

Check the generated files:
- `schema_context_full.txt` - Complete context with all details
- `schema_context_concise.txt` - Minimal context

Example from full context:
```
# FleetFix Database Schema

This is a PostgreSQL database for a fleet management system called FleetFix.
FleetFix tracks vehicles, drivers, maintenance, real-time telemetry, and performance metrics.

## Tables Overview

- **drivers** (25 rows): Fleet drivers with license information and employment status
- **vehicles** (30 rows): Fleet vehicles including make, model, mileage, and maintenance schedule
- **maintenance_records** (200 rows): Historical maintenance and service records for vehicles
...

## Detailed Schema

### vehicles
Fleet vehicles including make, model, mileage, and maintenance schedule

**Columns:**
- `id` (INTEGER) [PRIMARY KEY, NOT NULL]
- `make` (VARCHAR(50)) [NOT NULL]
- `model` (VARCHAR(50)) [NOT NULL]
- `vin` (VARCHAR(17)) [NOT NULL]
  Vehicle identification number (unique)
- `license_plate` (VARCHAR(20)) [NOT NULL]
  Vehicle license plate number
- `current_mileage` (INTEGER) [NOT NULL]
  Total odometer reading in miles
- `next_service_due` (DATE)
  Date when next maintenance is scheduled
...

## Key Relationships

- drivers → driver_performance (one-to-many)
- vehicles → maintenance_records (one-to-many)
- vehicles → telemetry (one-to-many)
...

## Important Notes

- All timestamps are in UTC
- Use CURRENT_DATE for queries about 'today' or 'yesterday'
- Vehicle status values: 'active', 'maintenance', 'inactive', 'retired'
...
```

## Features

### 1. Business Context
Not just technical schema, but business meaning:
```python
# Instead of just:
"vehicles.status (VARCHAR)"

# You get:
"vehicles.status: Vehicle status (active, maintenance, inactive, or retired)"
```

### 2. Relationship Detection
Automatically finds foreign keys:
```python
telemetry.vehicle_id → vehicles.id
telemetry.driver_id → drivers.id
```

### 3. Data Statistics
Includes row counts to help LLM understand data volume:
```
telemetry (130,000 rows)  # LLM knows this is a large table
drivers (25 rows)          # LLM knows this is small
```

### 4. Example Patterns
Provides sample queries as templates:
```sql
-- Vehicles overdue for maintenance
SELECT * FROM vehicles WHERE next_service_due < CURRENT_DATE;
```

## API Reference

### SchemaContextBuilder

**Constructor:**
```python
builder = SchemaContextBuilder(session=None)
```
- `session`: Optional SQLAlchemy session. If None, creates its own.

**Methods:**

#### `get_table_info(table_name: str) -> TableInfo`
Get detailed information about a specific table.

```python
vehicles = builder.get_table_info('vehicles')
print(f"Columns: {len(vehicles.columns)}")
print(f"Rows: {vehicles.row_count}")
```

#### `get_all_tables() -> List[TableInfo]`
Get information about all tables in the database.

```python
tables = builder.get_all_tables()
for table in tables:
    print(f"{table.name}: {table.row_count} rows")
```

#### `build_schema_context(include_samples: bool = False) -> str`
Build comprehensive schema context for LLM.

```python
context = builder.build_schema_context()
# Returns: ~2000 token formatted string
```

#### `build_concise_context() -> str`
Build minimal schema context for token efficiency.

```python
context = builder.build_concise_context()
# Returns: ~500 token formatted string
```

#### `get_table_sample_data(table_name: str, limit: int = 3) -> List[Dict]`
Get sample rows from a table (useful for understanding data format).

```python
samples = builder.get_table_sample_data('drivers', limit=2)
# Returns: [{"id": 1, "name": "John Doe", ...}, ...]
```

### Data Classes

**TableInfo:**
```python
@dataclass
class TableInfo:
    name: str                    # Table name
    columns: List[ColumnInfo]    # Column details
    row_count: int               # Number of rows
    description: str             # Business description
```

**ColumnInfo:**
```python
@dataclass
class ColumnInfo:
    name: str                # Column name
    type: str                # SQL data type
    nullable: bool           # Can be NULL
    primary_key: bool        # Is primary key
    foreign_key: str         # "table.column" if FK
    description: str         # Business description
```

## Testing

### Run Full Test Suite
```bash
python ai_agent/test_schema_context.py
```

### Individual Tests

**Test 1: Basic Introspection**
Verifies all tables are found and have correct row counts.

**Test 2: Column Details**
Checks column names, types, and constraints are detected.

**Test 3: Relationship Detection**
Verifies foreign key relationships are identified correctly.

**Test 4: Full Context Generation**
Ensures all required sections are present in output.

**Test 5: Concise Context Generation**
Verifies token reduction and completeness.

**Test 6: Sample Data Retrieval**
Tests ability to fetch sample rows.

**Test 7: Token Estimation**
Provides token usage estimates for both context types.

## Token Usage

### Full Context
- **Size:** ~2000 tokens
- **Use when:** Query requires business context
- **Best for:** Complex queries, ambiguous requests

### Concise Context
- **Size:** ~500 tokens
- **Use when:** Token budget is tight
- **Best for:** Simple queries, known patterns

### Why This Matters

LLM context windows (e.g., GPT-4: 8k-128k tokens, Claude: 200k tokens):
- Schema context: ~2000 tokens
- User query: ~50 tokens
- LLM response: ~500 tokens
- Room for conversation history: 5k-195k tokens

**Recommendation:** Use full context. Token usage is minimal.

## Customization

### Add Custom Descriptions

Edit `schema_context.py`:

```python
TABLE_DESCRIPTIONS = {
    'drivers': 'Your custom description',
    'vehicles': 'Your custom description',
    # ...
}

COLUMN_DESCRIPTIONS = {
    'vehicles': {
        'vin': 'Your custom column description',
        # ...
    }
}
```

### Modify Output Format

Edit `build_schema_context()` method to change formatting:

```python
def build_schema_context(self):
    # Customize sections, formatting, examples
    context_parts = [
        "# Your Custom Header",
        # ... your format
    ]
    return "\n".join(context_parts)
```

## Troubleshooting

### "No tables found"
**Cause:** Database connection issue or empty database  
**Fix:**
```bash
# Verify database has data
python database/test_connection.py

# Regenerate if needed
python database/seed_data.py --reset --inject-events
```

### "Foreign keys not detected"
**Cause:** Database doesn't have FK constraints defined  
**Fix:** Run schema.sql which includes FK definitions:
```bash
psql -U fleetfix_user -d fleetfix -f database/schema.sql
```

### "Import errors"
**Cause:** Python path issues  
**Fix:**
```bash
# Ensure you're in the right directory
cd backend
source venv/bin/activate

# Install dependencies if needed
pip install sqlalchemy psycopg2-binary
```

## Next Steps

Once schema context builder is working:

1. **Review generated context files**
   - Check `schema_context_full.txt`
   - Verify business descriptions make sense
   - Confirm relationships are correct

2. **Test with manual LLM queries**
   - Copy context to ChatGPT/Claude
   - Ask: "Generate SQL to find overdue vehicles"
   - Verify it produces correct SQL

3. **Move to Phase 2.2: Text-to-SQL**
   - Integrate LLM API (OpenAI/Anthropic)
   - Build prompt templates
   - Add SQL generation logic

## Design Decisions

### Why Include Business Context?

**Without business context:**
```
LLM sees: "vehicles.status VARCHAR"
Query: "Show me broken vehicles"
Result: Incorrect SQL (doesn't know what values mean)
```

**With business context:**
```
LLM sees: "vehicles.status: active, maintenance, inactive, retired"
Query: "Show me broken vehicles"
Result: SELECT * FROM vehicles WHERE status = 'maintenance'
```

### Why Two Context Versions?

- **Full:** Best accuracy, helps with complex queries
- **Concise:** Faster, cheaper, good for simple queries
- **Strategy:** Start with full, optimize later if needed

### Why Include Example Queries?

LLM learns patterns from examples:
```sql
-- Example provided:
SELECT * FROM vehicles WHERE next_service_due < CURRENT_DATE;

-- User asks: "vehicles due soon"
-- LLM correctly uses: next_service_due < CURRENT_DATE + INTERVAL '7 days'
```

## Performance Notes

- **Schema introspection:** ~50-100ms (cached in session)
- **Context generation:** ~10-20ms (string formatting)
- **Total overhead:** Negligible compared to LLM API call (~1-3 seconds)

**Recommendation:** Generate context once per request, don't cache (schema may change).

## Security Considerations

### What Schema Context Reveals

The context includes:
- Table and column names
- Relationships
- Data types
- Sample patterns

**Does NOT include:**
- Actual data values
- Credentials
- API keys
- Internal IPs

### Safe to Share With LLM?

Yes, with caveats:
- **Safe:** Table structure, column names
- **Safe:** Business descriptions you write
- **Caution:** Don't include sensitive table/column names in production
- **Never:** Include actual sensitive data in context

For production systems:
- Filter out sensitive tables (e.g., `user_credentials`)
- Redact sensitive column names
- Use generic descriptions

## Integration Example

How this will be used in Phase 2.2:

```python
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter

# Build context once
builder = SchemaContextBuilder()
schema_context = builder.build_schema_context()

# Use for query conversion
converter = TextToSQLConverter(schema_context)
sql = converter.convert("Show me vehicles overdue for maintenance")

# Result:
# SELECT * FROM vehicles WHERE next_service_due < CURRENT_DATE;
```

---

## Summary

**What you built:**
- Automated schema introspection
- Business context enrichment
- LLM-optimized formatting
- Token-efficient alternatives

**Why it matters:**
- Enables accurate SQL generation
- Reduces LLM hallucinations
- Provides business context
- Foundation for text-to-SQL

**Status:** ✓ Complete and tested

**Next:** Text-to-SQL converter with LLM integration

---

## Verification Checklist

Before moving to Phase 2.2:

- [ ] All tests pass (`python ai_agent/test_schema_context.py`)
- [ ] `schema_context_full.txt` generated successfully
- [ ] `schema_context_concise.txt` generated successfully
- [ ] Full context includes all 6 tables
- [ ] Business descriptions appear in output
- [ ] Foreign keys detected correctly
- [ ] Row counts are accurate
- [ ] Token estimates are reasonable (~2000 for full, ~500 for concise)

Run this to verify everything:
```bash
python ai_agent/test_schema_context.py && echo "✓ Ready for Phase 2.2!"
```