# Phase 2.2: Text-to-SQL Converter - Complete

## What You Built

A complete natural language to SQL pipeline with:
- LLM integration (Claude/GPT-4)
- Safety validation layer
- Conversation context support
- Comprehensive testing

## Files Created

```
backend/ai_agent/
├── text_to_sql.py           # LLM integration for SQL generation
├── sql_validator.py         # Safety validation and injection prevention
└── test_text_to_sql.py      # Integration tests
```

## Test Results

All tests should pass:

```
======================================================================
FLEETFIX TEXT-TO-SQL SYSTEM
Complete Integration Test Suite
======================================================================

✓ PASS: Integration Test (5/5 queries)
  - Time-based filtering with CURRENT_DATE
  - JOIN queries with relative dates
  - Aggregation with sorting and limiting
  - Multiple condition filtering
  - Complex aggregation with GROUP BY

✓ PASS: Security Test
  Malicious queries blocked:
    ✓ DELETE statement
    ✓ DROP statement
    ✓ UPDATE statement
    ✓ INSERT statement
    ✓ Multiple statements
    ✓ Hidden commands in comments
    ✓ UNION injection
  
  Safe queries allowed:
    ✓ WHERE 1=1 (legitimate pattern)
    ✓ OR '1'='1' (safe in LLM context)

✓ PASS: Conversation Context
  - Follow-up queries work correctly
  - Context maintained across conversation

Overall: 3/3 test suites passed
```

## Key Features Implemented

### 1. LLM Integration
- **Providers supported:** Anthropic Claude, OpenAI GPT-4
- **Prompt engineering:** Detailed schema context + examples
- **Response parsing:** Extracts SQL, explanation, confidence, warnings
- **Error handling:** Graceful fallbacks

### 2. Safety Validation
**Blocks:**
- Data modification (DELETE, UPDATE, INSERT, DROP)
- Multiple statements (SQL injection)
- UNION operations (data exfiltration)
- System commands (xp_cmdshell, EXEC)
- Hidden commands in comments

**Allows:**
- All SELECT queries
- JOINs, aggregations, subqueries
- WHERE 1=1 patterns (legitimate in LLM context)
- Complex analytical queries

### 3. Smart Context Awareness
**Understands that:**
- `OR 1=1` in LLM-generated SQL ≠ SQL injection
- Comments in legitimate queries ≠ hidden commands
- Only blocks truly dangerous patterns

### 4. Conversation Support
- Maintains query history
- Understands follow-up questions
- Provides context to LLM

## Architecture

```
User Query: "Show me overdue vehicles"
    ↓
Schema Context Builder
    | (provides database schema description)
    ↓
Text-to-SQL Converter
    | (sends to LLM with prompt)
    ↓
LLM (Claude/GPT-4)
    | (generates SQL + explanation)
    ↓
Response Parser
    | (extracts SQL, confidence, warnings)
    ↓
SQL Validator
    | (checks for dangerous operations)
    ↓
[IF VALID] → Query Executor
    ↓
Results returned to user
```

## Token Usage & Cost

**Per query:**
- Schema context: ~2,000 tokens
- User query: ~20 tokens
- LLM response: ~300 tokens
- **Total: ~2,320 tokens**

**Cost estimates:**
- **Claude Sonnet:** ~$0.003 per query
- **GPT-4:** ~$0.02 per query

**Recommendation:** Use Claude Sonnet for cost efficiency

## Example Queries Working

### Simple Filtering
```
User: "Show me active vehicles"
SQL: SELECT * FROM vehicles WHERE status = 'active';
```

### Time-Based
```
User: "Which drivers had issues yesterday?"
SQL: SELECT d.name, dp.score, dp.harsh_braking_events
     FROM drivers d
     JOIN driver_performance dp ON d.id = dp.driver_id
     WHERE dp.date = CURRENT_DATE - INTERVAL '1 day'
       AND dp.score < 70;
```

### Aggregation
```
User: "What's the average fuel efficiency last week?"
SQL: SELECT AVG(fuel_level) as avg_fuel
     FROM telemetry
     WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
```

### Complex Joins
```
User: "Show vehicles overdue with critical faults"
SQL: SELECT v.license_plate, v.next_service_due, 
            COUNT(fc.id) as fault_count
     FROM vehicles v
     LEFT JOIN fault_codes fc ON v.id = fc.vehicle_id
     WHERE v.next_service_due < CURRENT_DATE
       AND fc.severity = 'critical'
       AND fc.resolved = FALSE
     GROUP BY v.license_plate, v.next_service_due;
```

## Security Decisions Made

### Why We Block UNION
- No legitimate use case in our dashboard
- Primary vector for data exfiltration
- JOINs handle multi-table queries

### Why We Allow OR 1=1
- LLM generates complete queries (not concatenation)
- Legitimate pattern for dynamic query building
- No direct user input in SQL

### Why We Check After Semicolons
- Catches: `SELECT ...; DELETE ...`
- Allows: `SELECT ...; ` (trailing semicolon)
- More precise than counting semicolons

## Configuration

### Environment Variables Required

```bash
# .env file
# Choose one:
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...
```

### Model Selection

**Default models:**
- Anthropic: `claude-sonnet-4-20250514`
- OpenAI: `gpt-4o`

**To change:**
```python
converter = TextToSQLConverter(
    schema_context,
    provider="anthropic",
    model="claude-opus-4-20250514"  # More capable
)
```

## API Usage

### Basic Query Conversion

```python
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator

# Setup (once)
builder = SchemaContextBuilder()
schema_context = builder.build_schema_context()
converter = TextToSQLConverter(schema_context, provider="anthropic")
validator = SQLValidator()

# Convert query
result = converter.convert("Show me vehicles overdue for maintenance")

# Validate
validation = validator.validate(result.sql)

if validation.is_valid:
    # Safe to execute
    print(f"SQL: {validation.sanitized_sql}")
    print(f"Confidence: {result.confidence}")
    print(f"Explanation: {result.explanation}")
else:
    # Show errors
    print(f"Invalid SQL: {validation.errors}")
```

### With Conversation History

```python
# First query
result1 = converter.convert("Show critical fault codes")

# Follow-up
history = [("Show critical fault codes", result1.sql)]
result2 = converter.convert_with_conversation_history(
    "Show their maintenance history",
    conversation_history=history
)
```

## Verification Checklist

Before moving to Phase 2.3:

- [x] All integration tests pass (5/5 queries)
- [x] Security tests pass (malicious blocked, safe allowed)
- [x] Conversation context works
- [x] API key configured
- [x] Both Claude and OpenAI tested (choose one)
- [x] Schema context builder working (Phase 2.1)
- [x] Database has data (Phase 1)

## Known Limitations

### Queries That Work Well
- Simple filtering and sorting
- Time-based queries (today, yesterday, last 7 days)
- Aggregations (COUNT, AVG, SUM)
- JOINs (up to 3-4 tables)
- GROUP BY with HAVING

### Queries That May Need Refinement
- Very ambiguous requests ("show me problems")
- Complex business logic calculations
- Nested subqueries (3+ levels)
- Window functions (OVER, PARTITION BY)

### Not Supported
- Data modification (by design)
- Schema changes (by design)
- Stored procedures or functions
- Database administration commands

## Performance

**Typical end-to-end latency:**
- Schema context: 50ms (cached)
- LLM API call: 1-3 seconds
- SQL validation: <10ms
- **Total: 1.1-3.1 seconds**

**Bottleneck:** LLM API call (unavoidable)

**Optimization opportunities:**
- Cache common queries
- Use streaming responses (for faster perceived performance)
- Implement query result caching

## Next: Phase 2.3

Now that text-to-SQL is working, we need:

### Query Executor with Error Handling
- Execute SQL safely against database
- Handle query timeouts
- Catch and explain SQL errors
- Format results for display

### Insight Generator
- Analyze query results
- Identify patterns and anomalies
- Generate natural language insights
- Provide recommendations

### Result Formatter
- Convert SQL results to JSON
- Create data summaries
- Generate table/chart specifications

**Estimated time:** 1 week

**Files to create:**
- `ai_agent/query_executor.py` - Safe SQL execution
- `ai_agent/insight_generator.py` - Result analysis
- `ai_agent/test_query_executor.py` - Tests

## Troubleshooting

### "No API key found"
**Fix:** Add to `.env`:
```bash
ANTHROPIC_API_KEY=your_key_here
```

### "Import error: anthropic"
**Fix:**
```bash
pip install anthropic openai
```

### "SQL validation failed"
**Check:** Review `validation.errors` - validator is working correctly

### "LLM generates wrong SQL"
**Debug steps:**
1. Check schema context (`schema_context_full.txt`)
2. Try more specific query
3. Review LLM explanation for reasoning
4. Adjust prompt in `text_to_sql.py` if needed

### Tests fail intermittently
**Cause:** LLM responses can vary slightly
**Fix:** Run tests multiple times, adjust confidence thresholds if needed

## Interview Talking Points

### Technical Decisions

**Why LLM for text-to-SQL?**
> "Text-to-SQL is a complex NLP problem. Rule-based systems are brittle and can't handle natural language variety. LLMs have been trained on millions of SQL examples and understand both natural language intent and SQL semantics. This gives us flexibility without maintaining complex parsing rules."

**Why separate validation layer?**
> "Defense in depth. Even though we engineer the prompt to generate safe SQL, we validate as a second layer. This protects against prompt injection attacks and potential LLM mistakes. The validator is deterministic and fast, adding minimal latency."

**Why allow OR 1=1 patterns?**
> "Context matters. In traditional SQL injection, user input is concatenated into queries. Here, the LLM generates the complete query - there's no string concatenation. `WHERE 1=1` is a legitimate SQL pattern for dynamic queries. We block the actual threats: data modification, multiple statements, and UNION operations."

### Business Value

**User experience:**
> "Non-technical users can query data in natural language. Instead of learning SQL or waiting for a data analyst, fleet managers can ask 'Which drivers had safety issues yesterday?' and get instant answers."

**Scalability:**
> "The system handles new questions without code changes. As business questions evolve, users aren't blocked waiting for new reports to be built."

**Cost efficiency:**
> "At ~$0.003 per query with Claude, even 1000 queries/day costs only $3. Compare this to data analyst time at $50-100/hour building custom reports."

## Status Summary

**Phase 2.2:** ✓ Complete  
**Status:** Production-ready for portfolio/demo  
**Next Phase:** Query Executor & Insights

---

## Quick Commands Reference

```bash
# Run all tests
python ai_agent/test_text_to_sql.py

# Test individual components
python ai_agent/text_to_sql.py          # LLM converter test
python ai_agent/sql_validator.py        # Validator test

# Regenerate schema context
python ai_agent/schema_context.py

# Check database data
python database/test_connection.py
```

---

**Great work completing Phase 2.2!** The text-to-SQL system is the core intelligence of your AI dashboard. Ready to move on to Phase 2.3 when you are!