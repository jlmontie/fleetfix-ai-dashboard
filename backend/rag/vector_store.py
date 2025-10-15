"""
Vector Store Implementation using ChromaDB

Handles:
- Embedding generation (OpenAI or local sentence-transformers)
- Vector storage and indexing
- Semantic search
- Metadata filtering
- Hybrid search (semantic + keyword)
"""

import os
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import numpy as np

from .document_processor import DocumentChunk


@dataclass
class SearchResult:
    """Represents a search result with score and metadata"""
    content: str
    metadata: Dict[str, str]
    score: float
    chunk_id: str
    
    def __repr__(self):
        return f"SearchResult(score={self.score:.3f}, section={self.metadata.get('section', 'N/A')})"


class EmbeddingModel:
    """
    Wrapper for embedding generation.
    Supports both local (sentence-transformers) and API-based (OpenAI) models.
    """
    
    def __init__(
        self,
        model_type: Literal["local", "openai"] = "local",
        model_name: Optional[str] = None
    ):
        """
        Args:
            model_type: "local" for sentence-transformers, "openai" for OpenAI
            model_name: Model name (defaults to good choices for each type)
        """
        self.model_type = model_type
        
        if model_type == "local":
            # Use all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
            # Alternative: all-mpnet-base-v2 (768 dims, higher quality, slower)
            self.model_name = model_name or "all-MiniLM-L6-v2"
            print(f"Loading local embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
        elif model_type == "openai":
            # Use OpenAI's text-embedding-3-small (1536 dims)
            self.model_name = model_name or "text-embedding-3-small"
            # ChromaDB has built-in OpenAI support
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required for OpenAI embeddings")
            self.model = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=self.model_name
            )
            self.dimension = 1536  # text-embedding-3-small dimension
        
        print(f"Embedding dimension: {self.dimension}")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if self.model_type == "local":
            embeddings = self.model.encode(
                texts,
                show_progress_bar=True,
                batch_size=32
            )
            return embeddings.tolist()
        else:
            # OpenAI embedding function
            return self.model(texts)
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        if self.model_type == "local":
            embedding = self.model.encode([query])[0]
            return embedding.tolist()
        else:
            return self.model([query])[0]


class VectorStore:
    """
    ChromaDB-based vector store for document retrieval.
    
    Features:
    - Efficient similarity search
    - Metadata filtering
    - Persistent storage
    - Hybrid search (semantic + keyword)
    """
    
    def __init__(
        self,
        collection_name: str = "fleetfix_docs",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "local",
        model_name: Optional[str] = None
    ):
        """
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Where to store the vector database
            embedding_model: "local" or "openai"
            model_name: Specific model name (optional)
        """
        self.collection_name = collection_name
        
        # Initialize embedding model
        self.embedding_model = EmbeddingModel(
            model_type=embedding_model,
            model_name=model_name
        )
        
        # Initialize ChromaDB client
        print(f"Initializing ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=self.collection_name
            )
            print(f"Loaded existing collection: {self.collection_name}")
            print(f"  Documents in collection: {collection.count()}")
            return collection
        except:
            # Create new collection
            print(f"Creating new collection: {self.collection_name}")
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            return collection
    
    def add_documents(self, chunks: List[DocumentChunk], batch_size: int = 50):
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of DocumentChunk objects
            batch_size: Number of chunks to process at once
        """
        print(f"\nIndexing {len(chunks)} chunks into vector store...")
        
        # Process in batches for efficiency
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data
            ids = [chunk.chunk_id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]
            
            # Generate embeddings
            print(f"  Embedding batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
            embeddings = self.embedding_model.embed(documents)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        
        print(f"✓ Indexed {len(chunks)} chunks successfully")
        print(f"  Total documents in collection: {self.collection.count()}")
    
    def semantic_search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"source": "maintenance_procedures.md"})
        
        Returns:
            List of SearchResult objects sorted by relevance
        """
        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        for i in range(len(results['ids'][0])):
            # ChromaDB returns distances, convert to similarity scores (1 - distance for cosine)
            distance = results['distances'][0][i]
            similarity_score = 1 - distance
            
            search_results.append(SearchResult(
                content=results['documents'][0][i],
                metadata=results['metadatas'][0][i],
                score=similarity_score,
                chunk_id=results['ids'][0][i]
            ))
        
        return search_results
    
    def keyword_search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Perform keyword-based search (full-text search).
        Uses ChromaDB's where_document functionality.
        """
        # Create keyword search condition
        # ChromaDB supports basic text matching
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            similarity_score = 1 - distance
            
            search_results.append(SearchResult(
                content=results['documents'][0][i],
                metadata=results['metadatas'][0][i],
                score=similarity_score,
                chunk_id=results['ids'][0][i]
            ))
        
        return search_results
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        semantic_weight: float = 0.7,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic search (0-1), keyword gets (1 - semantic_weight)
            filter_metadata: Optional metadata filters
        
        Returns:
            List of SearchResult objects with combined scores
        """
        # Get more results from each method, then combine
        n_each = n_results * 2
        
        # Perform both searches
        semantic_results = self.semantic_search(query, n_each, filter_metadata)
        keyword_results = self.keyword_search(query, n_each, filter_metadata)
        
        # Combine scores
        combined_scores = {}
        
        # Add semantic scores
        for result in semantic_results:
            combined_scores[result.chunk_id] = {
                'result': result,
                'semantic_score': result.score,
                'keyword_score': 0
            }
        
        # Add keyword scores
        for result in keyword_results:
            if result.chunk_id in combined_scores:
                combined_scores[result.chunk_id]['keyword_score'] = result.score
            else:
                combined_scores[result.chunk_id] = {
                    'result': result,
                    'semantic_score': 0,
                    'keyword_score': result.score
                }
        
        # Calculate combined scores
        for chunk_id, scores in combined_scores.items():
            combined_score = (
                semantic_weight * scores['semantic_score'] +
                (1 - semantic_weight) * scores['keyword_score']
            )
            scores['combined_score'] = combined_score
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        # Return top N with updated scores
        final_results = []
        for item in sorted_results[:n_results]:
            result = item['result']
            result.score = item['combined_score']
            final_results.append(result)
        
        return final_results
    
    def search_by_document(self, document_name: str, n_results: int = 10) -> List[SearchResult]:
        """Get all chunks from a specific document"""
        return self.semantic_search(
            query="",  # Empty query
            n_results=n_results,
            filter_metadata={"source": document_name}
        )
    
    def search_by_section(self, section_query: str, n_results: int = 5) -> List[SearchResult]:
        """Search within specific document sections"""
        # Use metadata to filter by section hierarchy
        return self.semantic_search(query=section_query, n_results=n_results)
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_chunks': self.collection.count(),
            'collection_name': self.collection_name,
            'embedding_dimension': self.embedding_model.dimension,
            'embedding_model': self.embedding_model.model_name
        }
    
    def reset(self):
        """Delete all documents from the collection (useful for re-indexing)"""
        self.client.delete_collection(self.collection_name)
        self.collection = self._get_or_create_collection()
        print("Collection reset successfully")


# Utility function for query classification
def classify_query_type(query: str) -> str:
    """
    Classify query to determine best search strategy.
    
    Returns:
        'semantic': For conceptual queries
        'keyword': For specific terms/codes
        'hybrid': For mixed queries
    """
    query_lower = query.lower()
    
    # Keyword indicators: specific codes, exact terms
    keyword_indicators = [
        r'p0\d{3}',  # Fault codes like P0420
        r'code',
        r'procedure',
        r'policy',
        'specific',
        'exact'
    ]
    
    # Semantic indicators: conceptual questions
    semantic_indicators = [
        'what is',
        'explain',
        'how does',
        'why',
        'tell me about',
        'describe',
        'understand'
    ]
    
    import re
    
    has_keyword = any(re.search(pattern, query_lower) for pattern in keyword_indicators)
    has_semantic = any(indicator in query_lower for indicator in semantic_indicators)
    
    if has_keyword and not has_semantic:
        return 'keyword'
    elif has_semantic and not has_keyword:
        return 'semantic'
    else:
        return 'hybrid'


# Example usage
if __name__ == "__main__":
    from document_processor import DocumentProcessor
    
    # Process documents
    processor = DocumentProcessor("company_docs")
    chunks = processor.process_all_documents()
    
    # Initialize vector store (use "local" for free, "openai" for better quality)
    vector_store = VectorStore(
        collection_name="fleetfix_docs",
        persist_directory="./chroma_db",
        embedding_model="local"  # Change to "openai" if you have API key
    )
    
    # Index documents (only needed once, then persisted)
    if vector_store.collection.count() == 0:
        vector_store.add_documents(chunks)
    
    # Show statistics
    stats = vector_store.get_statistics()
    print("\nVector Store Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test searches
    print("\n" + "="*60)
    print("Testing Search Functionality")
    print("="*60)
    
    test_queries = [
        "What is fault code P0420?",
        "Oil change procedure",
        "Driver score calculation",
        "What happens if a driver has harsh braking events?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print(f"Query type: {classify_query_type(query)}")
        
        # Perform hybrid search
        results = vector_store.hybrid_search(query, n_results=3)
        
        print(f"Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. Score: {result.score:.3f}")
            print(f"     Section: {result.metadata['section']}")
            print(f"     Preview: {result.content[:150]}...")
