"""
AI Agent Integration with RAG System

Shows how to integrate the RAG system with your AI agent
for answering queries using both database and documents.
"""

import os
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from anthropic import Anthropic

from .document_retriever import DocumentRetriever, RetrievalResult
from .vector_store import VectorStore


@dataclass
class AgentResponse:
    """Structured response from AI agent"""
    answer: str
    query_type: Literal["database", "document", "hybrid"]
    sql_query: Optional[str] = None
    retrieved_docs: Optional[List[RetrievalResult]] = None
    citations: Optional[List[str]] = None
    confidence: float = 0.0


class RAGAgent:
    """
    AI Agent with RAG capabilities.
    
    Determines whether to:
    1. Query database (SQL generation)
    2. Query documents (RAG)
    3. Both (hybrid)
    """
    
    def __init__(
        self,
        retriever: DocumentRetriever,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None
    ):
        """
        Args:
            retriever: DocumentRetriever instance
            model: Claude model name
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        """
        self.retriever = retriever
        self.model = model
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        self.client = Anthropic(api_key=api_key)
    
    def classify_query(self, query: str) -> str:
        """
        Classify query to determine retrieval strategy.
        
        Returns:
            "database" - Query database (generate SQL)
            "document" - Query documents (RAG)
            "hybrid" - Both
        """
        query_lower = query.lower()
        
        # Database indicators
        database_keywords = [
            'show me', 'list', 'how many', 'which', 'what vehicles',
            'count', 'average', 'total', 'last', 'recent', 'today',
            'this week', 'this month', 'filter', 'where'
        ]
        
        # Document indicators
        document_keywords = [
            'what is', 'explain', 'how to', 'procedure', 'policy',
            'what should', 'why', 'fault code', 'what does', 'tell me about',
            'handbook', 'requirement', 'when should', 'guideline'
        ]
        
        has_database = any(keyword in query_lower for keyword in database_keywords)
        has_document = any(keyword in query_lower for keyword in document_keywords)
        
        if has_database and has_document:
            return "hybrid"
        elif has_database:
            return "database"
        elif has_document:
            return "document"
        else:
            # Default to hybrid for ambiguous queries
            return "hybrid"
    
    def answer_document_query(self, query: str) -> AgentResponse:
        """
        Answer query using only company documents (RAG).
        """
        # Retrieve relevant documents
        results, context = self.retriever.retrieve(query, n_results=5)
        
        # Build prompt with retrieved context
        prompt = f"""You are FleetFix AI Assistant. Answer the user's question using ONLY the company documentation provided below.

        {context}

        User Question: {query}

        Instructions:
        - Provide a clear, accurate answer based on the documentation
        - Cite sources using the [1], [2], etc. markers from the documentation
        - If the documentation doesn't contain the answer, say so
        - Be concise but comprehensive
        - Use bullet points when listing multiple items

        Answer:"""
        
        # Get response from Claude
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        answer = message.content[0].text
        
        return AgentResponse(
            answer=answer,
            query_type="document",
            retrieved_docs=results,
            citations=self.retriever.get_citations(results)
        )
    
    def answer_database_query(
        self,
        query: str,
        schema_context: str
    ) -> AgentResponse:
        """
        Answer query by generating SQL.
        
        Args:
            query: User query
            schema_context: Database schema description
        """
        prompt = f"""You are a SQL expert for FleetFix's fleet management database.

        Database Schema:
        {schema_context}

        Generate a safe PostgreSQL SELECT query to answer this question:
        "{query}"

        Requirements:
        - SELECT queries only (no DELETE, UPDATE, DROP, INSERT)
        - Use proper JOINs when needed
        - Include appropriate WHERE, ORDER BY, LIMIT clauses
        - Return ONLY the SQL query, no explanation

        SQL Query:"""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        sql_query = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return AgentResponse(
            answer=f"Generated SQL query: {sql_query}",
            query_type="database",
            sql_query=sql_query
        )
    
    def answer_hybrid_query(
        self,
        query: str,
        schema_context: str,
        database_results: Optional[List[Dict]] = None
    ) -> AgentResponse:
        """
        Answer query using both database and documents.
        
        Example: "Show me vehicles with P0420 fault code and explain what it means"
        - Database: Get vehicles with P0420
        - Documents: Get P0420 explanation and recommendations
        """
        # Get database query
        db_response = self.answer_database_query(query, schema_context)
        
        # Get document context
        doc_results, doc_context = self.retriever.retrieve(query, n_results=3)
        
        # If database results provided, include them
        db_summary = ""
        if database_results:
            db_summary = f"\nDatabase Results:\n{self._format_db_results(database_results)}\n"
        
        # Combine both for final answer
        prompt = f"""You are FleetFix AI Assistant. Answer the user's question using both the database query results and company documentation.

        {doc_context}

        {db_summary}

        SQL Query Generated: {db_response.sql_query}

        User Question: {query}

        Instructions:
        - Synthesize information from both database and documentation
        - Provide actionable insights
        - Cite documentation sources using [1], [2], etc.
        - Explain what the data means and what actions to take
        - Be concise but thorough

        Answer:"""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        answer = message.content[0].text
        
        return AgentResponse(
            answer=answer,
            query_type="hybrid",
            sql_query=db_response.sql_query,
            retrieved_docs=doc_results,
            citations=self.retriever.get_citations(doc_results)
        )
    
    def answer(
        self,
        query: str,
        schema_context: Optional[str] = None,
        database_results: Optional[List[Dict]] = None
    ) -> AgentResponse:
        """
        Main entry point - automatically routes to appropriate handler.
        
        Args:
            query: User question
            schema_context: Database schema (needed for SQL generation)
            database_results: Pre-executed database results (for hybrid queries)
        
        Returns:
            AgentResponse with answer and metadata
        """
        # Classify query
        query_type = self.classify_query(query)
        
        if query_type == "document":
            return self.answer_document_query(query)
        
        elif query_type == "database":
            if not schema_context:
                raise ValueError("schema_context required for database queries")
            return self.answer_database_query(query, schema_context)
        
        else:  # hybrid
            if not schema_context:
                # Fall back to document-only if no schema
                return self.answer_document_query(query)
            return self.answer_hybrid_query(query, schema_context, database_results)
    
    def _format_db_results(self, results: List[Dict], max_rows: int = 10) -> str:
        """Format database results for inclusion in prompt"""
        if not results:
            return "No results found."
        
        # Show first few rows
        display_results = results[:max_rows]
        formatted = []
        
        for i, row in enumerate(display_results, 1):
            row_str = ", ".join(f"{k}: {v}" for k, v in row.items())
            formatted.append(f"  {i}. {row_str}")
        
        if len(results) > max_rows:
            formatted.append(f"  ... and {len(results) - max_rows} more rows")
        
        return "\n".join(formatted)


# FastAPI Integration Example
class FastAPIIntegration:
    """
    Example of how to integrate with FastAPI backend.
    """
    
    def __init__(self):
        # Initialize RAG system
        from rag.document_processor import DocumentProcessor
        
        # Process documents (do this once at startup)
        processor = DocumentProcessor("company_docs")
        chunks = processor.process_all_documents()
        
        # Initialize vector store
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory="./chroma_db",
            embedding_model="local"  # or "openai"
        )
        
        # Index documents if needed
        if vector_store.collection.count() == 0:
            vector_store.add_documents(chunks)
        
        # Initialize retriever
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        
        # Initialize agent
        self.agent = RAGAgent(retriever=retriever)
    
    async def handle_query(self, query: str) -> Dict:
        """
        Handle incoming query from API endpoint.
        
        Example FastAPI endpoint:
        
        @app.post("/api/query")
        async def query_endpoint(request: QueryRequest):
            integration = FastAPIIntegration()
            return await integration.handle_query(request.query)
        """
        # Get schema context (you'd load this from your DB models)
        schema_context = self._get_schema_context()
        
        # Get response from agent
        response = self.agent.answer(
            query=query,
            schema_context=schema_context
        )
        
        # Format for API response
        return {
            "answer": response.answer,
            "query_type": response.query_type,
            "sql": response.sql_query,
            "citations": response.citations,
            "sources": [
                {
                    "section": doc.metadata.get("section"),
                    "source": doc.metadata.get("source"),
                    "relevance": doc.relevance_score
                }
                for doc in (response.retrieved_docs or [])
            ]
        }
    
    def _get_schema_context(self) -> str:
        """Get database schema description"""
        return """
        Database Schema:

        vehicles:
        - id (int, primary key)
        - make (varchar)
        - model (varchar)
        - year (int)
        - vin (varchar)
        - license_plate (varchar)
        - status (varchar)
        - current_mileage (int)

        maintenance_records:
        - id (int, primary key)
        - vehicle_id (int, foreign key to vehicles)
        - service_date (date)
        - service_type (varchar)
        - cost (decimal)
        - mileage (int)
        - next_service_due (date)

        fault_codes:
        - id (int, primary key)
        - vehicle_id (int, foreign key to vehicles)
        - timestamp (timestamp)
        - code (varchar)
        - description (varchar)
        - severity (varchar)
        - resolved (boolean)

        driver_performance:
        - id (int, primary key)
        - driver_id (int)
        - vehicle_id (int, foreign key to vehicles)
        - date (date)
        - harsh_braking_events (int)
        - rapid_acceleration (int)
        - idle_time (int)
        - hours_driven (decimal)
        - score (int)

        drivers:
        - id (int, primary key)
        - name (varchar)
        - license_number (varchar)
        - hire_date (date)
        - status (varchar)
        """


# Example Usage / Testing
if __name__ == "__main__":
    from rag.document_processor import DocumentProcessor
    from rag.vector_store import VectorStore
    
    print("Initializing RAG Agent...")
    
    # Set up RAG system
    processor = DocumentProcessor("company_docs")
    chunks = processor.process_all_documents()
    
    vector_store = VectorStore(
        collection_name="fleetfix_docs",
        persist_directory="./chroma_db",
        embedding_model="local"
    )
    
    if vector_store.collection.count() == 0:
        vector_store.add_documents(chunks)
    
    retriever = DocumentRetriever(
        vector_store=vector_store,
        max_context_chunks=5,
        enable_reranking=True
    )
    
    # Initialize agent
    agent = RAGAgent(retriever=retriever)
    
    # Test queries
    test_queries = [
        {
            "query": "What is fault code P0420 and what should I do about it?",
            "expected_type": "document"
        },
        {
            "query": "Show me all vehicles with overdue maintenance",
            "expected_type": "database"
        },
        {
            "query": "List vehicles with fault code P0420 and explain what we should do",
            "expected_type": "hybrid"
        },
        {
            "query": "What's our driver score calculation method?",
            "expected_type": "document"
        }
    ]
    
    schema_context = """
    vehicles (id, make, model, year, vin, current_mileage, status)
    maintenance_records (id, vehicle_id, service_date, next_service_due, cost)
    fault_codes (id, vehicle_id, timestamp, code, description, severity)
    driver_performance (id, driver_id, date, score, harsh_braking_events)
    """
    
    print("\n" + "="*80)
    print("RAG AGENT DEMO")
    print("="*80)
    
    for test in test_queries:
        query = test["query"]
        expected = test["expected_type"]
        
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"Expected Type: {expected}")
        print(f"{'='*80}")
        
        # Classify
        actual_type = agent.classify_query(query)
        print(f"Classified as: {actual_type}")
        print(f"✓ Correct!" if actual_type == expected else "✗ Mismatch")
        
        # Get answer
        response = agent.answer(query, schema_context=schema_context)
        
        print(f"\nResponse Type: {response.query_type}")
        
        if response.sql_query:
            print(f"\nGenerated SQL:\n{response.sql_query}")
        
        if response.citations:
            print(f"\nCitations:")
            for citation in response.citations:
                print(f"  {citation}")
        
        print(f"\nAnswer:\n{response.answer}")
        print(f"\n{'-'*80}")
