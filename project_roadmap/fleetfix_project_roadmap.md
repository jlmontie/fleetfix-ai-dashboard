# FleetFix AI Dashboard - Complete Project Roadmap

## Executive Summary

**Project Goal:** Build an AI-powered business intelligence dashboard that adapts daily based on what's important in your data, with natural language querying and dynamic visualization generation.

**Timeline:** 8-10 weeks (evenings/weekends)  
**Outcome:** Portfolio flagship project that differentiates you from other candidates

---

## Why This Project Wins

### The Problem with Your Current IoT Project
- ❌ Niche domain (agricultural sensors) - not relatable
- ❌ Basic ML (linear regression) - doesn't showcase advanced skills
- ❌ Simulated data - lacks real-world credibility
- ❌ Missing analytical depth - no EDA, model comparison, or feature engineering
- ✅ Great deployment infrastructure (keep this approach!)

### Why FleetFix AI Dashboard is Superior
- ✅ **Universal relevance** - everyone understands vehicles and delivery
- ✅ **Cutting-edge tech** - LLM integration is hottest skill right now
- ✅ **Unique differentiator** - adaptive dashboard that changes daily
- ✅ **Full-stack showcase** - data engineering + ML + frontend + deployment
- ✅ **Clear business value** - every metric has dollar impact
- ✅ **Interview gold** - naturally leads to deep technical discussions

---

## Portfolio Strategy: What Hiring Managers Want

### Must-Haves for Data Science/Engineering Portfolios

1. **3-5 high-quality projects** (not 10+ half-finished ones)
2. **Diverse skill demonstration** (ML, data engineering, visualization, storytelling)
3. **Real-world problems** (avoid Titanic, Iris, Boston Housing)
4. **Clear business value** articulated in $ terms
5. **Professional GitHub profile** with pinned repos and profile README
6. **Proper project structure** with consistent organization
7. **Reproducible work** with clear setup instructions
8. **Visual results** - charts, dashboards, or live demos

### Your Recommended Portfolio Structure

**Project 1: FleetFix AI Dashboard (Flagship)** ⭐
- Showcases AI integration, full-stack skills, product thinking
- Most impressive and memorable
- Pin this at top of GitHub

**Project 2: Cloud ETL Data Pipeline**
- Streaming data with real-time processing
- Use interesting data source (social media, financial, IoT)
- Include data quality monitoring
- Show cost optimization

**Project 3: Revised ML Deployment Project**
- Keep your deployment infrastructure from IoT project
- But swap domain to something relatable:
  - Customer churn prediction API (B2B SaaS)
  - Retail demand forecasting API
  - Fraud detection API
- Add ML depth: model comparison, feature importance, error analysis
- Include business metrics: "Saves $X/month by preventing..."

---

## Current Starter Code Assessment

### What You Have

**bi-ai-agent Repository:**
- ✅ Clear architecture diagram
- ✅ Modern tech stack (React, TypeScript, FastAPI, Node.js)
- ✅ Well-defined roadmap
- ⚠️ Mostly placeholder/boilerplate code
- ⚠️ No actual AI agent implementation
- ⚠️ No database schema or connection code

**bi-ai-agent-example-business Repository:**
- ✅ **BRILLIANT business model choice** (FleetFix)
- ✅ Well-thought-out metrics with business value
- ✅ Example queries defined
- ⚠️ No actual database schema files
- ⚠️ No sample data generated
- ⚠️ No company documents created

### Strategic Changes Recommended

**Keep:**
- ✅ FleetFix business model
- ✅ Architecture approach (microservices)
- ✅ Tech stack choices
- ✅ Conceptual roadmap

**Simplify:**
- 🔄 Remove Node.js backend → Use Python FastAPI for everything
- 🔄 Single monorepo instead of multiple repos
- 🔄 Focus on 4-5 visualization types, not dozens
- 🔄 Support 20-30 queries really well, not every possible query

**Build from Scratch:**
- 🆕 Database schema and realistic sample data
- 🆕 AI agent implementation (text-to-SQL)
- 🆕 Visualization service (chart generation)
- 🆕 Actual dashboard UI

---

## Simplified Architecture

```
fleetfix-ai-dashboard/
├── backend/                    # Python FastAPI only
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   ├── query.py           # Natural language query endpoint
│   │   ├── visualize.py       # Chart generation endpoint
│   │   └── digest.py          # Daily insights endpoint
│   ├── ai_agent/
│   │   ├── schema_context.py  # DB schema → text description
│   │   ├── text_to_sql.py     # LLM integration for SQL generation
│   │   └── insight_generator.py # AI analysis of results
│   ├── visualizer/
│   │   ├── chart_selector.py  # Choose chart type
│   │   └── plotly_generator.py # Generate Plotly configs
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schema.sql         # Database schema
│   │   └── seed_data.py       # Sample data generator
│   └── requirements.txt
├── frontend/                   # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx  # Main dashboard with metrics
│   │   │   ├── Chat.tsx       # Chat interface
│   │   │   ├── MetricCard.tsx # KPI display
│   │   │   └── Chart.tsx      # Plotly wrapper
│   │   ├── api/
│   │   │   └── client.ts      # Backend API client
│   │   └── App.tsx
│   └── package.json
├── data/                       # Data generation scripts
│   ├── generate_vehicles.py
│   ├── generate_telemetry.py
│   ├── generate_maintenance.py
│   └── generate_drivers.py
├── company_docs/               # FleetFix business documents
│   ├── maintenance_procedures.md
│   ├── fault_code_reference.md
│   └── driver_handbook.md
├── docker-compose.yml          # One-command local setup
├── .env.example
└── README.md                   # Portfolio-quality documentation
```

---

## FleetFix Business Context

### Company Overview
- **Name:** FleetFix
- **Tagline:** "Keep Your Vehicles Moving. We'll Watch the Rest."
- **Industry:** Vehicle Fleet Monitoring + Maintenance Analytics
- **HQ:** Kansas City, Missouri
- **Founded:** 2019
- **Target Market:** Small-to-midsize delivery companies, plumbing/HVAC, mobile businesses

### Key Metrics That Matter

| Metric | Description | Business Impact |
|--------|-------------|-----------------|
| Avg. Miles per Vehicle/Day | Fleet utilization rate | Operational efficiency |
| Fuel Efficiency (MPG) | Consumption tracking | Cost control |
| Fault Codes Triggered | Mechanical health | Preventive maintenance |
| On-Time Delivery % | Service quality | Customer satisfaction |
| Vehicle Downtime (hrs) | Lost productivity | Revenue impact |
| Driver Score (0-100) | Behavior rating | Safety & efficiency |
| Maintenance Compliance % | Preventative care | Risk mitigation |
| Route Deviation | Efficiency measure | Cost optimization |

### Example User Queries
- "Show me vehicles with overdue maintenance"
- "Which drivers had harsh braking events this week?"
- "What's our fleet's average fuel efficiency trend?"
- "Alert me to any fault codes triggered today"
- "Which vehicles are most at risk of breakdown?"

---

## Detailed Build Plan

## Phase 1: Data Foundation (Week 1-2)
**Focus:** Get realistic data in place first

### Database Schema Design

**Tables Needed:**
1. **vehicles**
   - id, make, model, year, vin, license_plate, status, purchase_date, current_mileage
   
2. **maintenance_records**
   - id, vehicle_id, service_date, service_type, cost, mileage, next_service_due
   
3. **telemetry**
   - id, vehicle_id, timestamp, gps_lat, gps_lon, speed, fuel_level, engine_temp, odometer
   
4. **driver_performance**
   - id, driver_id, vehicle_id, date, harsh_braking_events, rapid_acceleration, idle_time, hours_driven, score
   
5. **fault_codes**
   - id, vehicle_id, timestamp, code, description, severity, resolved

6. **drivers**
   - id, name, license_number, hire_date, status

### Sample Data Generation Strategy

**Use Python + Faker library to create:**
- 20-30 vehicles (mix of vans, trucks, sedans)
- 6-12 months of historical data
- Realistic patterns:
  - Seasonal variations in usage
  - Wear patterns (older vehicles have more issues)
  - Driver behavior variations (some aggressive, some smooth)
  - Maintenance cycles (oil changes every 3-5k miles)
- Intentional anomalies:
  - 2-3 vehicles overdue for maintenance
  - 1-2 vehicles with declining performance
  - A few drivers with consistently poor scores

### Tasks
1. ✅ Write PostgreSQL schema SQL files
2. ✅ Create data generator script with realistic logic
3. ✅ Load data into local PostgreSQL
4. ✅ Write verification queries to check data quality
5. ✅ Document schema relationships

**Deliverable:** Working PostgreSQL database with 6 months of FleetFix data

---

## Phase 2: Basic AI Agent (Week 2-3)
**Focus:** Get text-to-SQL working reliably

### Core Functionality
1. Accept natural language query from user
2. Read database schema and build context
3. Send to LLM with structured prompt
4. Generate safe SQL (SELECT only)
5. Validate SQL syntax
6. Execute query and return results
7. Handle errors gracefully

### AI Agent Implementation

**Schema Context Builder:**
```
Read database schema → Generate text description:
"The database has the following tables:
- vehicles: Stores fleet vehicle information (make, model, year, mileage, status)
- maintenance_records: Tracks all service events (date, type, cost, next due date)
- telemetry: Real-time vehicle data (GPS, speed, fuel, engine temp)
- driver_performance: Daily driver metrics (harsh braking, acceleration, score)
- fault_codes: Diagnostic trouble codes (code, severity, timestamp)"
```

**Text-to-SQL Prompt Template:**
```
System: You are a SQL expert for FleetFix's fleet management database.

Schema: [detailed schema description]

Constraints:
- Generate SELECT queries ONLY (no DELETE, UPDATE, DROP, INSERT)
- Use proper JOINs when querying multiple tables
- Include appropriate WHERE clauses for filtering
- Add ORDER BY and LIMIT when relevant
- Return valid PostgreSQL syntax

User query: "{natural_language_query}"

Generate a safe SQL query to answer this question.
Return only the SQL query, no explanation.
```

### Tasks
1. ✅ Build FastAPI endpoint: `POST /api/query`
2. ✅ Implement schema context builder
3. ✅ Integrate OpenAI or Claude API
4. ✅ Add SQL validation (check for dangerous keywords)
5. ✅ Execute SQL and return JSON results
6. ✅ Implement error handling and logging
7. ✅ Test with 15-20 example queries

**Deliverable:** Working API that converts English → SQL → Results

---

## Phase 3: Visualization Layer (Week 3-4)
**Focus:** Make data visual

### Chart Type Selection Logic

**Decision Tree:**
- Time series data (timestamps) → Line chart
- Categories + single value → Bar chart
- Categories + multiple values → Grouped bar chart
- Two numerical columns → Scatter plot
- Geographic data (lat/lon) → Map
- Single metric → Big number card
- Tabular data → Table

### Visualization Service

**Endpoint:** `POST /api/visualize`

**Input:** Query results + column metadata
**Output:** Plotly JSON specification

### Tasks
1. ✅ Build FastAPI endpoint for visualization
2. ✅ Implement chart type selector
3. ✅ Create Plotly generators for:
   - Line charts (time series)
   - Bar charts (categorical)
   - Scatter plots (correlation)
   - Tables (detailed data)
   - Maps (geographic)
4. ✅ Add chart customization (titles, labels, colors)
5. ✅ Test with various query result formats

**Deliverable:** Service that generates chart configs from data

---

## Phase 4: Dashboard UI (Week 4-5)
**Focus:** User experience and polish

### Dashboard Layout

**Top Section: Today's Highlights** (dynamic, changes daily)
- 2-3 AI-generated insights
- Relevant auto-generated charts

**Middle Section: Key Metrics** (static grid)
- Fleet Utilization: Avg miles/vehicle/day
- Fuel Efficiency: 30-day trend
- Maintenance Compliance: % on schedule
- Driver Performance: Score distribution
- Vehicle Health: Red/Yellow/Green status counts
- Active Fault Codes: Count + severity breakdown

**Bottom Section: Chat Interface**
- Natural language input
- Message history
- Response with text + visualizations
- "Show SQL" toggle for transparency

### Frontend Components

**MetricCard.tsx:**
- Display single KPI
- Show trend indicator (up/down arrow)
- Color-coded by status

**Chart.tsx:**
- Wrapper for Plotly React
- Loading states
- Error handling

**Chat.tsx:**
- Message input
- Message history with role (user/assistant)
- Render text responses
- Render chart components
- SQL query display (collapsible)

**Dashboard.tsx:**
- Layout orchestration
- API calls to backend
- State management

### Tasks
1. ✅ Set up React + TypeScript + Tailwind project
2. ✅ Build MetricCard component
3. ✅ Build Chart component with Plotly
4. ✅ Build Chat interface
5. ✅ Create Dashboard layout
6. ✅ Connect to backend APIs
7. ✅ Implement loading states and error handling
8. ✅ Style with Tailwind (professional appearance)
9. ✅ Add responsive design for desktop

**Deliverable:** Working full-stack application

---

## Phase 5: Dynamic Intelligence (Week 5-6)
**Focus:** The revolutionary differentiator

### Daily Digest Feature

**What Makes This Unique:**
- Dashboard adapts daily based on what changed
- AI identifies what's important today
- Relevant visualizations auto-generated
- No manual configuration needed

### Implementation Approach

**Endpoint:** `GET /api/daily-digest`

**Logic:**
1. Query database for last 24 hours of changes:
   - New fault codes
   - Maintenance due within 7 days
   - Driver scores that dropped >10 points
   - Fuel efficiency changes >5%
   - Vehicles with high downtime
   
2. Send data to LLM with prompt:
```
Analyze this fleet data from the last 24 hours.
Identify the 2-3 most important issues requiring attention.
For each issue:
- Explain why it matters
- Provide actionable recommendation
- Suggest relevant visualization

Data:
{data_summary}
```

3. Generate insights list with priorities
4. Auto-create visualizations for each insight
5. Return structured response

### Tasks
1. ✅ Create daily digest endpoint
2. ✅ Implement change detection queries
3. ✅ Build insight generation prompts
4. ✅ Add visualization auto-generation
5. ✅ Add "Today's Highlights" section to dashboard
6. ✅ Implement refresh mechanism
7. ✅ Test with different data scenarios

**Deliverable:** Dashboard that adapts daily based on data changes

---

## Phase 6: Polish & Deploy (Week 6-7)
**Focus:** Portfolio readiness

### Documentation Requirements

**README Structure:**
1. **Hook:** "AI-powered fleet dashboard that tells you what matters today"
2. **Problem Statement:** FleetFix challenges (reactive not proactive, data overload)
3. **Solution Demo:** GIF showing chat interaction + adaptive dashboard
4. **Key Features:** (4-5 with screenshots)
   - Natural language queries
   - Adaptive daily insights
   - Dynamic visualization generation
   - Context-aware responses
5. **Architecture Diagram:** Your clean architecture
6. **Live Demo:** Link + credentials
7. **Tech Stack:** Brief tech overview
8. **Quick Start:** One-command setup instructions
9. **Example Queries:** 10-15 sample questions users can ask
10. **Future Enhancements:** What you'd build next

### Deployment Strategy

**Local Development:**
- Docker Compose setup (PostgreSQL + Backend + Frontend)
- One command: `docker-compose up`

**Cloud Deployment Options:**
- **Render** (easiest, free tier): Separate services for frontend/backend
- **Railway** (simple, affordable): Full stack deployment
- **GCP Cloud Run** (professional): Containerized deployment

**Choose Render or Railway for speed** - both have simple GitHub integration

### Demo Video Script (2 minutes)

**0:00-0:15** - Hook
"This is FleetFix AI Dashboard - it doesn't just show you data, it tells you what matters today."

**0:15-0:45** - Adaptive Intelligence Demo
Show dashboard loading → highlights section appears
"Every morning, the AI analyzes what changed and surfaces the most important issues."

**0:45-1:15** - Natural Language Demo
Type query: "Which vehicles need maintenance this week?"
Show response with table and chart
"Ask questions in plain English, get insights with visualizations."

**1:15-1:45** - Follow-up Query Demo
Type: "Show me their maintenance history"
Show how it understands context
"The AI remembers context and can drill deeper."

**1:45-2:00** - Close
"Built with FastAPI, React, and Claude AI. Full code on GitHub."

### Tasks
1. ✅ Write comprehensive README
2. ✅ Add architecture diagram
3. ✅ Create demo GIF/video
4. ✅ Set up Docker Compose
5. ✅ Deploy to cloud platform
6. ✅ Test deployment thoroughly
7. ✅ Add monitoring/logging
8. ✅ Write medium article (optional but recommended)

**Deliverable:** Portfolio-ready project with live demo

---

## Critical Success Factors

### Scope Control (What NOT to Build)

**Don't Try To:**
- ❌ Support every possible SQL query
- ❌ Build 20+ chart types
- ❌ Handle real-time streaming (pre-generate data)
- ❌ Implement user authentication (demo mode only)
- ❌ Support mobile (desktop browser only)
- ❌ Integrate multiple LLM providers
- ❌ Build custom UI components (use libraries)
- ❌ Optimize for scale (this is a demo)

**Focus On:**
- ✅ 20-30 common queries that work flawlessly
- ✅ 4-5 visualization types that look professional
- ✅ Reliability over features
- ✅ Clear documentation over complex features
- ✅ Working demo over perfect code
- ✅ One thing done excellently

### Technical Simplifications

**Database:**
- PostgreSQL locally (no cloud DB needed for demo)
- Simple schema (5-7 tables maximum)
- Pre-generated data (no real-time ingestion)

**AI:**
- OpenAI or Claude API (no custom models)
- Structured prompts (no fine-tuning)
- Response caching for common queries (save costs)

**Frontend:**
- React + Tailwind (looks professional)
- Plotly React for all charts (one library)
- No complex state management (React hooks sufficient)

**Deployment:**
- Docker Compose for local
- Render/Railway for cloud (free/cheap)
- Single region (no multi-region complexity)

### What Makes This Project Interview Gold

**Technical Depth:**
- AI/LLM integration (hottest skill)
- Database schema design
- API development
- Frontend development
- Deployment and DevOps

**Business Value:**
- Clear problem statement
- Measurable impact ($)
- Real-world relevance
- Domain expertise demonstration

**Conversation Starters:**
- "How did you handle hallucinated SQL?"
- "What was your prompt engineering process?"
- "How do you ensure query safety?"
- "Tell me about the adaptive dashboard logic"
- "What would you build next?"

---

## Revised Timeline

### Optimistic (focused, experienced developer)
**6-7 weeks total**

### Realistic (evenings/weekends, learning as you go)
**8-10 weeks total**

### Conservative (new to some tech, careful approach)
**12 weeks total**

**Weekly Time Investment:**
- 10-15 hours/week = realistic completion in 8-10 weeks
- 20+ hours/week = aggressive 6-7 week timeline

---

## Next Steps

### Immediate Actions (This Week)

1. **Set up development environment**
   - Install PostgreSQL locally
   - Set up Python virtual environment
   - Get OpenAI or Claude API key
   - Initialize Git repository

2. **Database foundation**
   - Write schema SQL
   - Create data generation script
   - Load sample data
   - Verify with queries

3. **Project structure**
   - Create directory structure
   - Set up requirements.txt
   - Add .gitignore
   - Initialize README

### Decision Points

**Choose Your Stack:**
- **LLM Provider:** OpenAI GPT-4 or Claude Sonnet (I recommend Claude for SQL generation)
- **Frontend:** React + TypeScript + Tailwind
- **Deployment:** Render (easiest) or Railway (also easy) or GCP Cloud Run (more impressive)

**Development Approach:**
- Build sequentially (Phase 1 → 2 → 3...)
- Test each phase thoroughly before moving forward
- Get one feature working end-to-end before adding next

---

## Success Metrics

### How You'll Know This Project is Portfolio-Ready

**Technical Metrics:**
- ✅ 90%+ accuracy on 20 test queries
- ✅ <2 second response time for most queries
- ✅ All visualizations render correctly
- ✅ Zero crashes during 5-minute demo
- ✅ One-command local setup works

**Portfolio Metrics:**
- ✅ README is compelling (someone reads for >2 minutes)
- ✅ Live demo works without errors
- ✅ Demo video is clear and under 2 minutes
- ✅ Architecture diagram is professional
- ✅ Code is clean and commented

**Interview Metrics:**
- ✅ Can explain every technical decision
- ✅ Can demo live in under 5 minutes
- ✅ Can discuss trade-offs made
- ✅ Can articulate business value
- ✅ Generates follow-up questions from interviewer

---

## Resources & References

### Learning Resources
- **FastAPI:** https://fastapi.tiangolo.com/
- **React + TypeScript:** https://react-typescript-cheatsheet.netlify.app/
- **Plotly React:** https://plotly.com/javascript/react/
- **Prompt Engineering:** https://docs.anthropic.com/claude/docs/prompt-engineering
- **SQLAlchemy:** https://docs.sqlalchemy.org/

### Inspiration Projects
- WrenAI (text-to-SQL): https://github.com/Canner/WrenAI
- Metabase (open-source BI): https://github.com/metabase/metabase

### Tools
- **Faker** (data generation): https://faker.readthedocs.io/
- **Docker Compose** (local dev): https://docs.docker.com/compose/
- **Render** (deployment): https://render.com/

---

## Contact & Next Steps

Ready to start building? Let's begin with Phase 1: Database Foundation.

I can help you with:
1. ✅ Exact database schema SQL
2. ✅ Data generation Python script
3. ✅ AI agent prompt templates
4. ✅ Dashboard UI component design
5. ✅ Deployment configuration

**Just tell me where you want to start, and I'll provide detailed implementation code!**

---

*This roadmap is your complete guide to building a portfolio project that will differentiate you from other candidates. Save this document and refer back to it throughout your build process.*

**Good luck! You've got this. 🚀**