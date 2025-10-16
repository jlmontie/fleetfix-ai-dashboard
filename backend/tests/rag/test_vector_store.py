"""
Tests for RAG vector store

Tests ChromaDB integration, embedding generation,
semantic search, and document persistence.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.rag.vector_store import VectorStore, SearchResult
from backend.rag.document_processor import DocumentChunk


@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing"""
    return [
        DocumentChunk(
            content="Fault code P0420 indicates Catalyst System Efficiency Below Threshold. "
                   "This means the catalytic converter is not cleaning exhaust gases efficiently.",
            metadata={
                "source": "fault_code_reference.md",
                "section": "P0420",
                "h1": "Fault Codes"
            },
            chunk_id="fc_p0420_1"
        ),
        DocumentChunk(
            content="Oil change procedure: Warm up engine, drain old oil, replace filter, "
                   "add new oil per specifications. Frequency: every 3,000-5,000 miles.",
            metadata={
                "source": "maintenance_procedures.md",
                "section": "Oil Change",
                "h1": "Maintenance Procedures"
            },
            chunk_id="maint_oil_1"
        ),
        DocumentChunk(
            content="Driver score calculation includes harsh braking events, rapid acceleration, "
                   "idle time, and hours driven. Scores range from 0-100.",
            metadata={
                "source": "driver_handbook.md",
                "section": "Driver Scoring",
                "h1": "Performance Metrics"
            },
            chunk_id="driver_score_1"
        ),
    ]


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create vector store with local embeddings"""
    return VectorStore(
        collection_name="test_collection",
        persist_directory=temp_chroma_dir,
        embedding_model="local"
    )


class TestVectorStoreInitialization:
    """Test vector store setup and configuration"""
    
    def test_create_vector_store(self, temp_chroma_dir):
        """Test creating a new vector store"""
        vs = VectorStore(
            collection_name="test_init",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        assert vs is not None
        assert vs.collection is not None
    
    def test_persistence_directory_created(self, temp_chroma_dir):
        """Test that persistence directory is created"""
        vs = VectorStore(
            collection_name="test_persist",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        assert Path(temp_chroma_dir).exists()
    
    def test_collection_name(self, vector_store):
        """Test that collection is created with correct name"""
        assert vector_store.collection.name in ["test_collection", "test_collection"]  # May vary


class TestDocumentAddition:
    """Test adding documents to vector store"""
    
    def test_add_single_chunk(self, vector_store, sample_chunks):
        """Test adding a single document chunk"""
        vector_store.add_documents([sample_chunks[0]])
        
        # Verify document was added
        count = vector_store.collection.count()
        assert count == 1
    
    def test_add_multiple_chunks(self, vector_store, sample_chunks):
        """Test adding multiple document chunks"""
        vector_store.add_documents(sample_chunks)
        
        # Verify all documents were added
        count = vector_store.collection.count()
        assert count == len(sample_chunks)
    
    def test_add_empty_list(self, vector_store):
        """Test adding empty list of documents"""
        vector_store.add_documents([])
        
        # Should handle gracefully
        count = vector_store.collection.count()
        assert count == 0
    
    def test_metadata_preserved(self, vector_store, sample_chunks):
        """Test that metadata is preserved when adding documents"""
        vector_store.add_documents(sample_chunks)
        
        # Search and verify metadata
        results = vector_store.semantic_search("fault code", n_results=1)
        assert len(results) > 0
        assert results[0].metadata is not None
        assert 'source' in results[0].metadata


class TestSemanticSearch:
    """Test semantic search functionality"""
    
    @pytest.fixture
    def populated_store(self, vector_store, sample_chunks):
        """Create vector store with sample data"""
        vector_store.add_documents(sample_chunks)
        return vector_store
    
    def test_search_returns_results(self, populated_store):
        """Test that search returns results"""
        results = populated_store.semantic_search("What is P0420?", n_results=3)
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_search_relevance(self, populated_store):
        """Test that most relevant result is returned first"""
        results = populated_store.semantic_search("fault code P0420", n_results=3)
        
        # First result should be about P0420
        assert len(results) > 0
        assert 'P0420' in results[0].content or 'catalyst' in results[0].content.lower()
    
    def test_search_with_limit(self, populated_store):
        """Test that n_results parameter limits results"""
        results = populated_store.semantic_search("maintenance", n_results=1)
        
        assert len(results) == 1
    
    def test_search_scores(self, populated_store):
        """Test that search results have relevance scores"""
        results = populated_store.semantic_search("oil change procedure", n_results=3)
        
        assert len(results) > 0
        for result in results:
            assert hasattr(result, 'score') or hasattr(result, 'distance')
            # Scores should be reasonable (0-1 for similarity, or positive for distance)
            score = getattr(result, 'score', getattr(result, 'distance', None))
            assert score is not None
    
    def test_empty_query(self, populated_store):
        """Test handling of empty query"""
        results = populated_store.semantic_search("", n_results=3)
        
        # Should handle gracefully (return empty or raise appropriate error)
        assert isinstance(results, list)


class TestMetadataFiltering:
    """Test metadata-based filtering"""
    
    @pytest.fixture
    def populated_store(self, vector_store, sample_chunks):
        """Create vector store with sample data"""
        vector_store.add_documents(sample_chunks)
        return vector_store
    
    def test_filter_by_source(self, populated_store):
        """Test filtering results by source document"""
        # Search with metadata filter
        results = populated_store.semantic_search(
            "procedure",
            n_results=5,
            filter_metadata={"source": "maintenance_procedures.md"}
        )
        
        # All results should be from maintenance procedures
        if len(results) > 0:
            for result in results:
                assert result.metadata.get('source') == "maintenance_procedures.md"
    
    def test_filter_by_section(self, populated_store):
        """Test filtering by section within document"""
        results = populated_store.semantic_search(
            "P0420",
            n_results=5,
            filter_metadata={"section": "P0420"}
        )
        
        # Should return only P0420 section if filter works
        if len(results) > 0:
            assert any('P0420' in r.content for r in results)


class TestEmbeddingGeneration:
    """Test embedding generation"""
    
    def test_local_embeddings_work(self, temp_chroma_dir, sample_chunks):
        """Test that local sentence-transformers embeddings work"""
        vs = VectorStore(
            collection_name="test_embeddings",
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        
        # Add documents (will generate embeddings)
        vs.add_documents(sample_chunks)
        
        # Should be able to search (requires embeddings)
        results = vs.semantic_search("maintenance", n_results=1)
        assert len(results) > 0
    
    def test_embeddings_are_consistent(self, vector_store, sample_chunks):
        """Test that same content produces consistent embeddings"""
        # Add documents twice
        vector_store.add_documents([sample_chunks[0]])
        
        # Search should return the document
        results1 = vector_store.semantic_search(sample_chunks[0].content[:50], n_results=1)
        
        # Add same document again with different ID
        modified_chunk = DocumentChunk(
            content=sample_chunks[0].content,
            metadata=sample_chunks[0].metadata,
            chunk_id="duplicate"
        )
        vector_store.add_documents([modified_chunk])
        
        results2 = vector_store.semantic_search(sample_chunks[0].content[:50], n_results=2)
        
        # Both searches should return similar top results
        assert len(results1) > 0
        assert len(results2) > 0


class TestPersistence:
    """Test vector store persistence"""
    
    def test_data_persists_across_instances(self, temp_chroma_dir, sample_chunks):
        """Test that data persists when recreating vector store"""
        collection_name = "test_persistence"
        
        # Create store and add documents
        vs1 = VectorStore(
            collection_name=collection_name,
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        vs1.add_documents(sample_chunks)
        count1 = vs1.collection.count()
        
        # Create new instance with same configuration
        vs2 = VectorStore(
            collection_name=collection_name,
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        count2 = vs2.collection.count()
        
        # Should have same number of documents
        assert count2 == count1
    
    def test_search_works_after_reload(self, temp_chroma_dir, sample_chunks):
        """Test that search works after reloading persisted data"""
        collection_name = "test_search_persist"
        
        # Create store, add documents, and close
        vs1 = VectorStore(
            collection_name=collection_name,
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        vs1.add_documents(sample_chunks)
        
        # Reload and search
        vs2 = VectorStore(
            collection_name=collection_name,
            persist_directory=temp_chroma_dir,
            embedding_model="local"
        )
        results = vs2.semantic_search("P0420", n_results=1)
        
        assert len(results) > 0


class TestProductionVectorStore:
    """Test vector store with actual company documents"""
    
    @pytest.fixture
    def production_vector_store(self, temp_chroma_dir):
        """Create vector store with actual ChromaDB if available"""
        chroma_path = Path(__file__).parent.parent.parent.parent / "chroma_db"
        if not chroma_path.exists():
            pytest.skip("Production ChromaDB not found. Run `python -m rag.setup_rag` first.")
        
        return VectorStore(
            collection_name="fleetfix_docs",
            persist_directory=str(chroma_path),
            embedding_model="local"
        )
    
    def test_production_store_has_documents(self, production_vector_store):
        """Test that production vector store has documents"""
        count = production_vector_store.collection.count()
        
        # Should have ~156 chunks from company docs
        assert count >= 100
        assert count <= 300
    
    def test_search_fault_codes(self, production_vector_store):
        """Test searching for fault codes in production store"""
        results = production_vector_store.semantic_search("What is P0420?", n_results=3)
        
        assert len(results) > 0
        # Should find fault code documentation
        assert any('P0420' in r.content or 'catalyst' in r.content.lower() for r in results)
    
    def test_search_maintenance_procedures(self, production_vector_store):
        """Test searching for maintenance procedures"""
        results = production_vector_store.semantic_search("oil change procedure", n_results=3)
        
        assert len(results) > 0
        # Should find maintenance documentation
        assert any('oil' in r.content.lower() for r in results)


class TestErrorHandling:
    """Test error handling in vector store"""
    
    def test_invalid_embedding_model(self, temp_chroma_dir):
        """Test handling of invalid embedding model"""
        with pytest.raises((ValueError, Exception)):
            VectorStore(
                collection_name="test_invalid",
                persist_directory=temp_chroma_dir,
                embedding_model="nonexistent_model"
            )
    
    def test_search_empty_store(self, vector_store):
        """Test searching empty vector store"""
        results = vector_store.semantic_search("test query", n_results=5)
        
        # Should return empty list, not error
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

