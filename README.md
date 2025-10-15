# FleetFix AI Dashboard

An intelligent fleet management platform that combines natural language querying, adaptive insights, and real-time data visualization using Claude AI and RAG (Retrieval-Augmented Generation).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.2-3178C6.svg)](https://www.typescriptlang.org/)

## Overview

FleetFix is a full-stack business intelligence platform designed for fleet management operations. The system analyzes fleet data daily to surface critical issues automatically, supports natural language queries for ad-hoc analysis, and provides context-aware answers by combining database queries with company documentation.

### Key Features

- **Adaptive Daily Insights**: Automated analysis of fleet changes (fault codes, maintenance schedules, driver performance, fuel efficiency) with prioritized recommendations
- **Natural Language Queries**: Text-to-SQL conversion with Claude AI for intuitive data exploration
- **Hybrid AI Architecture**: Combines database queries with RAG document retrieval for context-aware responses
- **Dynamic Visualizations**: Automatic chart generation (Plotly) based on query results
- **Production-Ready**: Comprehensive test coverage, Docker containerization, and cloud deployment configuration

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)
- Anthropic API Key

### Setup

```bash
# Clone and configure environment
git clone <repository-url>
cd fleetfix-ai-dashboard
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

# Start with Docker Compose
docker-compose up -d

# Initialize RAG system (one-time)
docker-compose exec backend python scripts/setup_rag.py

# Seed database with sample data
docker-compose exec backend python database/seed_data.py --reset --inject-events
```

Access the dashboard at `http://localhost:3000`

API documentation available at `http://localhost:8000/docs`

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    React Frontend                     │
│           TypeScript • Tailwind • Plotly             │
└───────────────┬──────────────────────────────────────┘
                │ HTTP/REST
┌───────────────▼──────────────────────────────────────┐
│              FastAPI Backend (Python)                 │
│  ┌────────────────────────────────────────────────┐ │
│  │         Query Pipeline                         │ │
│  │  1. Classify Query (DB/Doc/Hybrid)            │ │
│  │  2. Generate SQL or Retrieve Docs             │ │
│  │  3. Execute & Validate                        │ │
│  │  4. Generate Visualizations                   │ │
│  │  5. Create Insights                           │ │
│  └────────────────────────────────────────────────┘ │
│                                                       │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐ │
│  │  Text-to-SQL │  │  RAG System   │  │  Daily   │ │
│  │  (Claude AI) │  │  (ChromaDB)   │  │  Digest  │ │
│  └──────────────┘  └───────────────┘  └──────────┘ │
└───────┬──────────────────┬───────────────────────────┘
        │                  │
┌───────▼──────────┐  ┌───▼──────────────┐
│   PostgreSQL     │  │   Company Docs   │
│   (Fleet Data)   │  │   (Markdown)     │
└──────────────────┘  └──────────────────┘
```

## Tech Stack

**Frontend:**
- React 18 with TypeScript
- Tailwind CSS for styling
- Plotly.js for visualizations
- Vite for development and build

**Backend:**
- FastAPI (Python 3.11)
- SQLAlchemy ORM
- PostgreSQL database
- Claude AI (Anthropic) for LLM
- ChromaDB for vector storage
- Sentence-Transformers for embeddings

**Infrastructure:**
- Docker & Docker Compose
- Google Cloud Run (deployment ready)
- Cloud SQL (PostgreSQL)

## Core Functionality

### Adaptive Daily Insights

The system automatically analyzes fleet data to detect significant changes:
- New fault codes (last 24 hours)
- Upcoming maintenance (within 7 days)
- Driver performance drops (>10 points)
- Fuel efficiency changes (>5%)
- High downtime vehicles (>4 hours)

A priority scoring algorithm surfaces the top 2-3 issues with actionable recommendations, estimated costs, and auto-generated visualizations.

### Query Types

**Database Queries:**
- "Show me vehicles overdue for maintenance"
- "Which drivers had harsh braking events this week?"
- "What's our fleet's average fuel efficiency?"

**Document Queries (RAG):**
- "What is fault code P0420?"
- "Explain the oil change procedure"
- "What's our idle time policy?"

**Hybrid Queries:**
- "Show vehicles with P0420 and explain what it means"
- "List overdue vehicles and tell me what maintenance they need"

### Visualization Generation

The system analyzes query results to automatically select appropriate chart types:
- Time series: Line charts
- Categories: Bar charts
- Correlations: Scatter plots
- Geographic data: Maps
- Tabular data: Interactive tables

## Project Structure

```
fleetfix-ai-dashboard/
├── backend/
│   ├── ai_agent/          # Text-to-SQL, insight generation
│   ├── api/               # FastAPI endpoints
│   ├── database/          # Models, schema, seed data
│   ├── rag/               # RAG system (ChromaDB, embeddings)
│   ├── visualizer/        # Plotly chart generation
│   └── tests/             # 75+ test cases
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── api/           # API client
│   │   └── types/         # TypeScript interfaces
│   └── Dockerfile
├── company_docs/          # Sample company documentation
└── docker-compose.yml     # Local development setup
```

## Development

### Local Development

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
python -m uvicorn api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Testing

```bash
# Backend tests (75+ test cases)
cd backend
pytest

# With coverage
pytest --cov=ai_agent --cov=database --cov=rag --cov-report=html

# Frontend tests
cd frontend
npm test
```

### Docker

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after changes
docker-compose up -d --build
```

## Deployment

The application is configured for deployment to Google Cloud Platform using Cloud Run. See deployment documentation for detailed instructions on:
- Cloud SQL setup
- Secret Manager configuration
- Container deployment
- Custom domain setup
- Monitoring and logging

## RAG System

The RAG system provides context-aware responses by retrieving relevant information from company documentation. The system uses:
- Intelligent chunking strategy for document processing
- Semantic search with ChromaDB
- Optional reranking for improved relevance
- Citation tracking for transparency

Setup requires one-time document indexing:

```bash
python scripts/setup_rag.py
```

## Performance

- Query Response Time: 800-1200ms average (includes AI processing)
- Daily Digest Generation: 2-5 seconds
- RAG Retrieval: <200ms (with reranking)
- Chart Generation: <10ms
- Cost per Query: ~$0.002 (Claude Sonnet)

## Key Design Decisions

**Claude AI vs GPT-4:** Selected for superior SQL generation accuracy in testing and more concise outputs.

**ChromaDB:** Open-source vector store with local embedding support, good performance, and straightforward deployment.

**FastAPI:** Automatic API documentation, type safety with Pydantic, excellent async support, and rapid development cycle.

**RAG Architecture:** Modular design allows independent scaling and optional deployment as a separate microservice.

## Testing

The project includes comprehensive test coverage across all major components:
- AI agent tests (text-to-SQL, query execution)
- RAG system tests (document processing, retrieval, integration)
- API integration tests
- Database tests
- Visualization tests

## License

MIT License - see LICENSE file for details.

## Contact

For questions or feedback, please open an issue on GitHub.
