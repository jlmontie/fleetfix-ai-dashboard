# Phase 3: FastAPI Backend & Dashboard

## What This Adds

REST API and web dashboard for your AI agent:
- **FastAPI Backend**: REST API endpoints
- **Simple Dashboard**: HTML/JavaScript test interface
- **API Documentation**: Auto-generated OpenAPI docs
- **Complete Integration**: AI agent accessible via HTTP

## Files Created

```
backend/
├── api/
│   ├── main.py              # FastAPI application
│   └── test_api.py          # API test suite
└── dashboard/
    └── dashboard.html       # Simple web interface
```

## Quick Start

### 1. Install Dependencies

Add to `requirements.txt`:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
```

Install:
```bash
pip install fastapi uvicorn
```

### 2. Create Directory Structure

```bash
cd backend
mkdir -p api dashboard
```

### 3. Copy Files

- `api/main.py` (from artifact)
- `api/test_api.py` (from artifact)
- `dashboard/dashboard.html` (from artifact)

### 4. Start API Server

```bash
cd backend
python api/main.py
```

Expected output:
```
==================================================
Starting FleetFix API Server
==================================================
API: http://localhost:8000
Docs: http://localhost:8000/docs
==================================================

Initializing AI components...
✓ Schema context loaded
✓ Text-to-SQL initialized (anthropic)
✓ SQL validator ready
✓ Query executor ready
✓ Insight generator ready
==================================================
FleetFix API Ready!
==================================================
```

### 5. Test API

In a new terminal:
```bash
python api/test_api.py
```

### 6. Open Dashboard

Open in browser:
```
backend/dashboard/dashboard.html
```

Or use a simple HTTP server:
```bash
cd backend/dashboard
python -m http.server 3000
```

Then visit: `http://localhost:3000/dashboard.html`

## API Endpoints

### GET /
Root endpoint with API info

### GET /health
Health check
```json
{
  "status": "healthy",
  "timestamp": "2025-10-03T10:30:00",
  "database": "connected",
  "ai_provider": "anthropic"
}
```

### POST /api/query
Execute natural language query

**Request:**
```json
{
  "query": "Show me vehicles overdue for maintenance",
  "include_insights": true,
  "max_rows": 100
}
```

**Response:**
```json
{
  "success": true,
  "query": "Show me vehicles overdue for maintenance",
  "sql": "SELECT license_plate, make, model...",
  "explanation": "This query finds vehicles...",
  "confidence": 0.95,
  "row_count": 3,
  "execution_time_ms": 45.2,
  "columns": ["license_plate", "make", "model", "days_overdue"],
  "rows": [
    {"license_plate": "KC-7392", "make": "Ford", "model": "Transit", "days_overdue": 15},
    ...
  ],
  "summary": "3 vehicles are overdue for maintenance",
  "insights": [
    {
      "type": "anomaly",
      "severity": "critical",
      "message": "Vehicle KC-7392 is critically overdue...",
      "confidence": 0.95
    }
  ],
  "recommendations": [
    "Schedule KC-7392 for immediate maintenance",
    ...
  ]
}
```

### GET /api/schema
Get database schema information

### GET /api/examples
Get example queries users can try

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show vehicles overdue for maintenance",
    "include_insights": true,
    "max_rows": 10
  }'
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "Show me vehicles overdue for maintenance",
        "include_insights": True,
        "max_rows": 10
    }
)

data = response.json()
print(f"Found {data['row_count']} results")
print(f"Summary: {data['summary']}")
```

### Using the Dashboard

1. Open `dashboard/dashboard.html` in browser
2. Type a question or click an example
3. Click "Ask"
4. View results, SQL, and insights

## API Documentation

FastAPI auto-generates interactive API docs:

**Swagger UI:** http://localhost:8000/docs
- Interactive API testing
- Request/response examples
- Try endpoints directly in browser

**ReDoc:** http://localhost:8000/redoc
- Alternative documentation view
- Better for reading/printing

## Dashboard Features

The simple HTML dashboard provides:

**Query Interface:**
- Text input for natural language questions
- Example query chips for quick access
- Enter key submit

**Results Display:**
- Summary of findings
- Generated SQL with syntax highlighting
- Data table (first 20 rows)
- Confidence score
- Execution time

**Insights:**
- Color-coded by severity (critical/warning/info)
- Typed insights (observation/pattern/anomaly/recommendation)
- Actionable recommendations

## Configuration

### Environment Variables

```bash
# .env file

# API Configuration
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://fleetfix_user:password@localhost:5432/fleetfix
```

### CORS Settings

By default, API allows requests from:
- `http://localhost:3000`

To add more origins:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com
```

## Error Handling

### API Errors

**400 Bad Request:**
- Invalid query format
- SQL validation failed
- Empty query

**422 Unprocessable Entity:**
- Invalid request schema
- Missing required fields

**500 Internal Server Error:**
- Query execution failed
- Database error
- LLM API error

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Dashboard Error Display

Errors show in red box with explanation:
```
Error: SQL generation failed: No API key found
```

## Performance

**API Latency:**
- Health check: <10ms
- Schema endpoint: ~50ms
- Query without insights: 1-3 seconds
- Query with insights: 3-6 seconds

**Bottlenecks:**
- LLM API calls (1-3 seconds each)
- Complex database queries (varies)

**Optimizations:**
- Cache schema context (done automatically)
- Limit result rows (configurable)
- Add request timeout (30 seconds default)

## Deployment Considerations

### For Local Development
Current setup works perfectly

### For Production

**Security:**
- [ ] Add authentication (JWT tokens)
- [ ] Implement rate limiting
- [ ] Use HTTPS
- [ ] Validate all inputs
- [ ] Add API key management

**Performance:**
- [ ] Add Redis caching
- [ ] Implement connection pooling
- [ ] Use async database queries
- [ ] Add request queue

**Monitoring:**
- [ ] Add logging (structured)
- [ ] Implement metrics (Prometheus)
- [ ] Error tracking (Sentry)
- [ ] Request tracing

**Infrastructure:**
- [ ] Use production ASGI server (gunicorn + uvicorn)
- [ ] Add reverse proxy (nginx)
- [ ] Container deployment (Docker)
- [ ] Cloud hosting (GCP Cloud Run, AWS ECS, etc.)

## Troubleshooting

### "Connection refused"
**Cause:** API server not running
**Fix:**
```bash
python api/main.py
```

### "CORS error" in browser
**Cause:** Dashboard origin not in CORS_ORIGINS
**Fix:** Add to .env:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### "No API key found"
**Cause:** LLM API key not set
**Fix:** Add to .env:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### API starts but queries fail
**Check:**
1. Database is running and has data
2. API key is valid
3. Check API logs for specific error

## Next Steps

### Immediate Improvements
- [ ] Add query history
- [ ] Save favorite queries
- [ ] Export results (CSV, JSON)
- [ ] Add dark mode

### Future Features
- [ ] Data visualization (charts)
- [ ] Daily digest endpoint
- [ ] Scheduled reports
- [ ] Multi-user support
- [ ] Dashboard customization

## Verification Checklist

- [ ] API server starts without errors
- [ ] Health endpoint returns 200
- [ ] Test script passes (6/6 tests)
- [ ] Dashboard loads in browser
- [ ] Can submit queries from dashboard
- [ ] Results display correctly
- [ ] Insights appear when available
- [ ] Error handling works

**Run to verify:**
```bash
# Terminal 1: Start API
python api/main.py

# Terminal 2: Test API
python api/test_api.py

# Terminal 3: Open dashboard
open dashboard/dashboard.html
```

## Status

**Phase 3:** Complete
**API:** Running and tested
**Dashboard:** Functional MVP
**Ready for:** Production enhancements or demo

---

**Congratulations!** You now have a complete AI-powered fleet management system with:
- Natural language query interface
- REST API backend
- Web dashboard
- Intelligent insights

Try it out and see your AI agent in action!