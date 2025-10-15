"""
Interactive CLI Demo for FleetFix RAG System

Run: python rag_demo_cli.py
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path so we can import backend modules
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_colored(text: str, color: str):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}")


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}{Colors.END}\n")


def print_result(result, index: int):
    """Pretty print a search result"""
    print(f"\n{Colors.CYAN}[{result.citation_key}] Relevance: {result.relevance_score:.3f}{Colors.END}")
    print(f"{Colors.BOLD}Section:{Colors.END} {result.metadata['section']}")
    print(f"{Colors.BOLD}Source:{Colors.END} {result.metadata['source']}")
    print(f"\n{result.content[:300]}...")
    print(f"{Colors.YELLOW}{'─'*80}{Colors.END}")


def initialize_system():
    """Initialize the RAG system"""
    print_header("Initializing FleetFix RAG System")
    
    try:
        from backend.rag.vector_store import VectorStore
        from backend.rag.document_retriever import DocumentRetriever
        
        # Check if vector store exists
        chroma_dir = Path("chroma_db")
        if not chroma_dir.exists():
            print_colored("✗ Vector store not found!", Colors.RED)
            print("\nPlease run setup first:")
            print("  python setup_rag.py")
            sys.exit(1)
        
        print("Loading vector store...")
        vector_store = VectorStore(
            collection_name="fleetfix_docs",
            persist_directory="./chroma_db",
            embedding_model="local"
        )
        
        print(f"✓ Loaded {vector_store.collection.count()} document chunks")
        
        print("\nInitializing retriever with reranking...")
        retriever = DocumentRetriever(
            vector_store=vector_store,
            max_context_chunks=5,
            enable_reranking=True
        )
        
        print_colored("✓ RAG system ready!\n", Colors.GREEN)
        
        return retriever
        
    except ImportError as e:
        print_colored(f"✗ Missing dependency: {e}", Colors.RED)
        print("\nPlease install requirements:")
        print("  pip install -r requirements_rag.txt")
        sys.exit(1)
    except Exception as e:
        print_colored(f"✗ Error initializing system: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_examples():
    """Show example queries"""
    print_header("Example Queries")
    
    examples = [
        ("Fault Codes", [
            "What is fault code P0420?",
            "Explain P0171 and what causes it",
            "How urgent is P0300?"
        ]),
        ("Maintenance", [
            "What's included in a Level 1 service?",
            "Oil change procedure and cost",
            "When should we replace brake pads?"
        ]),
        ("Driver Policies", [
            "How is driver score calculated?",
            "What happens if a driver scores below 80?",
            "Idle time policy and limits"
        ]),
        ("Fleet Policies", [
            "Fuel card usage policy",
            "Accident reporting procedure",
            "Vehicle replacement criteria"
        ])
    ]
    
    for category, queries in examples:
        print(f"{Colors.BOLD}{category}:{Colors.END}")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        print()


def search_mode(retriever):
    """Interactive search mode"""
    print_header("Search Mode")
    print("Enter your queries (or 'back' to return to menu)\n")
    
    while True:
        try:
            # Get query
            query = input(f"{Colors.BOLD}Query >{Colors.END} ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['back', 'exit', 'quit', 'menu']:
                break
            
            # Perform search
            print(f"\n{Colors.YELLOW}Searching...{Colors.END}")
            results, context = retriever.retrieve(query, n_results=5)
            
            # Display results
            print_colored(f"\n✓ Found {len(results)} relevant sections:", Colors.GREEN)
            
            for i, result in enumerate(results, 1):
                print_result(result, i)
            
            # Show citations
            print(f"\n{Colors.BOLD}Citations:{Colors.END}")
            for citation in retriever.get_citations(results):
                print(f"  {citation}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print_colored(f"\n✗ Error: {e}", Colors.RED)


def compare_search_strategies(retriever):
    """Compare different search strategies"""
    print_header("Compare Search Strategies")
    
    query = input(f"{Colors.BOLD}Enter query to compare:{Colors.END} ").strip()
    
    if not query:
        return
    
    print(f"\n{Colors.YELLOW}Running searches...{Colors.END}\n")
    
    # Get debug results
    debug_results = retriever.debug_search(query, n_results=3)
    
    strategies = ['semantic', 'keyword', 'hybrid']
    
    for strategy in strategies:
        print(f"{Colors.BOLD}{Colors.CYAN}{strategy.upper()} Search:{Colors.END}")
        results = debug_results[strategy]
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f}")
            print(f"     Section: {result['section']}")
            print(f"     Preview: {result['preview']}...")
            print()
        
        print(f"{Colors.YELLOW}{'─'*80}{Colors.END}\n")


def fault_code_lookup(retriever):
    """Specialized fault code lookup"""
    print_header("Fault Code Lookup")
    
    code = input(f"{Colors.BOLD}Enter fault code (e.g., P0420):{Colors.END} ").strip().upper()
    
    if not code:
        return
    
    print(f"\n{Colors.YELLOW}Looking up {code}...{Colors.END}")
    
    # Use specialized fault code retrieval
    results, context = retriever.retrieve_by_fault_code(code)
    
    if not results:
        print_colored(f"\n✗ No information found for {code}", Colors.RED)
        return
    
    print_colored(f"\n✓ Found information for {code}:", Colors.GREEN)
    
    # Display first (most relevant) result in detail
    result = results[0]
    
    print(f"\n{Colors.BOLD}Section:{Colors.END} {result.metadata['section']}")
    print(f"{Colors.BOLD}Source:{Colors.END} {result.metadata['source']}")
    print(f"{Colors.BOLD}Relevance:{Colors.END} {result.relevance_score:.3f}")
    print(f"\n{result.content}\n")


def policy_lookup(retriever):
    """Specialized policy lookup"""
    print_header("Policy Lookup")
    
    print("Common policies:")
    print("  1. Driver score")
    print("  2. Fuel card")
    print("  3. Accident reporting")
    print("  4. Maintenance schedule")
    print("  5. Custom search")
    print()
    
    choice = input(f"{Colors.BOLD}Select option (1-5):{Colors.END} ").strip()
    
    policy_queries = {
        '1': "driver score calculation and performance categories",
        '2': "fuel card usage policy",
        '3': "accident reporting procedure",
        '4': "preventive maintenance schedule",
    }
    
    if choice == '5':
        query = input(f"{Colors.BOLD}Enter policy topic:{Colors.END} ").strip()
    elif choice in policy_queries:
        query = policy_queries[choice]
    else:
        return
    
    print(f"\n{Colors.YELLOW}Searching policies for: {query}...{Colors.END}")
    
    results, context = retriever.retrieve_policy(query)
    
    print_colored(f"\n✓ Found {len(results)} relevant policy sections:", Colors.GREEN)
    
    for result in results:
        print_result(result, 0)


def export_context(retriever):
    """Export formatted context for LLM"""
    print_header("Export Context for LLM")
    
    query = input(f"{Colors.BOLD}Enter query:{Colors.END} ").strip()
    
    if not query:
        return
    
    results, context = retriever.retrieve(query, n_results=5)
    
    # Ask where to save
    filename = input(f"{Colors.BOLD}Save to file (or press Enter for stdout):{Colors.END} ").strip()
    
    if filename:
        with open(filename, 'w') as f:
            f.write(context)
        print_colored(f"\n✓ Context exported to {filename}", Colors.GREEN)
    else:
        print(f"\n{Colors.YELLOW}{'='*80}")
        print("CONTEXT FOR LLM")
        print(f"{'='*80}{Colors.END}\n")
        print(context)


def show_statistics(retriever):
    """Show vector store statistics"""
    print_header("Vector Store Statistics")
    
    stats = retriever.vector_store.get_statistics()
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"  Collection name: {stats['collection_name']}")
    print(f"  Embedding model: {stats['embedding_model']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")
    print(f"\n{Colors.BOLD}Content:{Colors.END}")
    print(f"  Total chunks: {stats['total_chunks']}")
    
    # Get document breakdown
    all_sources = set()
    collection = retriever.vector_store.collection
    
    # Get all metadata
    all_data = collection.get(include=['metadatas'])
    
    for metadata in all_data['metadatas']:
        all_sources.add(metadata.get('source', 'Unknown'))
    
    print(f"  Documents indexed: {len(all_sources)}")
    print(f"\n{Colors.BOLD}Source Documents:{Colors.END}")
    for source in sorted(all_sources):
        # Count chunks per document
        count = sum(1 for m in all_data['metadatas'] if m.get('source') == source)
        print(f"  - {source}: {count} chunks")


def main_menu(retriever):
    """Show main menu and handle user input"""
    
    while True:
        print_header("FleetFix RAG System - Interactive Demo")
        
        print(f"{Colors.BOLD}Options:{Colors.END}")
        print("  1. 🔍 Search Documents")
        print("  2. 📊 Compare Search Strategies")
        print("  3. 🚨 Fault Code Lookup")
        print("  4. 📋 Policy Lookup")
        print("  5. 💡 Show Example Queries")
        print("  6. 📤 Export Context for LLM")
        print("  7. 📈 Show Statistics")
        print("  8. ❌ Exit")
        print()
        
        choice = input(f"{Colors.BOLD}Select option (1-8):{Colors.END} ").strip()
        
        if choice == '1':
            search_mode(retriever)
        elif choice == '2':
            compare_search_strategies(retriever)
        elif choice == '3':
            fault_code_lookup(retriever)
        elif choice == '4':
            policy_lookup(retriever)
        elif choice == '5':
            show_examples()
            input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        elif choice == '6':
            export_context(retriever)
        elif choice == '7':
            show_statistics(retriever)
            input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        elif choice == '8':
            print_colored("\n👋 Goodbye!", Colors.GREEN)
            break
        else:
            print_colored("\n✗ Invalid option", Colors.RED)


def main():
    """Main entry point"""
    try:
        # Initialize system
        retriever = initialize_system()
        
        # Show main menu
        main_menu(retriever)
        
    except KeyboardInterrupt:
        print_colored("\n\n👋 Goodbye!", Colors.GREEN)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n✗ Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
