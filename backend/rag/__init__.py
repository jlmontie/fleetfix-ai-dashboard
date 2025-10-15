"""
FleetFix RAG System

Production-grade Retrieval-Augmented Generation for company documents.

Main Components:
- DocumentProcessor: Intelligent document chunking
- VectorStore: Embedding generation and storage
- DocumentRetriever: Search and reranking
- RAGAgent: Main agent for query classification and routing
"""

from .document_processor import DocumentProcessor, DocumentChunk
from .vector_store import VectorStore, SearchResult
from .document_retriever import DocumentRetriever, RetrievalResult
from .rag_agent import RAGAgent, AgentResponse

__version__ = "1.0.0"

__all__ = [
    "DocumentProcessor",
    "DocumentChunk",
    "VectorStore", 
    "SearchResult",
    "DocumentRetriever",
    "RetrievalResult",
    "RAGAgent",
    "AgentResponse",
]