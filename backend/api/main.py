"""
FleetFix FastAPI Application
Main API server for AI-powered dashboard
"""

import os
import sys
from typing import Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from ai_agent.query_executor import QueryExecutor
from ai_agent.insight_generator import InsightGenerator

# Initialize FastAPI app
app = FastAPI(
    title="FleetFix AI API",
    description="AI-powered fleet management query API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
schema_context = None
text_to_sql = None
sql_validator = None
query_executor = None
insight_generator = None


@app.on_event("startup")
async def startup_event():
    """Initialize AI components on startup"""
    global schema_context, text_to_sql, sql_validator, query_executor, insight_generator
    
    print("Initializing AI components...")
    
    # Build schema context
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    print("✓ Schema context loaded")
    
    # Initialize components
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    text_to_sql = TextToSQLConverter(schema_context, provider=provider)
    print(f"✓ Text-to-SQL initialized ({provider})")
    
    sql_validator = SQLValidator()
    print("✓ SQL validator ready")
    
    query_executor = QueryExecutor(timeout_seconds=30)
    print("✓ Query executor ready")
    
    insight_generator = InsightGenerator(provider=provider)
    print("✓ Insight generator ready")
    
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


class InsightResponse(BaseModel):
    """AI-generated insight"""
    type: str
    severity: str
    message: str
    confidence: float


class QueryResponse(BaseModel):
    """Query execution response"""
    success: bool
    query: str
    sql: str
    explanation: str
    confidence: float
    row_count: int
    execution_time_ms: float
    columns: list
    rows: list
    summary: Optional[str] = None
    insights: Optional[list[InsightResponse]] = None
    recommendations: Optional[list[str]] = None
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
    """Root endpoint"""
    return {
        "message": "FleetFix AI API",
        "version": "1.0.0",
        "docs": "/docs"
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
    Execute natural language query
    
    Converts natural language to SQL, executes it, and optionally generates insights.
    """
    try:
        # Step 1: Convert to SQL
        sql_result = text_to_sql.convert(request.query)
        
        if sql_result.error:
            raise HTTPException(
                status_code=400,
                detail=f"SQL generation failed: {sql_result.error}"
            )
        
        # Step 2: Validate SQL
        validation = sql_validator.validate(sql_result.sql)
        
        if not validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"SQL validation failed: {'; '.join(validation.errors)}"
            )
        
        # Step 3: Execute query
        exec_result = query_executor.execute_with_limit(
            validation.sanitized_sql,
            max_rows=request.max_rows,
            session=db
        )
        
        if not exec_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Query execution failed: {exec_result.error}"
            )
        
        # Step 4: Generate insights (optional)
        insights_list = None
        recommendations = None
        summary = None
        
        if request.include_insights and exec_result.row_count > 0:
            insight_result = insight_generator.generate_insights(
                request.query,
                sql_result.sql,
                exec_result
            )
            
            if not insight_result.error:
                summary = insight_result.summary
                recommendations = insight_result.recommendations
                
                insights_list = [
                    InsightResponse(
                        type=i.type,
                        severity=i.severity,
                        message=i.message,
                        confidence=i.confidence
                    )
                    for i in insight_result.insights
                ]
        
        # Build response
        return QueryResponse(
            success=True,
            query=request.query,
            sql=sql_result.sql,
            explanation=sql_result.explanation,
            confidence=sql_result.confidence,
            row_count=exec_result.row_count,
            execution_time_ms=exec_result.execution_time_ms,
            columns=exec_result.columns,
            rows=exec_result.rows,
            summary=summary,
            insights=insights_list,
            recommendations=recommendations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
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
    
    port = int(os.getenv("API_PORT", 8001))
    
    print("=" * 50)
    print("Starting FleetFix API Server")
    print("=" * 50)
    print(f"API: http://localhost:{port}")
    print(f"Docs: http://localhost:{port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )