"""
One-command setup script for FleetFix RAG system

Run: python -m rag.setup_rag
"""

import os
import sys
from pathlib import Path


def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required = {
        'chromadb': 'chromadb',
        'sentence_transformers': 'sentence-transformers',
        'anthropic': 'anthropic',
        'numpy': 'numpy'
    }
    
    missing = []
    
    for package, pip_name in required.items():
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(pip_name)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies installed!")
    return True


def check_documents():
    """Check if company documents exist"""
    print_header("Checking Company Documents")
    
    docs_dir = Path("company_docs")
    
    if not docs_dir.exists():
        print(f"✗ Directory 'company_docs' not found!")
        print(f"\nPlease create the directory and add your markdown files:")
        print(f"  mkdir company_docs")
        return False
    
    md_files = list(docs_dir.glob("*.md"))
    
    if not md_files:
        print(f"✗ No .md files found in company_docs/")
        print(f"\nPlease add your company documentation files.")
        return False
    
    print(f"✓ Found {len(md_files)} document(s):")
    for f in md_files:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
    
    return True


def check_api_key():
    """Check if Anthropic API key is set"""
    print_header("Checking API Key")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not found in environment")
        print("\nOptions:")
        print("1. Add to .env file:")
        print("   ANTHROPIC_API_KEY=your_key_here")
        print("\n2. Export in shell:")
        print("   export ANTHROPIC_API_KEY=your_key_here")
        print("\n3. Add to ~/.bashrc or ~/.zshrc for persistence")
        return False
    
    print(f"✓ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True


def process_documents():
    """Process and index documents"""
    print_header("Processing Documents")
    
    try:
        from rag.document_processor import DocumentProcessor
        
        processor = DocumentProcessor("company_docs")
        chunks = processor.process_all_documents()
        
        stats = processor.get_chunk_statistics(chunks)
        
        print(f"\n✓ Successfully processed documents!")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Average chunk size: {stats['avg_chunk_size']:.0f} characters")
        print(f"  Documents processed: {stats['documents_processed']}")
        
        return chunks
        
    except Exception as e:
        print(f"✗ Error processing documents: {e}")
        return None


def create_vector_store(chunks):
    """Create and populate vector store"""
    print_header("Creating Vector Store")
    
    try:
        from rag.vector_store import VectorStore
        
        # Check if vector store already exists
        chroma_dir = Path("chroma_db")
        
        if chroma_dir.exists():
            print("⚠️  Vector store already exists at ./chroma_db")
            response = input("Reset and rebuild? (y/N): ").strip().lower()
            
            if response != 'y':
                print("Keeping existing vector store.")
                vector_store = VectorStore(
                    collection_name="fleetfix_docs",
                    persist_directory="./chroma_db",
                    embedding_model="local"
                )
                print(f"✓ Loaded existing vector store ({vector_store.collection.count()} chunks)")
                return vector_store
            
            print("Resetting vector store...")
        
        # Create new vector store
        print("Initializing ChromaDB with local embeddings...")
        print("(This will download the embedding model on first run - ~400MB)")
        
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory="./chroma_db",
            embedding_model="local"
        )
        
        # Reset if rebuilding
        if chroma_dir.exists():
            vector_store.reset()
        
        # Index documents
        print(f"\nIndexing {len(chunks)} chunks...")
        print("(This may take 1-2 minutes...)")
        
        vector_store.add_documents(chunks, batch_size=50)
        
        stats = vector_store.get_statistics()
        print(f"\n✓ Vector store created successfully!")
        print(f"  Total chunks indexed: {stats['total_chunks']}")
        print(f"  Embedding dimension: {stats['embedding_dimension']}")
        print(f"  Model: {stats['embedding_model']}")
        
        return vector_store
        
    except Exception as e:
        print(f"✗ Error creating vector store: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_retrieval(vector_store):
    """Test the retrieval system"""
    print_header("Testing Retrieval System")
    
    try:
        from rag.document_retriever import DocumentRetriever
        
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=3,
            enable_reranking=True
        )
        
        # Test query
        test_query = "What is fault code P0420?"
        
        print(f"Test query: '{test_query}'")
        print("\nRetrieving...")
        
        results, context = retriever.retrieve(test_query)
        
        print(f"\n✓ Retrieved {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. Relevance: {result.relevance_score:.3f}")
            print(f"     Section: {result.metadata['section']}")
            print(f"     Source: {result.metadata['source']}")
        
        print("\n✓ RAG system is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_next_steps():
    """Print instructions for next steps"""
    print_header("Setup Complete! 🎉")
    
    print("""
    Your RAG system is ready to use!

    Next Steps:

    1. Test the CLI demo:
    python rag_demo_cli.py

    2. Integrate with your FastAPI backend:
    
    from ai_agent_integration import RAGAgent
    from vector_store import VectorStore
    from document_retriever import DocumentRetriever
    
    vector_store = VectorStore(...)
    retriever = DocumentRetriever(vector_store=vector_store)
    agent = RAGAgent(retriever=retriever)
    
    response = agent.answer("Your query here")

    3. Read the full documentation:
    RAG_SYSTEM_README.md

    4. Run tests:
    python document_retriever.py

    Happy building! 🚀
    """)


def main():
    """Main setup flow"""
    print("\n" + "="*80)
    print("  FleetFix RAG System Setup")
    print("="*80)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies first.")
        sys.exit(1)
    
    # Step 2: Check documents
    if not check_documents():
        print("\n⚠️  Please add company documents to company_docs/ directory.")
        sys.exit(1)
    
    # Step 3: Check API key (optional for RAG, required for agent)
    check_api_key()  # Don't exit if missing, can still build vector store
    
    # Step 4: Process documents
    chunks = process_documents()
    if not chunks:
        print("\n⚠️  Failed to process documents.")
        sys.exit(1)
    
    # Step 5: Create vector store
    vector_store = create_vector_store(chunks)
    if not vector_store:
        print("\n⚠️  Failed to create vector store.")
        sys.exit(1)
    
    # Step 6: Test retrieval
    if not test_retrieval(vector_store):
        print("\n⚠️  Retrieval test failed.")
        sys.exit(1)
    
    # Success!
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
