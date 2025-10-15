"""
RAG Integration Layer for FleetFix API

This module provides a clean interface to integrate the RAG system with the main API.
Designed to be modular and support microservice deployment.

The RAG system handles:
- Document-only queries (policies, procedures, fault codes)
- Hybrid queries (database + documents)
- Query classification and routing
"""

import os
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, asdict
import logging

# Graceful imports - RAG is optional for microservice flexibility
try:
    from rag import (
        VectorStore,
        DocumentRetriever,
        DocumentProcessor,
        RAGAgent,
        AgentResponse
    )
    RAG_AVAILABLE = True
except ImportError:
    try:
        from backend.rag import (
            VectorStore,
            DocumentRetriever,
            DocumentProcessor,
            RAGAgent,
            AgentResponse
        )
        RAG_AVAILABLE = True
    except ImportError as e:
        logging.warning(f"RAG system not available: {e}")
        RAG_AVAILABLE = False
        VectorStore = None
        DocumentRetriever = None
        DocumentProcessor = None
        RAGAgent = None
        AgentResponse = None


logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Context information from document retrieval"""
    retrieved_docs: List[Dict[str, Any]]
    citations: List[str]
    context_text: str
    relevance_scores: List[float]


class RAGIntegration:
    """
    Main RAG integration class for FleetFix API.
    
    This class can be initialized once at startup and reused for all requests.
    Designed to fail gracefully if RAG is not available (microservice deployment).
    """
    
    def __init__(
        self,
        company_docs_path: str = "company_docs",
        chroma_db_path: str = "./chroma_db",
        max_context_chunks: int = 5,
        enable_reranking: bool = True
    ):
        """
        Initialize RAG integration.
        
        Args:
            company_docs_path: Path to company documentation
            chroma_db_path: Path to ChromaDB persistence directory
            max_context_chunks: Maximum number of document chunks to retrieve
            enable_reranking: Whether to enable result reranking
        
        Raises:
            RuntimeError: If RAG is not available
        """
        if not RAG_AVAILABLE:
            raise RuntimeError(
                "RAG system not available. Install dependencies: "
                "pip install -r backend/rag/requirements.txt"
            )
        
        self.company_docs_path = company_docs_path
        self.chroma_db_path = chroma_db_path
        self.max_context_chunks = max_context_chunks
        self.enable_reranking = enable_reranking
        
        # These will be initialized in initialize()
        self.vector_store: Optional[VectorStore] = None
        self.retriever: Optional[DocumentRetriever] = None
        self.rag_agent: Optional[RAGAgent] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize RAG components.
        
        This is separated from __init__ to allow deferred initialization
        and better error handling.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing RAG system...")
            
            # Check if chroma_db exists
            if not os.path.exists(self.chroma_db_path):
                logger.error(
                    f"ChromaDB not found at {self.chroma_db_path}. "
                    "Please run setup script: python scripts/setup_rag.py"
                )
                return False
            
            # Initialize vector store
            logger.info("Loading vector store...")
            self.vector_store = VectorStore(
                collection_name="fleetfix_docs",
                persist_directory=self.chroma_db_path,
                embedding_model="local"
            )
            
            # Check if database has documents
            doc_count = self.vector_store.collection.count()
            if doc_count == 0:
                logger.error(
                    "Vector database is empty. "
                    "Please run setup script: python scripts/setup_rag.py"
                )
                return False
            
            logger.info(f"Vector store loaded with {doc_count} documents")
            
            # Initialize retriever
            self.retriever = DocumentRetriever(
                vector_store=self.vector_store,
                max_context_chunks=self.max_context_chunks,
                enable_reranking=self.enable_reranking
            )
            logger.info("Document retriever ready")
            
            # Initialize RAG agent
            self.rag_agent = RAGAgent(
                retriever=self.retriever,
                model="claude-sonnet-4-20250514"
            )
            logger.info("RAG agent ready")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if RAG system is available and initialized"""
        return RAG_AVAILABLE and self._initialized
    
    def classify_query(self, query: str) -> Literal["database", "document", "hybrid"]:
        """
        Classify query to determine routing strategy.
        
        Returns:
            "database" - SQL query needed
            "document" - Document retrieval only
            "hybrid" - Both database and documents
        """
        if not self.is_available():
            # Default to database query if RAG not available
            return "database"
        
        return self.rag_agent.classify_query(query)
    
    def retrieve_documents(
        self,
        query: str,
        n_results: Optional[int] = None
    ) -> Optional[RAGContext]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query
            n_results: Number of results to retrieve (defaults to max_context_chunks)
        
        Returns:
            RAGContext with retrieved documents and citations, or None if unavailable
        """
        if not self.is_available():
            logger.warning("RAG system not available for document retrieval")
            return None
        
        try:
            results, context_text = self.retriever.retrieve(
                query=query,
                n_results=n_results
            )
            
            # Convert RetrievalResult objects to dicts for API response
            retrieved_docs = [
                {
                    "content": doc.content,
                    "section": doc.metadata.get("section", "Unknown"),
                    "source": doc.metadata.get("source", "Unknown"),
                    "relevance_score": doc.relevance_score,
                    "citation_key": doc.citation_key
                }
                for doc in results
            ]
            
            citations = self.retriever.get_citations(results)
            relevance_scores = [doc.relevance_score for doc in results]
            
            return RAGContext(
                retrieved_docs=retrieved_docs,
                citations=citations,
                context_text=context_text,
                relevance_scores=relevance_scores
            )
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return None
    
    def answer_document_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Answer query using only documents (no database).
        
        Args:
            query: User query
        
        Returns:
            Dict with answer, citations, and retrieved docs, or None if unavailable
        """
        if not self.is_available():
            return None
        
        try:
            response: AgentResponse = self.rag_agent.answer_document_query(query)
            
            # Convert to dict for API response
            return {
                "answer": response.answer,
                "query_type": response.query_type,
                "citations": response.citations,
                "retrieved_docs": [
                    {
                        "content": doc.content,
                        "section": doc.metadata.get("section"),
                        "source": doc.metadata.get("source"),
                        "relevance_score": doc.relevance_score
                    }
                    for doc in (response.retrieved_docs or [])
                ]
            }
            
        except Exception as e:
            logger.error(f"Error answering document query: {e}")
            return None
    
    def enhance_database_results(
        self,
        query: str,
        database_results: List[Dict[str, Any]],
        sql_query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Enhance database results with relevant document context.
        
        This is used for hybrid queries where we have both database results
        and want to add explanatory context from documents.
        
        Args:
            query: Original user query
            database_results: Results from database query
            sql_query: The SQL query that was executed
        
        Returns:
            Dict with enhanced answer, citations, and context, or None if unavailable
        """
        if not self.is_available():
            return None
        
        try:
            # Get relevant document context
            rag_context = self.retrieve_documents(query, n_results=3)
            
            if not rag_context:
                return None
            
            # Format database results for context
            db_summary = self._format_db_results(database_results)
            
            # Build enhanced prompt
            prompt = f"""You are FleetFix AI Assistant. The user asked: "{query}"

We executed this SQL query:
{sql_query}

Database Results:
{db_summary}

Relevant Company Documentation:
{rag_context.context_text}

Instructions:
- Synthesize the database results with the documentation
- Provide actionable insights based on both sources
- Cite documentation using [1], [2], etc. markers
- Explain what the data means and recommend next steps
- Be concise but thorough

Enhanced Answer:"""
            
            # Get enhanced answer from LLM
            from anthropic import Anthropic
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            enhanced_answer = message.content[0].text
            
            return {
                "enhanced_answer": enhanced_answer,
                "citations": rag_context.citations,
                "retrieved_docs": rag_context.retrieved_docs,
                "context_text": rag_context.context_text
            }
            
        except Exception as e:
            logger.error(f"Error enhancing database results: {e}")
            return None
    
    def _format_db_results(self, results: List[Dict], max_rows: int = 10) -> str:
        """Format database results for LLM prompt"""
        if not results:
            return "No results found."
        
        display_results = results[:max_rows]
        formatted = []
        
        for i, row in enumerate(display_results, 1):
            row_str = ", ".join(f"{k}: {v}" for k, v in row.items())
            formatted.append(f"  {i}. {row_str}")
        
        if len(results) > max_rows:
            formatted.append(f"  ... and {len(results) - max_rows} more rows")
        
        return "\n".join(formatted)


# Singleton instance for API use
_rag_integration: Optional[RAGIntegration] = None


def get_rag_integration() -> Optional[RAGIntegration]:
    """
    Get the global RAG integration instance.
    
    Returns None if RAG is not available or not initialized.
    """
    return _rag_integration


def initialize_rag_integration(
    company_docs_path: str = "company_docs",
    chroma_db_path: str = "./chroma_db",
    max_context_chunks: int = 5,
    enable_reranking: bool = True
) -> bool:
    """
    Initialize the global RAG integration instance.
    
    Call this once at application startup.
    
    Returns:
        True if initialization successful, False otherwise
    """
    global _rag_integration
    
    if not RAG_AVAILABLE:
        logger.warning("RAG system not available - API will run without document retrieval")
        return False
    
    try:
        _rag_integration = RAGIntegration(
            company_docs_path=company_docs_path,
            chroma_db_path=chroma_db_path,
            max_context_chunks=max_context_chunks,
            enable_reranking=enable_reranking
        )
        
        success = _rag_integration.initialize()
        
        if success:
            logger.info("✓ RAG integration initialized successfully")
        else:
            logger.error("✗ RAG integration initialization failed")
            _rag_integration = None
        
        return success
        
    except Exception as e:
        logger.error(f"Error initializing RAG integration: {e}")
        _rag_integration = None
        return False


