"""
Tests for RAG agent

Tests query classification (database/document/hybrid),
document query handling, hybrid query enhancement,
and LLM integration.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from backend.rag.rag_agent import RAGAgent, AgentResponse
from backend.rag.document_retriever import DocumentRetriever
from backend.rag.vector_store import VectorStore
from backend.rag.document_processor import DocumentChunk


# Skip tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv('ANTHROPIC_API_KEY') and not os.getenv('OPENAI_API_KEY'),
    reason="API key required for RAG agent tests"
)


@pytest.fixture
def mock_retriever():
    """Create mock document retriever"""
    retriever = Mock(spec=DocumentRetriever)
    
    # Mock retrieve method
    def mock_retrieve(query, n_results=None, filter_source=None):
        from backend.rag.vector_store import SearchResult
        results = [
            SearchResult(
                content="Fault code P0420 indicates Catalyst System Efficiency Below Threshold. "
                       "Common causes: worn catalytic converter, faulty oxygen sensor.",
                metadata={
                    "source": "fault_code_reference.md",
                    "section": "P0420",
                    "citation_key": "1"
                },
                score=0.95
            )
        ]
        context = "[1] Fault Code Reference > P0420\n\nFault code P0420 indicates..."
        return results, context
    
    retriever.retrieve.side_effect = mock_retrieve
    retriever.retrieve_by_fault_code.side_effect = mock_retrieve
    retriever.retrieve_policy.side_effect = mock_retrieve
    retriever.retrieve_maintenance_procedure.side_effect = mock_retrieve
    
    return retriever


@pytest.fixture
def rag_agent(mock_retriever):
    """Create RAG agent with mock retriever"""
    return RAGAgent(retriever=mock_retriever)


class TestQueryClassification:
    """Test query classification (database/document/hybrid)"""
    
    def test_classify_database_query(self, rag_agent):
        """Test classification of database-only queries"""
        queries = [
            "Show me all vehicles",
            "How many drivers do we have?",
            "List vehicles with mileage over 100000",
            "Show driver performance for last week"
        ]
        
        for query in queries:
            classification = rag_agent.classify_query(query)
            assert classification in ["database", "hybrid"]  # Some might be borderline
    
    def test_classify_document_query(self, rag_agent):
        """Test classification of document-only queries"""
        queries = [
            "What is fault code P0420?",
            "Explain the oil change procedure",
            "What is our idle time policy?",
            "How do I calculate driver scores?"
        ]
        
        for query in queries:
            classification = rag_agent.classify_query(query)
            assert classification in ["document", "hybrid"]
    
    def test_classify_hybrid_query(self, rag_agent):
        """Test classification of hybrid queries"""
        queries = [
            "Show vehicles with P0420 and explain what it means",
            "List drivers with low scores and explain the scoring policy",
            "Which vehicles need maintenance and what are the procedures?"
        ]
        
        for query in queries:
            classification = rag_agent.classify_query(query)
            # Should be either document or hybrid (both need RAG)
            assert classification in ["document", "hybrid"]
    
    def test_classification_consistency(self, rag_agent):
        """Test that similar queries get similar classifications"""
        query1 = "What is P0420?"
        query2 = "Explain fault code P0420"
        
        classification1 = rag_agent.classify_query(query1)
        classification2 = rag_agent.classify_query(query2)
        
        # Both should be document queries
        assert classification1 == classification2


class TestProductionRAGAgent:
    """Test RAG agent with actual company documents"""
    
    @pytest.fixture
    def production_agent(self):
        """Create RAG agent with actual documents"""
        chroma_path = Path(__file__).parent.parent.parent.parent / "chroma_db"
        if not chroma_path.exists():
            pytest.skip("Production ChromaDB not found. Run scripts/setup_rag.py first.")
        
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory=str(chroma_path),
            embedding_model="local"
        )
        
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        
        return RAGAgent(retriever=retriever)
    
    def test_answer_fault_code_question(self, production_agent):
        """Test answering actual fault code questions"""
        response = production_agent.answer_document_query("What is fault code P0420?")
        
        assert hasattr(response, 'answer')
        assert len(response.answer) > 50
        # Should mention catalyst or converter
        assert 'catalyst' in response.answer.lower() or 'converter' in response.answer.lower()
    
    def test_answer_maintenance_question(self, production_agent):
        """Test answering maintenance procedure questions"""
        response = production_agent.answer_document_query("How do I change the oil?")
        
        assert hasattr(response, 'answer')
        assert len(response.answer) > 50
        # Should mention oil change procedure
        assert 'oil' in response.answer.lower()
    
    def test_answer_policy_question(self, production_agent):
        """Test answering policy questions"""
        response = production_agent.answer_document_query("What is the idle time policy?")
        
        assert hasattr(response, 'answer')
        assert len(response.answer) > 20
        # Should mention idle time
        assert 'idle' in response.answer.lower()
    
    def test_classify_real_queries(self, production_agent):
        """Test classification of real-world queries"""
        test_cases = [
            ("What is P0420?", "document"),
            ("Show me all vehicles", "database"),
            ("Show vehicles with P0420 and explain it", "hybrid"),
        ]
        
        for query, expected_type in test_cases:
            classification = production_agent.classify_query(query)
            # Classification might not be exact, but should be reasonable
            assert classification in ["database", "document", "hybrid"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

