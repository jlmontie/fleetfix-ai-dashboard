# FleetFix Test Suite

Comprehensive pytest test suite for the FleetFix AI agent system.

## Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── pytest.ini                     # Pytest settings
├── test_database.py               # Database connection and data quality tests
├── test_schema_context.py         # Schema introspection tests
├── test_text_to_sql.py           # Text-to-SQL conversion tests
└── test_complete_pipeline.py     # End-to-end pipeline tests
```

## Setup

### 1. Install pytest and dependencies

```bash
pip install pytest pytest-cov pytest-timeout
```

### 2. Configure environment

Ensure your `.env` file has:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fleetfix
ANTHROPIC_API_KEY=your_key_here  # Or OPENAI_API_KEY
```

### 3. Verify database is seeded

```bash
python database/seed_data.py
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test file

```bash
pytest tests/test_database.py
pytest tests/test_schema_context.py
pytest tests/test_text_to_sql.py
pytest tests/test_complete_pipeline.py
```

### Run specific test class

```bash
pytest tests/test_database.py::TestDatabaseConnection
pytest tests/test_text_to_sql.py::TestSQLGeneration
```

### Run specific test

```bash
pytest tests/test_database.py::TestDatabaseConnection::test_connection
```

### Run tests by marker

```bash
# Run only fast tests (skip slow/integration tests)
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run only tests requiring API keys
pytest -m requires_api

# Run only database tests
pytest -m requires_db
```

### Verbose output

```bash
# Show detailed output
pytest -v

# Show even more detail (print statements, etc.)
pytest -vv -s

# Show local variables on failures
pytest -l
```

### Coverage reports

```bash
# Run with coverage
pytest --cov=ai_agent --cov=database --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=ai_agent --cov=database --cov-report=html
open htmlcov/index.html
```

### Parallel execution

```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Test Categories

### Database Tests (`test_database.py`)

Tests database connectivity, data quality, and relationships.

**Classes:**
- `TestDatabaseConnection` - Basic connectivity
- `TestDataQuality` - Data integrity checks
- `TestDataRelationships` - Foreign key validation
- `TestFleetStatistics` - Aggregation queries

**Run:**
```bash
pytest tests/test_database.py -v
```

### Schema Context Tests (`test_schema_context.py`)

Tests schema introspection and context generation.

**Classes:**
- `TestBasicIntrospection` - Table discovery
- `TestColumnDetails` - Column metadata
- `TestRelationships` - Foreign key detection
- `TestContextGeneration` - Context building
- `TestSampleData` - Sample data retrieval
- `TestTokenEstimation` - Token usage estimation

**Run:**
```bash
pytest tests/test_schema_context.py -v
```

### Text-to-SQL Tests (`test_text_to_sql.py`)

Tests natural language to SQL conversion.

**Classes:**
- `TestSQLGeneration` - Query generation
- `TestSQLExecution` - Query execution
- `TestSQLSecurity` - Injection prevention
- `TestConversationContext` - Multi-turn queries
- `TestSQLQuality` - Output quality

**Run:**
```bash
pytest tests/test_text_to_sql.py -v
```

**Note:** Requires API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)

### Complete Pipeline Tests (`test_complete_pipeline.py`)

Tests end-to-end pipeline: Query → SQL → Execution → Insights

**Classes:**
- `TestEndToEndPipeline` - Full pipeline flow
- `TestQueryExecutor` - Query execution
- `TestResultFormatter` - Result formatting
- `TestInsightGenerator` - Insight generation
- `TestPipelineErrorHandling` - Error cases
- `TestPipelinePerformance` - Performance checks
- `TestPipelineIntegration` - Integration scenarios

**Run:**
```bash
pytest tests/test_complete_pipeline.py -v
```

**Note:** Requires API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)

## Common Test Patterns

### Parametrized Tests

Many tests use `@pytest.mark.parametrize` to test multiple scenarios:

```python
@pytest.mark.parametrize("query,expected", [
    ("Show me vehicles", ["vehicles"]),
    ("Show me drivers", ["drivers"]),
])
def test_queries(query, expected):
    # Test code here
```

### Fixtures

Shared setup is done via fixtures in `conftest.py`:

```python
@pytest.fixture(scope="module")
def builder():
    return SchemaContextBuilder()
```

### Markers

Tests are marked for organization:

```python
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.requires_api
def test_expensive_operation():
    # Test code
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Setup database
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/fleetfix
        run: |
          python database/seed_data.py
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/fleetfix
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests fail with "No API key found"

Set either `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in your `.env` file.

To skip tests requiring API keys:
```bash
pytest -m "not requires_api"
```

### Tests fail with database connection errors

1. Check PostgreSQL is running: `pg_isadmin`
2. Verify DATABASE_URL in `.env`
3. Run seed script: `python database/seed_data.py`

### Import errors

Make sure you're running from the project root and the project structure is:
```
fleetfix/
├── ai_agent/
├── database/
├── tests/
└── .env
```

### Slow tests

Skip slow/integration tests:
```bash
pytest -m "not slow and not integration"
```

Or run in parallel:
```bash
pytest -n auto
```

## Best Practices

1. **Run tests before committing**
   ```bash
   pytest
   ```

2. **Check coverage regularly**
   ```bash
   pytest --cov --cov-report=term-missing
   ```

3. **Use markers to organize test runs**
   ```bash
   pytest -m "not requires_api"  # Skip API tests during dev
   ```

4. **Keep tests fast**
   - Use fixtures for expensive setup
   - Mock external services when possible
   - Use `scope="module"` for session-wide fixtures

5. **Write descriptive test names**
   ```python
   def test_vehicles_have_valid_mileage():  # Good
   def test_data():  # Bad
   ```

## Adding New Tests

1. Create test file: `test_yourfeature.py`
2. Use test classes to organize related tests
3. Add appropriate markers
4. Update this README with new test categories

Example:
```python
"""
Tests for your new feature
"""

import pytest

class TestYourFeature:
    """Test your feature description"""
    
    def test_basic_functionality(self):
        """Test basic feature works"""
        assert True
    
    @pytest.mark.slow
    def test_expensive_operation(self):
        """Test expensive operation"""
        # Expensive test code
```
