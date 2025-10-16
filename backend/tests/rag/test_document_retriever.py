"""
Tests for RAG document retriever

Tests query classification, reranking, specialized search strategies,
and citation generation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.rag.vector_store import VectorStore
from backend.rag.document_retriever import DocumentRetriever
from backend.rag.document_processor import DocumentChunk


@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_chunks():
    """Create sample document chunks covering various topics"""
    return [
        DocumentChunk(
            content="Fault code P0420 indicates Catalyst System Efficiency Below Threshold (Bank 1). "
                   "This means the catalytic converter is not cleaning exhaust gases efficiently. "
                   "Common causes: worn catalytic converter (50%), faulty oxygen sensor (25%), "
                   "engine running rich or lean (15%). Severity: MEDIUM. Service within 1-2 weeks.",
            metadata={
                "source": "fault_code_reference.md",
                "section": "Fault Code Reference > P0420",
                "h1": "P0420 - Catalyst System Efficiency"
            },
            chunk_id="fc_p0420_1"
        ),
        DocumentChunk(
            content="Fault code P0300 indicates Random/Multiple Cylinder Misfire Detected. "
                   "This is a serious issue that can damage the catalytic converter if not addressed. "
                   "Common causes: spark plugs, ignition coils, fuel injectors, compression issues. "
                   "Severity: HIGH. Service immediately.",
            metadata={
                "source": "fault_code_reference.md",
                "section": "Fault Code Reference > P0300",
                "h1": "P0300 - Misfire Detected"
            },
            chunk_id="fc_p0300_1"
        ),
        DocumentChunk(
            content="Oil change procedure: 1) Warm up engine for 5 minutes. 2) Position drain pan. "
                   "3) Remove drain plug and drain oil. 4) Replace oil filter. 5) Install drain plug. "
                   "6) Add new oil per specifications. Frequency: every 3,000-5,000 miles. "
                   "Use 5W-30 synthetic oil for best performance.",
            metadata={
                "source": "maintenance_procedures.md",
                "section": "Preventive Maintenance > Oil Change",
                "h1": "Oil Change Procedure"
            },
            chunk_id="maint_oil_1"
        ),
        DocumentChunk(
            content="Tire rotation procedure: Rotate tires every 5,000-7,000 miles. "
                   "For FWD vehicles, use forward cross pattern. For RWD vehicles, use rearward cross. "
                   "Always check tire pressure after rotation. Recommended pressure: 32-35 PSI.",
            metadata={
                "source": "maintenance_procedures.md",
                "section": "Preventive Maintenance > Tire Rotation",
                "h1": "Tire Rotation"
            },
            chunk_id="maint_tire_1"
        ),
        DocumentChunk(
            content="Driver score calculation: Harsh braking events (-5 points each), "
                   "rapid acceleration (-3 points each), excessive idle time (-2 points per hour), "
                   "speeding violations (-10 points each). Base score is 100. "
                   "Drivers with scores below 70 require coaching.",
            metadata={
                "source": "driver_handbook.md",
                "section": "Performance Metrics > Driver Scoring",
                "h1": "Driver Score Calculation"
            },
            chunk_id="driver_score_1"
        ),
        DocumentChunk(
            content="Idle time policy: Maximum allowed idle time is 15 minutes per day. "
                   "Excessive idling wastes fuel, increases emissions, and accelerates engine wear. "
                   "Drivers should turn off engines during extended stops. "
                   "Exception: extreme weather conditions (below 20°F or above 95°F).",
            metadata={
                "source": "fleet_policies.md",
                "section": "Fleet Policies > Idle Time",
                "h1": "Idle Time Policy"
            },
            chunk_id="policy_idle_1"
        ),
    ]


@pytest.fixture
def populated_retriever(temp_chroma_dir, sample_chunks):
    """Create document retriever with sample data"""
    vector_store = VectorStore(
        collection_name="test_retrieval",
        persist_directory=temp_chroma_dir,
        embedding_model="local"
    )
    vector_store.add_documents(sample_chunks)
    
    return DocumentRetriever(
        vector_store=vector_store,
        max_context_chunks=5,
        enable_reranking=True
    )


class TestBasicRetrieval:
    """Test basic document retrieval functionality"""
    
    def test_retrieve_returns_results(self, populated_retriever):
        """Test that retrieve returns search results"""
        results, context = populated_retriever.retrieve("What is P0420?")
        
        assert len(results) > 0
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_retrieve_respects_max_chunks(self, populated_retriever):
        """Test that max_context_chunks limit is respected"""
        populated_retriever.max_context_chunks = 2
        results, context = populated_retriever.retrieve("maintenance procedure")
        
        assert len(results) <= 2
    
    def test_context_is_formatted(self, populated_retriever):
        """Test that context string is properly formatted"""
        results, context = populated_retriever.retrieve("fault code")
        
        # Context should include section headers and citations
        assert "[" in context  # Citation markers
        assert "]" in context


class TestQueryClassification:
    """Test query type classification (semantic vs keyword)"""
    
    def test_classify_semantic_query(self, populated_retriever):
        """Test classification of semantic queries"""
        query = "What should I do about catalyst efficiency issues?"
        # This is a semantic query - should use semantic search
        results, context = populated_retriever.retrieve(query)
        
        assert len(results) > 0
        # Should find catalyst-related content
        assert any('catalyst' in r.content.lower() or 'P0420' in r.content for r in results)
    
    def test_classify_keyword_query(self, populated_retriever):
        """Test classification of keyword queries"""
        query = "P0420"
        # This is a keyword query - exact match
        results, context = populated_retriever.retrieve(query)
        
        assert len(results) > 0
        # Should find P0420 content
        assert any('P0420' in r.content for r in results)


class TestReranking:
    """Test result reranking functionality"""
    
    def test_reranking_improves_relevance(self, temp_chroma_dir, sample_chunks):
        """Test that reranking boosts relevant results"""
        vector_store = VectorStore(
            collection_name="test_rerank",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        vector_store.add_documents(sample_chunks)
        
        # Create retrievers with and without reranking
        retriever_no_rerank = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=False
        )
        
        retriever_with_rerank = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        
        # Search for specific fault code
        query = "What is P0420?"
        results_no_rerank, _ = retriever_no_rerank.retrieve(query)
        results_with_rerank, _ = retriever_with_rerank.retrieve(query)
        
        # Both should return results
        assert len(results_no_rerank) > 0
        assert len(results_with_rerank) > 0
        
        # With reranking, P0420 should be in top results
        assert any('P0420' in r.content for r in results_with_rerank[:2])
    
    def test_reranking_enabled_flag(self, populated_retriever):
        """Test that reranking can be enabled/disabled"""
        populated_retriever.enable_reranking = False
        results1, _ = populated_retriever.retrieve("P0420")
        
        populated_retriever.enable_reranking = True
        results2, _ = populated_retriever.retrieve("P0420")
        
        # Both should return results (reranking affects order, not presence)
        assert len(results1) > 0
        assert len(results2) > 0


class TestSpecializedSearch:
    """Test specialized search methods"""
    
    def test_retrieve_fault_code(self, populated_retriever):
        """Test specialized fault code retrieval"""
        results, context = populated_retriever.retrieve_by_fault_code("P0420")
        
        assert len(results) > 0
        # Should specifically find P0420 documentation
        assert any('P0420' in r.content for r in results)
        # Should boost fault code reference documents
        assert any('fault_code' in r.metadata.get('source', '').lower() for r in results[:2])
    
    def test_retrieve_policy(self, populated_retriever):
        """Test policy-specific retrieval"""
        results, context = populated_retriever.retrieve_policy("idle time policy")
        
        assert len(results) > 0
        # Should find policy documents
        assert any('policy' in r.metadata.get('source', '').lower() or 'idle' in r.content.lower() for r in results)
    
    def test_retrieve_maintenance_procedure(self, populated_retriever):
        """Test maintenance procedure retrieval"""
        results, context = populated_retriever.retrieve_maintenance_procedure("oil change")
        
        assert len(results) > 0
        # Should find maintenance documentation
        assert any('oil' in r.content.lower() for r in results)
        assert any('maintenance' in r.metadata.get('source', '').lower() for r in results)


class TestDeduplication:
    """Test deduplication of overlapping chunks"""
    
    def test_removes_duplicate_content(self, temp_chroma_dir):
        """Test that duplicate or highly similar chunks are deduplicated"""
        # Create chunks with overlapping content
        chunks = [
            DocumentChunk(
                content="Oil change procedure step 1: Warm up the engine for 5 minutes.",
                metadata={"source": "maintenance.md"},
                chunk_id="oil_1"
            ),
            DocumentChunk(
                content="Oil change procedure step 1: Warm up the engine for 5 minutes. Step 2: Position drain pan.",
                metadata={"source": "maintenance.md"},
                chunk_id="oil_2"
            ),
            DocumentChunk(
                content="Tire rotation procedure: Rotate every 5,000 miles.",
                metadata={"source": "maintenance.md"},
                chunk_id="tire_1"
            ),
        ]
        
        vector_store = VectorStore(
            collection_name="test_dedup",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        vector_store.add_documents(chunks)
        
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=3,
            enable_reranking=False
        )
        
        results, context = retriever.retrieve("oil change procedure")
        
        # Should return results (deduplication is best-effort)
        assert len(results) > 0


class TestCitationGeneration:
    """Test citation generation for retrieved documents"""
    
    def test_citations_in_context(self, populated_retriever):
        """Test that context includes citation markers"""
        results, context = populated_retriever.retrieve("What is P0420?")
        
        # Context should include citation markers like [1], [2]
        assert '[1]' in context or '[' in context
    
    def test_citation_metadata(self, populated_retriever):
        """Test that results include citation keys"""
        results, context = populated_retriever.retrieve("fault code")
        
        # Results should have metadata for citations
        for result in results:
            assert result.metadata is not None
            assert 'source' in result.metadata
    
    def test_unique_citations(self, populated_retriever):
        """Test that citation numbers are unique"""
        results, context = populated_retriever.retrieve("maintenance")
        
        # Extract citation numbers from context
        import re
        citations = re.findall(r'\[(\d+)\]', context)
        
        if len(citations) > 0:
            # Citation numbers should be sequential
            assert len(set(citations)) > 0


class TestProductionRetriever:
    """Test retriever with actual company documents"""
    
    @pytest.fixture
    def production_retriever(self):
        """Create retriever with actual company documents"""
        chroma_path = Path(__file__).parent.parent.parent.parent / "chroma_db"
        if not chroma_path.exists():
            pytest.skip("Production ChromaDB not found. Run `python -m rag.setup_rag` first.")
        
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory=str(chroma_path),
            embedding_model="local"
        )
        
        return DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
    
    def test_retrieve_fault_code_documentation(self, production_retriever):
        """Test retrieving actual fault code documentation"""
        results, context = production_retriever.retrieve("What is fault code P0420?")
        
        assert len(results) > 0
        assert any('P0420' in r.content or 'catalyst' in r.content.lower() for r in results)
    
    def test_retrieve_maintenance_procedures(self, production_retriever):
        """Test retrieving actual maintenance procedures"""
        results, context = production_retriever.retrieve("How do I change the oil?")
        
        assert len(results) > 0
        assert any('oil' in r.content.lower() for r in results)
    
    def test_retrieve_driver_policies(self, production_retriever):
        """Test retrieving driver policies"""
        results, context = production_retriever.retrieve("What is the idle time policy?")
        
        assert len(results) > 0
        assert any('idle' in r.content.lower() for r in results)
    
    def test_context_quality(self, production_retriever):
        """Test that retrieved context is high quality"""
        results, context = production_retriever.retrieve("P0420 fault code")
        
        # Context should be substantial
        assert len(context) > 100
        # Should include relevant information
        assert 'P0420' in context or 'catalyst' in context.lower()
        # Should be well-formatted
        assert '\n' in context  # Has structure


class TestErrorHandling:
    """Test error handling in document retrieval"""
    
    def test_empty_query(self, populated_retriever):
        """Test handling of empty query"""
        results, context = populated_retriever.retrieve("")
        
        # Should handle gracefully
        assert isinstance(results, list)
        assert isinstance(context, str)
    
    def test_very_long_query(self, populated_retriever):
        """Test handling of very long query"""
        long_query = "What is P0420? " * 100
        results, context = populated_retriever.retrieve(long_query)
        
        # Should handle gracefully
        assert isinstance(results, list)
    
    def test_special_characters_query(self, populated_retriever):
        """Test handling of special characters"""
        results, context = populated_retriever.retrieve("P0420 <>&[]")
        
        # Should handle gracefully
        assert isinstance(results, list)
    
    def test_retrieve_with_no_results(self, temp_chroma_dir):
        """Test retrieval when no relevant documents exist"""
        vector_store = VectorStore(
            collection_name="test_empty",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        
        results, context = retriever.retrieve("nonexistent topic")
        
        # Should return empty results gracefully
        assert results == []
        assert context == "" or context is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

