"""
Document Processing Pipeline for RAG System

Handles:
- Intelligent markdown chunking (preserves structure)
- Metadata extraction
- Chunk optimization for retrieval
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""
    content: str
    metadata: Dict[str, str]
    chunk_id: str
    
    def __repr__(self):
        return f"DocumentChunk(id={self.chunk_id}, size={len(self.content)}, source={self.metadata.get('source')})"


class MarkdownChunker:
    """
    Intelligent markdown chunker that preserves document structure
    and creates semantically meaningful chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks for context continuity
            min_chunk_size: Minimum chunk size (avoid tiny chunks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(self, content: str, source_file: str) -> List[DocumentChunk]:
        """
        Main chunking method that creates semantic chunks from markdown.
        
        Strategy:
        1. Split by headers (h1, h2, h3)
        2. Keep sections together when possible
        3. Split large sections by paragraphs
        4. Add overlap for context continuity
        5. Include metadata (section, subsection, source)
        """
        chunks = []
        global_chunk_num = 0  # Global counter to ensure unique IDs across all sections
        
        # Extract document title
        doc_title = self._extract_title(content)
        
        # Split into sections by headers
        sections = self._split_by_headers(content)
        
        for section in sections:
            section_chunks, global_chunk_num = self._process_section(
                section=section,
                doc_title=doc_title,
                source_file=source_file,
                start_chunk_num=global_chunk_num
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _extract_title(self, content: str) -> str:
        """Extract document title from first h1"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1) if match else "Unknown Document"
    
    def _split_by_headers(self, content: str) -> List[Dict]:
        """
        Split document by markdown headers while preserving hierarchy.
        
        Returns list of sections with:
        - h1, h2, h3 hierarchy
        - Content under each header
        """
        sections = []
        current_h1 = None
        current_h2 = None
        current_h3 = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for headers
            h1_match = re.match(r'^#\s+(.+)$', line)
            h2_match = re.match(r'^##\s+(.+)$', line)
            h3_match = re.match(r'^###\s+(.+)$', line)
            
            if h1_match:
                # Save previous section
                if current_h1 and current_content:
                    sections.append({
                        'h1': current_h1,
                        'h2': current_h2,
                        'h3': current_h3,
                        'content': '\n'.join(current_content)
                    })
                current_h1 = h1_match.group(1)
                current_h2 = None
                current_h3 = None
                current_content = [line]
                
            elif h2_match:
                # Save previous section
                if current_h1 and current_content and len(current_content) > 1:
                    sections.append({
                        'h1': current_h1,
                        'h2': current_h2,
                        'h3': current_h3,
                        'content': '\n'.join(current_content)
                    })
                current_h2 = h2_match.group(1)
                current_h3 = None
                current_content = [line]
                
            elif h3_match:
                # Save previous section
                if current_h1 and current_content and len(current_content) > 1:
                    sections.append({
                        'h1': current_h1,
                        'h2': current_h2,
                        'h3': current_h3,
                        'content': '\n'.join(current_content)
                    })
                current_h3 = h3_match.group(1)
                current_content = [line]
                
            else:
                current_content.append(line)
        
        # Don't forget last section
        if current_h1 and current_content:
            sections.append({
                'h1': current_h1,
                'h2': current_h2,
                'h3': current_h3,
                'content': '\n'.join(current_content)
            })
        
        return sections
    
    def _process_section(
        self,
        section: Dict,
        doc_title: str,
        source_file: str,
        start_chunk_num: int = 0
    ) -> Tuple[List[DocumentChunk], int]:
        """
        Process a section into chunks.
        
        If section is small enough, keep as one chunk.
        If large, split by paragraphs with overlap.
        """
        content = section['content']
        
        # If section is small enough, return as single chunk
        if len(content) <= self.chunk_size:
            return ([self._create_chunk(
                content=content,
                section=section,
                doc_title=doc_title,
                source_file=source_file,
                chunk_num=start_chunk_num
            )], start_chunk_num + 1)
        
        # Section is too large, need to split
        chunks = []
        paragraphs = self._split_paragraphs(content)
        
        current_chunk = []
        current_size = 0
        chunk_num = start_chunk_num
        
        for para in paragraphs:
            para_size = len(para)
            
            # If adding this paragraph exceeds chunk size
            if current_size + para_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    section=section,
                    doc_title=doc_title,
                    source_file=source_file,
                    chunk_num=chunk_num
                ))
                
                # Start new chunk with overlap
                # Keep last paragraph for context continuity
                current_chunk = [current_chunk[-1], para]
                current_size = len(current_chunk[-2]) + para_size
                chunk_num += 1
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Don't forget last chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            if len(chunk_content) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    section=section,
                    doc_title=doc_title,
                    source_file=source_file,
                    chunk_num=chunk_num
                ))
                chunk_num += 1
        
        return chunks, chunk_num
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs, preserving lists and tables"""
        # Split on double newlines, but preserve markdown structures
        paragraphs = re.split(r'\n\n+', content)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _create_chunk(
        self,
        content: str,
        section: Dict,
        doc_title: str,
        source_file: str,
        chunk_num: int
    ) -> DocumentChunk:
        """Create a DocumentChunk with proper metadata"""
        
        # Build hierarchical section path
        section_path = []
        if section.get('h1'):
            section_path.append(section['h1'])
        if section.get('h2'):
            section_path.append(section['h2'])
        if section.get('h3'):
            section_path.append(section['h3'])
        
        section_string = ' > '.join(section_path) if section_path else doc_title
        
        # Extract key terms for better retrieval
        key_terms = self._extract_key_terms(content)
        
        # Build metadata (ChromaDB doesn't accept None or empty strings)
        metadata = {
            'source': source_file,
            'document': doc_title,
            'section': section_string,
            'chunk_num': str(chunk_num),
            'char_count': str(len(content))
        }
        
        # Add optional fields only if they exist
        if section.get('h1'):
            metadata['h1'] = section['h1']
        if section.get('h2'):
            metadata['h2'] = section['h2']
        if section.get('h3'):
            metadata['h3'] = section['h3']
        if key_terms:
            metadata['key_terms'] = ', '.join(key_terms)
        
        # Create unique ID using global chunk number
        # Sanitize filename by removing .md extension
        file_base = source_file.replace('.md', '')
        chunk_id = f"{file_base}:chunk{chunk_num}"
        
        return DocumentChunk(
            content=content,
            metadata=metadata,
            chunk_id=chunk_id
        )
    
    def _extract_key_terms(self, content: str, top_n: int = 10) -> List[str]:
        """
        Extract key terms from content for better retrieval.
        Simple frequency-based extraction (in production, use NER or TF-IDF).
        """
        # Remove markdown formatting
        text = re.sub(r'[#*`\[\]()]', '', content.lower())
        
        # Common words to ignore
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'if', 'then', 'than', 'so'
        }
        
        # Extract words (3+ characters, not stop words)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        words = [w for w in words if w not in stop_words]
        
        # Count frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]


class DocumentProcessor:
    """
    Main document processing pipeline.
    Orchestrates chunking for all company documents.
    """
    
    def __init__(self, docs_directory: str = "company_docs"):
        self.docs_dir = Path(docs_directory)
        self.chunker = MarkdownChunker(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100
        )
    
    def process_all_documents(self) -> List[DocumentChunk]:
        """
        Process all markdown documents in the directory.
        Returns list of all chunks ready for embedding.
        """
        all_chunks = []
        
        # Get all .md files
        md_files = list(self.docs_dir.glob("*.md"))
        
        if not md_files:
            raise FileNotFoundError(f"No .md files found in {self.docs_dir}")
        
        print(f"Processing {len(md_files)} documents...")
        
        for md_file in md_files:
            print(f"  Processing: {md_file.name}")
            
            # Read file
            content = md_file.read_text(encoding='utf-8')
            
            # Chunk document
            chunks = self.chunker.chunk_document(
                content=content,
                source_file=md_file.name
            )
            
            print(f"    Created {len(chunks)} chunks")
            all_chunks.extend(chunks)
        
        print(f"\nTotal chunks created: {len(all_chunks)}")
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """Get statistics about chunks for monitoring"""
        if not chunks:
            return {}
        
        sizes = [len(chunk.content) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(sizes) / len(sizes),
            'min_chunk_size': min(sizes),
            'max_chunk_size': max(sizes),
            'total_characters': sum(sizes),
            'documents_processed': len(set(c.metadata['source'] for c in chunks))
        }


# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor("company_docs")
    
    # Process all documents
    chunks = processor.process_all_documents()
    
    # Get statistics
    stats = processor.get_chunk_statistics(chunks)
    print("\nChunk Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show example chunk
    if chunks:
        print("\nExample Chunk:")
        print(f"  ID: {chunks[0].chunk_id}")
        print(f"  Section: {chunks[0].metadata['section']}")
        print(f"  Content preview: {chunks[0].content[:200]}...")
