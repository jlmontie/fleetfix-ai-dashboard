# Phase 2.3: Query Executor & Insight Generator

## What This Adds

The final pieces of the AI agent:
- **Query Executor**: Safely executes SQL with timeout and error handling
- **Result Formatter**: Converts database results to readable formats
- **Insight Generator**: AI analyzes results and provides intelligent insights
- **Complete Pipeline**: End-to-end natural language query system

## Files Created

```
backend/ai_agent/
├── query_executor.py           # Safe SQL execution
├── insight_generator.py        # AI result analysis  
└── test_complete_pipeline.py   # Full integration test
```

## Complete Pipeline Flow

```
User: "Show me vehicles overdue for maintenance"
  ↓
Schema Context (database schema)
  ↓
Text-to-SQL (LLM generates SQL)
  ↓
SQL Validator (safety checks)
  ↓
Query Executor (runs SQL)
  ↓
Result Formatter (formats output)
  ↓
Insight Generator (AI analyzes)
  ↓
User receives: SQL + Results + Insights + Recommendations
```

## Setup

### 1. Copy Files

Place in `backend/ai_agent/`:
- `query_executor.py`
- `insight_generator.py`
- `test_complete_pipeline.py`

### 2. Run Tests

```bash
cd backend
source venv/bin/activate
python ai_agent/test_complete_pipeline.py
```

### 3. Try Interactive Demo

```bash
python ai_agent/test_complete_pipeline.py --demo
```

## Expected Output

```
======================================================================
COMPLETE PIPELINE TEST
Natural Language → SQL → Execution → Insights
======================================================================

LLM Provider: anthropic

1. Initializing components...
   ✓ Schema context loaded
   ✓ Text-to-SQL converter ready
   ✓ SQL validator ready
   ✓ Query executor ready
   ✓ Insight generator ready

======================================================================
Running Complete Pipeline Tests
======================================================================

Test 1: Show me vehicles that are overdue for maintenance
======================================================================

Step 1: Converting to SQL...
✓ SQL generated (confidence: 0.95)

Generated SQL:
SELECT license_plate, make, model, next_service_due,
       CURRENT_DATE - next_service_due as days_overdue
FROM vehicles
WHERE next_service_due < CURRENT_DATE
ORDER BY days_overdue DESC;

Explanation: This query finds vehicles where maintenance is past due...

Step 2: Validating SQL...
✓ SQL validation passed

Step 3: Executing query...
✓ Query executed successfully
  Rows returned: 3
  Execution time: 45.2ms

Query Results:
license_plate | make   | model     | next_service_due | days_overdue
KC-7392       | Ford   | Transit   | 2025-09-18       | 15
KC-1847       | Ram    | ProMaster | 2025-09-26       | 7
KC-9284       | Mercedes | Sprinter | 2025-09-28     | 5

Total: 3 rows (45.2ms)

Step 4: Generating insights...
✓ Insights generated

SUMMARY:
  3 vehicles are overdue for maintenance, with one critically overdue by 15 days

KEY FINDINGS:
  1. Vehicle KC-7392 (Ford Transit) is 15 days overdue - highest risk
  2. Two vehicles overdue by 5-7 days  
  3. All overdue vehicles are cargo vans with high mileage

INSIGHTS:

  ✗ [ANOMALY] critical
     Vehicle KC-7392 is critically overdue (15 days past due date). Risk of 
     breakdown is 3x higher than normal, potentially causing delivery delays...

  ⚠ [PATTERN] warning
     All overdue vehicles are cargo vans, suggesting these vehicles may need 
     more frequent maintenance schedules due to higher usage patterns...

RECOMMENDATIONS:
  1. Schedule KC-7392 for immediate maintenance (within 24 hours)
  2. Contact drivers of other 2 overdue vehicles to schedule within 3 days
  3. Review cargo van maintenance intervals - consider reducing from 5000 to 4000 miles

✓ Test 1 PASSED - Complete pipeline successful

[Tests 2-3...]

======================================================================
TEST SUMMARY
======================================================================
Total tests: 3
Passed: 3
Failed: 0
Success rate: 100.0%

======================================================================
✓ SUCCESS! Complete pipeline is fully functional!
======================================================================
```

## Components

### Query Executor

**Features:**
- Timeout protection (default 30 seconds)
- Error handling with user-friendly messages
- Result serialization (dates, decimals, etc.)
- Automatic LIMIT for large result sets
- Sample result fetching

**Usage:**
```python
from ai_agent.query_executor import QueryExecutor, ResultFormatter

executor = QueryExecutor(timeout_seconds=10)
result = executor.execute(sql)

if result.success:
    print(f"Found {result.row_count} rows")
    formatter = ResultFormatter()
    print(formatter.to_table_string(result))
else:
    print(f"Error: {result.error}")
```

### Insight Generator

**Generates:**
- Summary (one-sentence overview)
- Key findings (3-5 main points)
- Insights (observations, patterns, anomalies, recommendations)
- Actionable recommendations

**Insight Types:**
- **observation**: Basic fact about the data
- **pattern**: Trend or recurring theme
- **anomaly**: Unusual or concerning finding
- **recommendation**: Suggested action

**Severity Levels:**
- **info**: Informational
- **warning**: Needs attention
- **critical**: Urgent action required

**Usage:**
```python
from ai_agent.insight_generator import InsightGenerator

generator = InsightGenerator(provider="anthropic")
insights = generator.generate_insights(
    user_query="Show overdue vehicles",
    sql=sql_query,
    result=execution_result
)

print(insights.summary)
for insight in insights.insights:
    print(f"{insight.severity}: {insight.message}")
```

### Result Formatter

**Formats:**
- ASCII table (for terminal display)
- Summary statistics
- Column type inference

**Usage:**
```python
from ai_agent.query_executor import ResultFormatter

formatter = ResultFormatter()

# Table format
table = formatter.to_table_string(result, max_rows=20)

# Summary
summary = formatter.to_summary(result)
print(f"Rows: {summary['row_count']}")
print(f"Columns: {summary['columns']}")
```

## Interactive Demo

Run the interactive demo to test queries in real-time:

```bash
python ai_agent/test_complete_pipeline.py --demo
```

**Example session:**
```
Ask a question about your fleet: Show me drivers with poor performance
----------------------------------------------------------------------
🤖 Converting to SQL...
✓ SQL generated

Generated SQL:
SELECT d.name, AVG(dp.score) as avg_score
FROM drivers d
JOIN driver_performance dp ON d.id = dp.driver_id
WHERE dp.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.name
HAVING AVG(dp.score) < 70
ORDER BY avg_score ASC;

Confidence: 95%

🔍 Executing query...
✓ Found 2 results (67ms)

Results:
name        | avg_score
Mike Chen   | 52.3
Sarah Lee   | 64.8

💡 Generating insights...
2 drivers have consistently poor performance scores over the last 30 days

Recommendations:
  1. Schedule coaching sessions for Mike Chen (critically low score)
  2. Review driving patterns to identify specific improvement areas
  3. Consider vehicle reassignment if scores don't improve

----------------------------------------------------------------------
```

## Token Usage & Cost

**Per complete query:**
- Schema context: ~2,000 tokens
- SQL generation: ~300 tokens  
- Insight generation: ~500 tokens
- **Total: ~2,800 tokens**

**Cost (approximate):**
- **Claude Sonnet:** ~$0.004 per query
- **GPT-4:** ~$0.025 per query

**For 1000 queries/day:**
- Claude: ~$4/day ($120/month)
- GPT-4: ~$25/day ($750/month)

## Performance

**Typical end-to-end latency:**
1. SQL generation: 1-2 seconds
2. SQL validation: <10ms
3. Query execution: 50-500ms
4. Insight generation: 2-3 seconds
**Total: 3-6 seconds**

**Bottlenecks:**
- LLM API calls (unavoidable)
- Complex queries (database dependent)

**Optimizations:**
- Cache common queries
- Use result limits
- Parallel insight generation

## What Insights Look Like

### Example 1: Overdue Maintenance

**Query:** "Show vehicles overdue for maintenance"

**Insights:**
```
SUMMARY:
3 vehicles are overdue for maintenance, with one critically overdue by 15 days.

KEY FINDINGS:
1. Vehicle KC-7392 (Ford Transit) is 15 days overdue - highest risk
2. Two vehicles overdue by 5-7 days
3. All overdue vehicles are cargo vans with high mileage (40k+ miles)

INSIGHTS:
✗ [ANOMALY - critical] Vehicle KC-7392 is critically overdue (15 days past due date). 
   Risk of breakdown is 3x higher than normal, potentially causing delivery delays 
   and repair costs of $500-2000.

⚠ [PATTERN - warning] All overdue vehicles are cargo vans, suggesting these vehicles 
   may need more frequent maintenance schedules due to higher usage patterns.

RECOMMENDATIONS:
1. Schedule KC-7392 for immediate maintenance (within 24 hours)
2. Contact drivers of other 2 overdue vehicles to schedule within 3 days
3. Review cargo van maintenance intervals - consider reducing from 5000 to 4000 miles
```

### Example 2: Driver Performance

**Query:** "Which drivers had issues yesterday?"

**Insights:**
```
SUMMARY:
2 drivers had significantly poor performance yesterday with multiple safety events.

KEY FINDINGS:
1. Mike Chen had 15 harsh braking events (3x normal)
2. Sarah Johnson had 12 speeding incidents
3. Both drivers were operating cargo vans on the same route

INSIGHTS:
⚠ [ANOMALY - warning] Mike Chen's harsh braking is 3x his normal rate, suggesting 
   possible vehicle issues (brake problems) or unusual traffic conditions.

ℹ [PATTERN - info] Both drivers were on Route 35 yesterday, which has construction. 
   This may explain the unusual driving patterns.

RECOMMENDATIONS:
1. Inspect brake systems on both vehicles
2. Brief drivers on construction detours for Route 35
3. Monitor these drivers over next 3 days to confirm this was situational
```

## Error Handling

### Query Timeout
```
Error: Query timeout: Query took longer than 30 seconds
```
**Causes:** Complex query, large dataset, slow database
**Solutions:** Simplify query, add indexes, increase timeout

### Empty Results
```
No results found for this query

Recommendations:
- Check if the filters are correct
- Try broadening the search criteria
- Verify the data exists in the database
```

### SQL Syntax Error
```
Error: SQL syntax error at or near "WHER"
```
**Cause:** LLM generated invalid SQL (rare)
**Solution:** Retry query or rephrase

## Verification Checklist

Before considering Phase 2 complete:

- [ ] Query executor tests pass
- [ ] Insight generator tests pass
- [ ] Complete pipeline test passes (3/3)
- [ ] Interactive demo works
- [ ] Insights are relevant and actionable
- [ ] Error handling works correctly
- [ ] Results format properly

Run this to verify:
```bash
python ai_agent/test_complete_pipeline.py
```

## Next: Phase 3 - FastAPI & Dashboard

Now that the AI agent is complete, we'll build:

### FastAPI Endpoints
- `/api/query` - Natural language query endpoint
- `/api/daily-digest` - Generate daily insights
- `/api/health` - Health check

### Dashboard Integration
- Chat interface for queries
- Result visualization
- Insight display
- Daily digest view

**Estimated time:** 1-2 weeks

---

**Status:** Phase 2.3 Complete  
**AI Agent:** Fully functional  
**Ready for:** API and Dashboard development