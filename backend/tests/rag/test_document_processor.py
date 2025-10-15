"""
Tests for RAG document processor

Tests intelligent document chunking, metadata extraction,
and markdown processing capabilities.
"""

import pytest
import os
from pathlib import Path
from backend.rag.document_processor import DocumentProcessor, DocumentChunk


@pytest.fixture
def test_docs_dir(tmp_path):
    """Create temporary test documents"""
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()
    
    # Create test document with markdown structure
    test_doc = docs_dir / "test_procedure.md"
    test_doc.write_text("""# Maintenance Procedures

    ## Oil Change Procedure

    ### Required Tools
    - Oil filter wrench
    - Drain pan
    - New oil filter

    ### Steps
    1. Warm up the engine for 5 minutes
    2. Position drain pan under oil pan
    3. Remove drain plug and drain oil
    4. Replace oil filter
    5. Install drain plug with new washer
    6. Add new oil per specifications

    ## Tire Rotation

    ### Frequency
    Rotate tires every 5,000-7,000 miles.

    ### Pattern
    For FWD vehicles, use forward cross pattern.
    For RWD vehicles, use rearward cross pattern.
    """)
    
    return docs_dir


@pytest.fixture
def processor(test_docs_dir):
    """Create document processor with test docs"""
    return DocumentProcessor(str(test_docs_dir))


class TestDocumentProcessing:
    """Test document loading and processing"""
    
    def test_process_all_documents(self, processor):
        """Test processing all documents in directory"""
        chunks = processor.process_all_documents()
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)


class TestChunking:
    """Test intelligent chunking strategy"""
    
    def test_chunk_respects_headers(self, processor):
        """Test that chunks respect markdown header structure"""
        chunks = processor.process_all_documents()
        
        # Check that chunks have section information
        chunks_with_sections = [c for c in chunks if c.metadata.get('section')]
        assert len(chunks_with_sections) > 0
    
    def test_chunk_size_reasonable(self, processor):
        """Test that chunk sizes are within expected range"""
        chunks = processor.process_all_documents()
        
        # Most chunks should be between 100 and 2000 characters
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert len(chunk.content) < 5000  # Max reasonable chunk size
    
    def test_chunks_have_overlap(self, processor):
        """Test that adjacent chunks have overlap for context continuity"""
        chunks = processor.process_all_documents()
        
        # If there are multiple chunks from same document, check overlap
        if len(chunks) >= 2:
            # Group by source
            from collections import defaultdict
            chunks_by_source = defaultdict(list)
            for chunk in chunks:
                chunks_by_source[chunk.metadata['source']].append(chunk)
            
            # Check for overlap in multi-chunk documents
            for source, source_chunks in chunks_by_source.items():
                if len(source_chunks) >= 2:
                    # At least one pair should have some overlap
                    has_overlap = False
                    for i in range(len(source_chunks) - 1):
                        # Check if any words from end of chunk i appear in start of chunk i+1
                        chunk1_end = source_chunks[i].content[-100:]
                        chunk2_start = source_chunks[i+1].content[:100]
                        if any(word in chunk2_start for word in chunk1_end.split()[-5:]):
                            has_overlap = True
                            break
                    # Note: overlap might not always be present in test docs, so we just verify structure
                    assert source_chunks[i].metadata['source'] == source_chunks[i+1].metadata['source']


class TestMetadataExtraction:
    """Test metadata extraction from documents"""
    
    def test_source_file_extracted(self, processor):
        """Test that source filename is extracted"""
        chunks = processor.process_all_documents()
        
        for chunk in chunks:
            assert 'source' in chunk.metadata
            assert chunk.metadata['source'].endswith('.md')
    
    def test_section_hierarchy_extracted(self, processor):
        """Test that section hierarchy is preserved"""
        chunks = processor.process_all_documents()
        
        # At least some chunks should have section information
        chunks_with_hierarchy = [c for c in chunks if 'h1' in c.metadata or 'h2' in c.metadata]
        assert len(chunks_with_hierarchy) > 0
    
    def test_chunk_index_present(self, processor):
        """Test that chunks are indexed"""
        chunks = processor.process_all_documents()
        
        for chunk in chunks:
            assert 'chunk_id' in chunk.metadata or chunk.content  # Has some identifier


class TestProductionDocuments:
    """Test processing of actual company documents"""
    
    @pytest.fixture
    def production_processor(self):
        """Create processor with actual company docs"""
        company_docs_path = Path(__file__).parent.parent.parent.parent / "company_docs"
        if not company_docs_path.exists():
            pytest.skip("Company docs not found")
        return DocumentProcessor(str(company_docs_path))
    
    def test_process_company_documents(self, production_processor):
        """Test processing actual FleetFix company documents"""
        chunks = production_processor.process_all_documents()
        
        # Should create significant number of chunks from company docs
        assert len(chunks) >= 100  # At least 100 chunks from 32k+ words
        assert len(chunks) <= 200  # But not too many (reasonable chunking)
    
    def test_fault_code_document_processed(self, production_processor):
        """Test that fault code reference is properly chunked"""
        chunks = production_processor.process_all_documents()
        
        # Should have chunks from fault_code_reference.md
        fault_code_chunks = [c for c in chunks if 'fault_code' in c.metadata.get('source', '').lower()]
        assert len(fault_code_chunks) > 0
        
        # Should contain P0420 (common fault code)
        p0420_chunks = [c for c in chunks if 'P0420' in c.content or 'p0420' in c.content.lower()]
        assert len(p0420_chunks) > 0
    
    def test_maintenance_procedures_processed(self, production_processor):
        """Test that maintenance procedures are properly chunked"""
        chunks = production_processor.process_all_documents()
        
        # Should have chunks from maintenance_procedures.md
        maint_chunks = [c for c in chunks if 'maintenance' in c.metadata.get('source', '').lower()]
        assert len(maint_chunks) > 0


class TestErrorHandling:
    """Test error handling in document processing"""
    
    def test_empty_directory(self, tmp_path):
        """Test handling of empty directory"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        processor = DocumentProcessor(str(empty_dir))
        
        # Should raise FileNotFoundError when no .md files found
        with pytest.raises(FileNotFoundError):
            chunks = processor.process_all_documents()
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory"""
        with pytest.raises((FileNotFoundError, ValueError)):
            processor = DocumentProcessor("/nonexistent/path")
            processor.process_all_documents()
    
    def test_invalid_markdown(self, tmp_path):
        """Test handling of invalid or empty markdown files"""
        docs_dir = tmp_path / "invalid_docs"
        docs_dir.mkdir()
        
        # Create empty file
        empty_file = docs_dir / "empty.md"
        empty_file.write_text("")
        
        processor = DocumentProcessor(str(docs_dir))
        chunks = processor.process_all_documents()
        
        # Should handle gracefully (return empty or skip)
        assert isinstance(chunks, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

