"""
Document Retriever with Reranking

This is the main interface for the RAG system.
Handles:
- Query understanding
- Retrieval strategy selection
- Result reranking
- Context formatting for LLM
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

from .vector_store import VectorStore, SearchResult, classify_query_type


@dataclass
class RetrievalResult:
    """
    Enhanced result with reranking and citation info.
    """
    content: str
    metadata: Dict[str, str]
    relevance_score: float
    original_score: float
    chunk_id: str
    citation_key: str  # For LLM citations [1], [2], etc.
    
    def format_for_context(self) -> str:
        """Format chunk for inclusion in LLM context"""
        section = self.metadata.get('section', 'Unknown')
        source = self.metadata.get('source', 'Unknown')
        
        return f"""[{self.citation_key}] From: {source} - {section}

{self.content}
"""
    
    def format_citation(self) -> str:
        """Format citation for display to user"""
        return f"[{self.citation_key}] {self.metadata.get('section')} ({self.metadata.get('source')})"


class ReRanker:
    """
    Simple reranking based on query-specific rules.
    
    In production, consider:
    - Cross-encoder models (e.g., ms-marco-MiniLM)
    - LLM-based reranking
    - Click-through data
    """
    
    def __init__(self):
        # Boost scores for specific document types based on query
        self.document_boost = {
            'maintenance': 'maintenance_procedures.md',
            'service': 'maintenance_procedures.md',
            'repair': 'maintenance_procedures.md',
            'fault': 'fault_code_reference.md',
            'code': 'fault_code_reference.md',
            'p0': 'fault_code_reference.md',
            'dtc': 'fault_code_reference.md',
            'driver': 'driver_handbook.md',
            'score': 'driver_handbook.md',
            'performance': 'driver_handbook.md',
            'policy': 'fleet_policies.md',
            'compliance': 'fleet_policies.md',
            'fuel': 'fleet_policies.md'
        }
    
    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        boost_factor: float = 1.2
    ) -> List[RetrievalResult]:
        """
        Rerank results based on query understanding.
        
        Args:
            query: Original query
            results: Initial search results
            boost_factor: How much to boost relevant document scores
        
        Returns:
            Reranked list of RetrievalResult objects
        """
        query_lower = query.lower()
        reranked = []
        
        for i, result in enumerate(results):
            score = result.score
            
            # Boost score if document type matches query intent
            for keyword, doc_name in self.document_boost.items():
                if keyword in query_lower and result.metadata.get('source') == doc_name:
                    score *= boost_factor
                    break
            
            # Boost if query terms appear in section headers
            section = result.metadata.get('section', '').lower()
            query_terms = set(query_lower.split())
            section_terms = set(section.split())
            
            # Boost for header matches
            if query_terms & section_terms:
                score *= 1.1
            
            # Boost for exact phrase matches in content
            if query_lower in result.content.lower():
                score *= 1.15
            
            # Create RetrievalResult
            reranked.append(RetrievalResult(
                content=result.content,
                metadata=result.metadata,
                relevance_score=score,
                original_score=result.score,
                chunk_id=result.chunk_id,
                citation_key=str(i + 1)
            ))
        
        # Sort by new relevance score
        reranked.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update citation keys after reranking
        for i, result in enumerate(reranked):
            result.citation_key = str(i + 1)
        
        return reranked
    
    def filter_duplicates(
        self,
        results: List[RetrievalResult],
        similarity_threshold: float = 0.85
    ) -> List[RetrievalResult]:
        """
        Remove near-duplicate results (from overlapping chunks).
        
        Simple implementation using content similarity.
        In production, use MinHash or SimHash.
        """
        filtered = []
        seen_content = []
        
        for result in results:
            content = result.content.lower()
            
            # Check if too similar to any already selected result
            is_duplicate = False
            for seen in seen_content:
                # Simple overlap measure
                overlap = len(set(content.split()) & set(seen.split()))
                total = len(set(content.split()) | set(seen.split()))
                similarity = overlap / total if total > 0 else 0
                
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(result)
                seen_content.append(content)
        
        return filtered


class DocumentRetriever:
    """
    Main RAG retrieval interface.
    
    This is what your AI agent will use to retrieve relevant context.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        max_context_chunks: int = 5,
        enable_reranking: bool = True
    ):
        """
        Args:
            vector_store: Initialized VectorStore instance
            max_context_chunks: Maximum chunks to include in context
            enable_reranking: Whether to apply reranking
        """
        self.vector_store = vector_store
        self.max_context_chunks = max_context_chunks
        self.enable_reranking = enable_reranking
        self.reranker = ReRanker() if enable_reranking else None
    
    def retrieve(
        self,
        query: str,
        n_results: int = None,
        filter_source: Optional[str] = None
    ) -> Tuple[List[RetrievalResult], str]:
        """
        Main retrieval method.
        
        Args:
            query: User query
            n_results: Number of results (defaults to max_context_chunks)
            filter_source: Optional source document filter
        
        Returns:
            Tuple of (results, formatted_context_string)
        """
        n_results = n_results or self.max_context_chunks
        
        # Classify query type
        query_type = classify_query_type(query)
        
        # Prepare metadata filter
        filter_metadata = {"source": filter_source} if filter_source else None
        
        # Choose search strategy based on query type
        if query_type == 'semantic':
            raw_results = self.vector_store.semantic_search(
                query=query,
                n_results=n_results * 2,  # Get extra for reranking/filtering
                filter_metadata=filter_metadata
            )
        elif query_type == 'keyword':
            raw_results = self.vector_store.keyword_search(
                query=query,
                n_results=n_results * 2,
                filter_metadata=filter_metadata
            )
        else:  # hybrid
            raw_results = self.vector_store.hybrid_search(
                query=query,
                n_results=n_results * 2,
                filter_metadata=filter_metadata
            )
        
        # Apply reranking if enabled
        if self.enable_reranking and self.reranker:
            results = self.reranker.rerank(query, raw_results)
            results = self.reranker.filter_duplicates(results)
        else:
            # Convert to RetrievalResult without reranking
            results = [
                RetrievalResult(
                    content=r.content,
                    metadata=r.metadata,
                    relevance_score=r.score,
                    original_score=r.score,
                    chunk_id=r.chunk_id,
                    citation_key=str(i + 1)
                )
                for i, r in enumerate(raw_results)
            ]
        
        # Take top N after reranking
        results = results[:n_results]
        
        # Format context for LLM
        context = self._format_context(results)
        
        return results, context
    
    def retrieve_by_fault_code(self, fault_code: str) -> Tuple[List[RetrievalResult], str]:
        """
        Specialized retrieval for fault codes.
        Always searches fault_code_reference.md
        """
        # Normalize fault code (e.g., p0420 -> P0420)
        fault_code = fault_code.upper()
        
        return self.retrieve(
            query=f"fault code {fault_code}",
            filter_source="fault_code_reference.md",
            n_results=3
        )
    
    def retrieve_policy(self, policy_topic: str) -> Tuple[List[RetrievalResult], str]:
        """
        Specialized retrieval for policies.
        Searches relevant policy documents.
        """
        # Try driver handbook first for driver-related queries
        if any(term in policy_topic.lower() for term in ['driver', 'score', 'performance']):
            sources = ['driver_handbook.md', 'fleet_policies.md']
        else:
            sources = ['fleet_policies.md', 'driver_handbook.md']
        
        all_results = []
        for source in sources:
            results, _ = self.retrieve(
                query=policy_topic,
                filter_source=source,
                n_results=2
            )
            all_results.extend(results)
        
        # Rerank combined results
        if self.enable_reranking:
            # Convert back to SearchResult for reranking
            search_results = [
                SearchResult(
                    content=r.content,
                    metadata=r.metadata,
                    score=r.relevance_score,
                    chunk_id=r.chunk_id
                )
                for r in all_results
            ]
            all_results = self.reranker.rerank(policy_topic, search_results)
        
        # Take top results
        final_results = all_results[:self.max_context_chunks]
        context = self._format_context(final_results)
        
        return final_results, context
    
    def retrieve_maintenance_procedure(
        self,
        procedure_query: str
    ) -> Tuple[List[RetrievalResult], str]:
        """
        Specialized retrieval for maintenance procedures.
        """
        return self.retrieve(
            query=procedure_query,
            filter_source="maintenance_procedures.md",
            n_results=self.max_context_chunks
        )
    
    def _format_context(self, results: List[RetrievalResult]) -> str:
        """
        Format retrieved chunks into a context string for the LLM.
        
        Includes:
        - Citation markers
        - Source information
        - Clear chunk separation
        """
        if not results:
            return "No relevant information found in company documents."
        
        context_parts = [
            "=== RELEVANT COMPANY DOCUMENTATION ===\n",
            f"Retrieved {len(results)} relevant sections:\n"
        ]
        
        for result in results:
            context_parts.append(result.format_for_context())
            context_parts.append("\n" + "-" * 60 + "\n")
        
        context_parts.append("\n=== END DOCUMENTATION ===")
        
        return "\n".join(context_parts)
    
    def get_citations(self, results: List[RetrievalResult]) -> List[str]:
        """
        Get formatted citations for user display.
        """
        return [result.format_citation() for result in results]
    
    def debug_search(self, query: str, n_results: int = 5) -> Dict:
        """
        Debug method to see how different search strategies perform.
        Useful for tuning the system.
        """
        results = {}
        
        # Semantic search
        semantic = self.vector_store.semantic_search(query, n_results)
        results['semantic'] = [
            {
                'score': r.score,
                'section': r.metadata.get('section'),
                'preview': r.content[:100]
            }
            for r in semantic
        ]
        
        # Keyword search
        keyword = self.vector_store.keyword_search(query, n_results)
        results['keyword'] = [
            {
                'score': r.score,
                'section': r.metadata.get('section'),
                'preview': r.content[:100]
            }
            for r in keyword
        ]
        
        # Hybrid search
        hybrid = self.vector_store.hybrid_search(query, n_results)
        results['hybrid'] = [
            {
                'score': r.score,
                'section': r.metadata.get('section'),
                'preview': r.content[:100]
            }
            for r in hybrid
        ]
        
        return results


# Example usage
if __name__ == "__main__":
    from rag.document_processor import DocumentProcessor
    from rag.vector_store import VectorStore
    
    # Initialize system
    print("Initializing RAG system...")
    
    # Process documents
    processor = DocumentProcessor("company_docs")
    chunks = processor.process_all_documents()
    
    # Initialize vector store
    vector_store = VectorStore(
        collection_name="fleetfix_docs",
        persist_directory="./chroma_db",
        embedding_model="local"
    )
    
    # Index if needed
    if vector_store.collection.count() == 0:
        vector_store.add_documents(chunks)
    
    # Initialize retriever
    retriever = DocumentRetriever(
        vector_store=vector_store,
        max_context_chunks=5,
        enable_reranking=True
    )
    
    # Test queries
    print("\n" + "="*80)
    print("RAG SYSTEM DEMO")
    print("="*80)
    
    test_cases = [
        {
            'query': "What should I do about fault code P0420?",
            'description': "Fault code query"
        },
        {
            'query': "Oil change procedure and cost",
            'description': "Maintenance procedure"
        },
        {
            'query': "What happens if a driver has a score below 80?",
            'description': "Policy question"
        },
        {
            'query': "Driver performance metrics and scoring",
            'description': "Complex policy question"
        }
    ]
    
    for test_case in test_cases:
        query = test_case['query']
        description = test_case['description']
        
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"Type: {description}")
        print(f"{'='*80}")
        
        # Retrieve
        results, context = retriever.retrieve(query)
        
        print(f"\nRetrieved {len(results)} chunks")
        print("\nTop Results:")
        for result in results:
            print(f"\n  [{result.citation_key}] Relevance: {result.relevance_score:.3f}")
            print(f"      Section: {result.metadata['section']}")
            print(f"      Source: {result.metadata['source']}")
            print(f"      Preview: {result.content[:150]}...")
        
        # Show formatted context (what goes to LLM)
        print(f"\n{'='*80}")
        print("FORMATTED CONTEXT FOR LLM:")
        print(f"{'='*80}")
        print(context[:1000])  # Show first 1000 chars
        print(f"\n... [context continues for {len(context)} total characters]")
        
        # Show citations
        print("\nCitations for User:")
        for citation in retriever.get_citations(results):
            print(f"  {citation}")
    
    # Debug comparison
    print("\n\n" + "="*80)
    print("DEBUG: Comparing Search Strategies")
    print("="*80)
    
    debug_query = "What is P0420?"
    debug_results = retriever.debug_search(debug_query, n_results=3)
    
    for strategy, results in debug_results.items():
        print(f"\n{strategy.upper()} Search:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f} | {result['section']}")
