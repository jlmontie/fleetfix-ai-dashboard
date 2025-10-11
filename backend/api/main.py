"""
Main FastAPI application for FleetFix AI Dashboard.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLAgent
from ai_agent.sql_validator import SQLValidator
from ai_agent.query_executor import QueryExecutor
from ai_agent.insight_generator import InsightGenerator, Insight
from visualizer.plotly_generator import generate_plotly_chart

# Import visualization router
from api.visualize import router as visualize_router

# Initialize FastAPI app
app = FastAPI(
    title="FleetFix AI Dashboard API",
    description="AI-powered fleet management analytics",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(visualize_router, prefix="/api", tags=["visualization"])

# Serve static dashboard for testing
dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

# Global components (initialized on startup)
schema_context = None
sql_validator = None
query_executor = None
insight_generator = None


@app.on_event("startup")
async def startup_event():
    """Initialize AI components on startup"""
    global schema_context, sql_validator, query_executor, insight_generator
    
    print("Initializing AI components...")
    
    # Build schema context
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    print("✓ Schema context loaded")
    
    # Initialize components
    sql_validator = SQLValidator()
    print("✓ SQL validator ready")
    
    query_executor = QueryExecutor(timeout_seconds=30)
    print("✓ Query executor ready")
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    insight_generator = InsightGenerator(provider=provider)
    print(f"✓ Insight generator ready ({provider})")
    
    print("=" * 50)
    print("FleetFix API Ready!")
    print("=" * 50)


# Request/Response Models

class QueryRequest(BaseModel):
    """Natural language query request"""
    query: str = Field(..., description="Natural language question", min_length=1)
    include_insights: bool = Field(True, description="Generate AI insights")
    max_rows: int = Field(100, description="Maximum rows to return", ge=1, le=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me vehicles overdue for maintenance",
                "include_insights": True,
                "max_rows": 100
            }
        }


class QueryResponse(BaseModel):
    """Response model for query results with visualization."""
    success: bool
    query: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    results: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    chart_config: Optional[Dict[str, Any]] = None
    plotly_chart: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    insights: Optional[List[Insight]] = None
    recommendations: Optional[List[str]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database: str
    ai_provider: str


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """API root endpoint."""
    return {
        "name": "FleetFix AI Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/query",
            "visualize": "/api/visualize",
            "schema": "/api/schema",
            "examples": "/api/examples",
            "dashboard": "/dashboard/dashboard.html",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "ai_provider": provider
    }


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute natural language query with visualization.
    
    This endpoint orchestrates:
    1. Text-to-SQL conversion with chart recommendation (single AI call)
    2. SQL validation
    3. Query execution
    4. Plotly chart generation
    5. Insight generation
    """
    try:
        # Step 1: Generate SQL and chart recommendation (single AI call)
        text_to_sql_agent = TextToSQLAgent(schema_context)
        sql_result = text_to_sql_agent.generate_sql_and_chart(request.query)
        
        if sql_result.get('error'):
            return QueryResponse(
                success=False,
                error=sql_result['error'],
                query=request.query
            )
        
        sql_query = sql_result.get('sql')
        chart_config = sql_result.get('chart_config', {})
        explanation = sql_result.get('explanation', '')
        confidence = chart_config.get('confidence', 0.0)
        
        if not sql_query:
            return QueryResponse(
                success=False,
                error="No SQL generated",
                query=request.query
            )
        
        # Step 2: Validate SQL
        validation = sql_validator.validate(sql_query)
        
        if not validation.is_valid:
            return QueryResponse(
                success=False,
                error=f"SQL validation failed: {'; '.join(validation.errors)}",
                sql=sql_query,
                query=request.query
            )
        
        # Step 3: Execute query
        exec_result = query_executor.execute_with_limit(
            validation.sanitized_sql,
            max_rows=request.max_rows,
            session=db
        )
        
        if not exec_result.success:
            return QueryResponse(
                success=False,
                error=f"Query execution failed: {exec_result.error}",
                sql=sql_query,
                query=request.query
            )
        
        # Step 4: Generate Plotly chart specification
        plotly_chart = None
        if exec_result.rows and chart_config:
            try:
                # Convert rows to dict format for plotly generator
                # results = [dict(zip(exec_result.columns, row)) for row in exec_result.rows]
                
                plotly_chart = generate_plotly_chart(
                    chart_config=chart_config,
                    results=exec_result.rows,
                    columns=exec_result.columns
                )
            except Exception as e:
                print(f"Plotly generation failed: {str(e)}")
                # Don't fail the whole request if visualization fails
                plotly_chart = None
        
        # Step 5: Generate insights (optional)
        insights_list = None
        recommendations = None
        summary = None
        
        if request.include_insights and exec_result.row_count > 0:
            insight_result = insight_generator.generate_insights(
                request.query,
                sql_query,
                exec_result
            )
            
            if not insight_result.error:
                summary = insight_result.summary
                recommendations = insight_result.recommendations
                insights_list = insight_result.insights
        print(f"\nInsights list: {insights_list}\n")
        # Convert rows to dict format for response
        results = [dict(zip(exec_result.columns, row)) for row in exec_result.rows]
        
        # Return comprehensive response
        return QueryResponse(
            success=True,
            query=request.query,
            sql=sql_query,
            explanation=explanation,
            confidence=confidence,
            results=results,
            columns=exec_result.columns,
            row_count=exec_result.row_count,
            execution_time_ms=exec_result.execution_time_ms,
            chart_config=chart_config,
            plotly_chart=plotly_chart,
            summary=summary,
            insights=insights_list,
            recommendations=recommendations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return QueryResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
            query=request.query
        )


@app.get("/api/schema", tags=["Schema"])
async def get_schema():
    """Get database schema information"""
    builder = SchemaContextBuilder()
    tables = builder.get_all_tables()
    
    return {
        "tables": [
            {
                "name": table.name,
                "description": table.description,
                "row_count": table.row_count,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "primary_key": col.primary_key,
                        "foreign_key": col.foreign_key,
                        "description": col.description
                    }
                    for col in table.columns
                ]
            }
            for table in tables
        ]
    }


@app.get("/api/examples", tags=["Query"])
async def get_example_queries():
    """Get example queries users can try"""
    return {
        "examples": [
            {
                "category": "Maintenance",
                "queries": [
                    "Show me vehicles that are overdue for maintenance",
                    "Which vehicles need service this week?",
                    "What are the most expensive maintenance services?"
                ]
            },
            {
                "category": "Driver Performance",
                "queries": [
                    "Which drivers had poor performance yesterday?",
                    "Show me drivers with the best safety scores",
                    "Who had the most harsh braking events this week?"
                ]
            },
            {
                "category": "Fleet Health",
                "queries": [
                    "Show me all unresolved critical fault codes",
                    "What's our fleet's average fuel efficiency?",
                    "Which vehicles have the highest mileage?"
                ]
            },
            {
                "category": "Analysis",
                "queries": [
                    "Show me maintenance costs by vehicle type",
                    "What's the trend in driver performance over the last month?",
                    "Which routes have the most safety incidents?"
                ]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    
    print("=" * 50)
    print("Starting FleetFix API Server")
    print("=" * 50)
    print(f"API: http://localhost:{port}")
    print(f"Docs: http://localhost:{port}/docs")
    print(f"Dashboard: http://localhost:{port}/dashboard/dashboard.html")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )