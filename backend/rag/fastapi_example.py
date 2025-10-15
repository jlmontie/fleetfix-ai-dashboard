"""
FastAPI Integration for FleetFix RAG System

Complete API endpoints with request validation, error handling,
and response formatting.

Run: uvicorn fastapi_endpoints:app --reload
"""

from typing import Optional, List, Dict, Literal
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

from rag.vector_store import VectorStore
from rag.document_retriever import DocumentRetriever
from rag.rag_agent import RAGAgent, AgentResponse


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for document queries"""
    query: str = Field(..., min_length=3, max_length=500, description="User query")
    n_results: Optional[int] = Field(5, ge=1, le=10, description="Number of results to return")
    filter_source: Optional[str] = Field(None, description="Filter by specific document")
    include_context: bool = Field(False, description="Include raw context in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is fault code P0420?",
                "n_results": 5,
                "filter_source": None,
                "include_context": False
            }
        }


class SearchResult(BaseModel):
    """Model for a single search result"""
    content: str = Field(..., description="Chunk content")
    section: str = Field(..., description="Document section")
    source: str = Field(..., description="Source document")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")
    citation_key: str = Field(..., description="Citation reference")


class QueryResponse(BaseModel):
    """Response model for document queries"""
    query: str
    results: List[SearchResult]
    num_results: int
    context: Optional[str] = None
    citations: List[str]
    query_time_ms: float
    timestamp: datetime


class AgentQueryRequest(BaseModel):
    """Request model for AI agent queries"""
    query: str = Field(..., min_length=3, max_length=500)
    schema_context: Optional[str] = Field(None, description="Database schema for SQL generation")
    database_results: Optional[List[Dict]] = Field(None, description="Pre-executed database results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me vehicles with fault code P0420 and explain what it means",
                "schema_context": "vehicles(id, make, model, year, vin)...",
                "database_results": None
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for AI agent queries"""
    query: str
    answer: str
    query_type: Literal["database", "document", "hybrid"]
    sql_query: Optional[str] = None
    citations: Optional[List[str]] = None
    sources: List[Dict]
    query_time_ms: float
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    vector_store_status: str
    total_chunks: int
    embedding_model: str
    timestamp: datetime


class StatsResponse(BaseModel):
    """Statistics response"""
    total_chunks: int
    collection_name: str
    embedding_dimension: int
    embedding_model: str
    documents: List[Dict[str, int]]


# ============================================================================
# Initialize FastAPI App
# ============================================================================

app = FastAPI(
    title="FleetFix RAG API",
    description="Retrieval-Augmented Generation API for FleetFix company documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Global State (Initialize on Startup)
# ============================================================================

retriever: Optional[DocumentRetriever] = None
agent: Optional[RAGAgent] = None
vector_store: Optional[VectorStore] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global retriever, agent, vector_store
    
    logger.info("Initializing FleetFix RAG system...")
    
    try:
        # Initialize vector store
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory="./chroma_db",
            embedding_model="local"
        )
        logger.info(f"✓ Vector store loaded: {vector_store.collection.count()} chunks")
        
        # Initialize retriever
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        logger.info("✓ Document retriever initialized")
        
        # Initialize AI agent
        try:
            agent = RAGAgent(retriever=retriever)
            logger.info("✓ AI agent initialized")
        except ValueError:
            logger.warning("⚠ AI agent not initialized (missing ANTHROPIC_API_KEY)")
            agent = None
        
        logger.info("✓ RAG system ready!")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize RAG system: {e}")
        raise


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "message": "FleetFix RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not vector_store or not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized"
        )
    
    stats = vector_store.get_statistics()
    
    return HealthResponse(
        status="healthy",
        vector_store_status="operational",
        total_chunks=stats['total_chunks'],
        embedding_model=stats['embedding_model'],
        timestamp=datetime.now()
    )


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get vector store statistics"""
    if not vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized"
        )
    
    stats = vector_store.get_statistics()
    
    # Get document breakdown
    all_data = vector_store.collection.get(include=['metadatas'])
    doc_counts = {}
    
    for metadata in all_data['metadatas']:
        source = metadata.get('source', 'Unknown')
        doc_counts[source] = doc_counts.get(source, 0) + 1
    
    documents = [
        {"source": source, "chunks": count}
        for source, count in sorted(doc_counts.items())
    ]
    
    return StatsResponse(
        total_chunks=stats['total_chunks'],
        collection_name=stats['collection_name'],
        embedding_dimension=stats['embedding_dimension'],
        embedding_model=stats['embedding_model'],
        documents=documents
    )


@app.post("/search", response_model=QueryResponse)
async def search_documents(request: QueryRequest):
    """
    Search company documents using semantic search.
    
    This endpoint performs RAG-based retrieval without LLM generation.
    Use for raw document retrieval.
    """
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retriever not initialized"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Perform retrieval
        results, context = retriever.retrieve(
            query=request.query,
            n_results=request.n_results,
            filter_source=request.filter_source
        )
        
        query_time_ms = (time.time() - start_time) * 1000
        
        # Format results
        search_results = [
            SearchResult(
                content=r.content,
                section=r.metadata.get('section', 'Unknown'),
                source=r.metadata.get('source', 'Unknown'),
                relevance_score=r.relevance_score,
                citation_key=r.citation_key
            )
            for r in results
        ]
        
        return QueryResponse(
            query=request.query,
            results=search_results,
            num_results=len(results),
            context=context if request.include_context else None,
            citations=retriever.get_citations(results),
            query_time_ms=query_time_ms,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Query the AI agent with RAG capabilities.
    
    This endpoint uses the LLM to generate natural language responses
    using retrieved context from company documents.
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent not initialized (ANTHROPIC_API_KEY required)"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Get response from agent
        response = agent.answer(
            query=request.query,
            schema_context=request.schema_context,
            database_results=request.database_results
        )
        
        query_time_ms = (time.time() - start_time) * 1000
        
        # Format sources
        sources = []
        if response.retrieved_docs:
            sources = [
                {
                    "section": doc.metadata.get("section"),
                    "source": doc.metadata.get("source"),
                    "relevance": round(doc.relevance_score, 3)
                }
                for doc in response.retrieved_docs
            ]
        
        return AgentQueryResponse(
            query=request.query,
            answer=response.answer,
            query_type=response.query_type,
            sql_query=response.sql_query,
            citations=response.citations,
            sources=sources,
            query_time_ms=query_time_ms,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Agent query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@app.get("/search/fault-code/{code}", response_model=QueryResponse)
async def search_fault_code(code: str):
    """
    Specialized endpoint for fault code lookup.
    
    Example: /search/fault-code/P0420
    """
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retriever not initialized"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Perform specialized fault code retrieval
        results, context = retriever.retrieve_by_fault_code(code)
        
        query_time_ms = (time.time() - start_time) * 1000
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No information found for fault code {code}"
            )
        
        # Format results
        search_results = [
            SearchResult(
                content=r.content,
                section=r.metadata.get('section', 'Unknown'),
                source=r.metadata.get('source', 'Unknown'),
                relevance_score=r.relevance_score,
                citation_key=r.citation_key
            )
            for r in results
        ]
        
        return QueryResponse(
            query=f"fault code {code}",
            results=search_results,
            num_results=len(results),
            context=None,
            citations=retriever.get_citations(results),
            query_time_ms=query_time_ms,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fault code search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/search/policy", response_model=QueryResponse)
async def search_policy(
    topic: str = Query(..., min_length=3, description="Policy topic to search")
):
    """
    Specialized endpoint for policy lookup.
    
    Example: /search/policy?topic=driver%20score
    """
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retriever not initialized"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Perform specialized policy retrieval
        results, context = retriever.retrieve_policy(topic)
        
        query_time_ms = (time.time() - start_time) * 1000
        
        # Format results
        search_results = [
            SearchResult(
                content=r.content,
                section=r.metadata.get('section', 'Unknown'),
                source=r.metadata.get('source', 'Unknown'),
                relevance_score=r.relevance_score,
                citation_key=r.citation_key
            )
            for r in results
        ]
        
        return QueryResponse(
            query=topic,
            results=search_results,
            num_results=len(results),
            context=None,
            citations=retriever.get_citations(results),
            query_time_ms=query_time_ms,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Policy search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/documents", response_model=List[str])
async def list_documents():
    """List all indexed documents"""
    if not vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized"
        )
    
    try:
        all_data = vector_store.collection.get(include=['metadatas'])
        sources = sorted(set(m.get('source', 'Unknown') for m in all_data['metadatas']))
        return sources
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


# ============================================================================
# Development / Testing Endpoints
# ============================================================================

@app.get("/dev/compare-strategies")
async def compare_strategies(query: str = Query(..., min_length=3)):
    """
    Compare different search strategies (for debugging/tuning).
    
    Development endpoint that shows results from semantic, keyword, and hybrid search.
    """
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retriever not initialized"
        )
    
    try:
        debug_results = retriever.debug_search(query, n_results=5)
        return {
            "query": query,
            "strategies": debug_results
        }
        
    except Exception as e:
        logger.error(f"Compare strategies error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


# ============================================================================
# Main (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
