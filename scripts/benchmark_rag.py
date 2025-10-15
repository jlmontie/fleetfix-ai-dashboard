"""
RAG System Benchmarking and Evaluation

Measures:
- Retrieval accuracy (top-k accuracy)
- Query latency
- Embedding generation speed
- Reranking impact
- Search strategy comparison

Run: python benchmark_rag.py
"""

import time
import json
import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

# Add project root to Python path so we can import backend modules
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from backend.rag.vector_store import VectorStore
from backend.rag.document_retriever import DocumentRetriever


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    metric_name: str
    value: float
    unit: str
    description: str


@dataclass
class QueryTestCase:
    """Test case for retrieval quality"""
    query: str
    expected_sources: List[str]  # Expected document sources
    expected_sections: List[str]  # Expected sections (partial matches OK)
    category: str


# ============================================================================
# Test Dataset
# ============================================================================

TEST_QUERIES = [
    QueryTestCase(
        query="What is fault code P0420?",
        expected_sources=["fault_code_reference.md"],
        expected_sections=["P0420", "Catalyst"],
        category="fault_code"
    ),
    QueryTestCase(
        query="Explain P0171 and what causes it",
        expected_sources=["fault_code_reference.md"],
        expected_sections=["P0171", "System Too Lean"],
        category="fault_code"
    ),
    QueryTestCase(
        query="Oil change procedure and cost",
        expected_sources=["maintenance_procedures.md"],
        expected_sections=["Level 1", "oil"],
        category="maintenance"
    ),
    QueryTestCase(
        query="Tire rotation procedure",
        expected_sources=["maintenance_procedures.md"],
        expected_sections=["tire", "rotation"],
        category="maintenance"
    ),
    QueryTestCase(
        query="How is driver score calculated?",
        expected_sources=["driver_handbook.md"],
        expected_sections=["Driver Score", "calculation"],
        category="driver_policy"
    ),
    QueryTestCase(
        query="What happens if driver scores below 80?",
        expected_sources=["driver_handbook.md"],
        expected_sections=["Needs Improvement", "performance"],
        category="driver_policy"
    ),
    QueryTestCase(
        query="Fuel card usage policy",
        expected_sources=["fleet_policies.md"],
        expected_sections=["fuel card", "policy"],
        category="fleet_policy"
    ),
    QueryTestCase(
        query="Accident reporting procedure",
        expected_sources=["fleet_policies.md"],
        expected_sections=["accident", "reporting"],
        category="fleet_policy"
    ),
    QueryTestCase(
        query="Vehicle maintenance schedule and intervals",
        expected_sources=["maintenance_procedures.md"],
        expected_sections=["schedule", "interval"],
        category="maintenance"
    ),
    QueryTestCase(
        query="Driver performance metrics and scoring system",
        expected_sources=["driver_handbook.md"],
        expected_sections=["performance", "metrics", "score"],
        category="driver_policy"
    ),
]


# ============================================================================
# Benchmarking Functions
# ============================================================================

def benchmark_retrieval_accuracy(
    retriever: DocumentRetriever,
    test_cases: List[QueryTestCase]
) -> Dict[str, float]:
    """
    Measure retrieval accuracy using test cases.
    
    Metrics:
    - Top-1 accuracy: First result matches expected
    - Top-3 accuracy: Expected result in top 3
    - Top-5 accuracy: Expected result in top 5
    - MRR (Mean Reciprocal Rank): Average of 1/rank
    """
    print("\n" + "="*80)
    print("RETRIEVAL ACCURACY BENCHMARK")
    print("="*80)
    
    top1_correct = 0
    top3_correct = 0
    top5_correct = 0
    reciprocal_ranks = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Query: {test_case.query}")
        
        # Retrieve
        results, _ = retriever.retrieve(test_case.query, n_results=5)
        
        # Check if expected source appears in results
        result_sources = [r.metadata.get('source') for r in results]
        
        # Check if expected section keywords appear
        found_rank = None
        for rank, result in enumerate(results, 1):
            source = result.metadata.get('source')
            section = result.metadata.get('section', '').lower()
            
            source_match = source in test_case.expected_sources
            section_match = any(
                exp.lower() in section 
                for exp in test_case.expected_sections
            )
            
            if source_match and section_match:
                found_rank = rank
                break
        
        if found_rank:
            print(f"  ✓ Found at rank {found_rank}")
            if found_rank == 1:
                top1_correct += 1
            if found_rank <= 3:
                top3_correct += 1
            if found_rank <= 5:
                top5_correct += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            print(f"  ✗ Not found in top 5")
            print(f"    Expected: {test_case.expected_sources[0]} - {test_case.expected_sections}")
            print(f"    Got: {results[0].metadata.get('source')} - {results[0].metadata.get('section')}")
            reciprocal_ranks.append(0.0)
    
    # Calculate metrics
    n = len(test_cases)
    top1_acc = (top1_correct / n) * 100
    top3_acc = (top3_correct / n) * 100
    top5_acc = (top5_correct / n) * 100
    mrr = statistics.mean(reciprocal_ranks)
    
    print("\n" + "-"*80)
    print("RESULTS:")
    print(f"  Top-1 Accuracy: {top1_acc:.1f}%")
    print(f"  Top-3 Accuracy: {top3_acc:.1f}%")
    print(f"  Top-5 Accuracy: {top5_acc:.1f}%")
    print(f"  Mean Reciprocal Rank: {mrr:.3f}")
    
    return {
        'top1_accuracy': top1_acc,
        'top3_accuracy': top3_acc,
        'top5_accuracy': top5_acc,
        'mrr': mrr
    }


def benchmark_query_latency(
    retriever: DocumentRetriever,
    num_queries: int = 50
) -> Dict[str, float]:
    """
    Measure query latency across different search strategies.
    """
    print("\n" + "="*80)
    print("QUERY LATENCY BENCHMARK")
    print("="*80)
    
    test_query = "What is fault code P0420?"
    
    # Semantic search
    print("\nSemantic Search:")
    semantic_times = []
    for i in range(num_queries):
        start = time.time()
        retriever.vector_store.semantic_search(test_query, n_results=5)
        elapsed = (time.time() - start) * 1000
        semantic_times.append(elapsed)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{num_queries} queries completed...")
    
    # Hybrid search with reranking
    print("\nHybrid Search + Reranking:")
    hybrid_times = []
    for i in range(num_queries):
        start = time.time()
        retriever.retrieve(test_query, n_results=5)
        elapsed = (time.time() - start) * 1000
        hybrid_times.append(elapsed)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{num_queries} queries completed...")
    
    # Calculate statistics
    results = {
        'semantic_mean_ms': statistics.mean(semantic_times),
        'semantic_median_ms': statistics.median(semantic_times),
        'semantic_p95_ms': sorted(semantic_times)[int(0.95 * len(semantic_times))],
        'hybrid_mean_ms': statistics.mean(hybrid_times),
        'hybrid_median_ms': statistics.median(hybrid_times),
        'hybrid_p95_ms': sorted(hybrid_times)[int(0.95 * len(hybrid_times))],
    }
    
    print("\n" + "-"*80)
    print("RESULTS:")
    print(f"\nSemantic Search:")
    print(f"  Mean: {results['semantic_mean_ms']:.2f}ms")
    print(f"  Median: {results['semantic_median_ms']:.2f}ms")
    print(f"  P95: {results['semantic_p95_ms']:.2f}ms")
    print(f"\nHybrid + Reranking:")
    print(f"  Mean: {results['hybrid_mean_ms']:.2f}ms")
    print(f"  Median: {results['hybrid_median_ms']:.2f}ms")
    print(f"  P95: {results['hybrid_p95_ms']:.2f}ms")
    print(f"\nReranking Overhead: {results['hybrid_mean_ms'] - results['semantic_mean_ms']:.2f}ms")
    
    return results


def benchmark_embedding_speed(vector_store: VectorStore) -> Dict[str, float]:
    """
    Measure embedding generation speed.
    """
    print("\n" + "="*80)
    print("EMBEDDING SPEED BENCHMARK")
    print("="*80)
    
    # Test texts of varying lengths
    short_text = "What is fault code P0420?"
    medium_text = " ".join([short_text] * 10)
    long_text = " ".join([short_text] * 50)
    
    texts = {
        'short': [short_text] * 100,
        'medium': [medium_text] * 100,
        'long': [long_text] * 100
    }
    
    results = {}
    
    for size, text_list in texts.items():
        print(f"\n{size.capitalize()} texts ({len(text_list[0])} chars):")
        
        start = time.time()
        vector_store.embedding_model.embed(text_list)
        elapsed = time.time() - start
        
        throughput = len(text_list) / elapsed
        
        results[f'{size}_throughput'] = throughput
        results[f'{size}_time_ms'] = elapsed * 1000
        
        print(f"  Throughput: {throughput:.1f} texts/sec")
        print(f"  Total time: {elapsed*1000:.1f}ms")
    
    return results


def benchmark_reranking_impact(
    retriever: DocumentRetriever,
    test_cases: List[QueryTestCase]
) -> Dict[str, float]:
    """
    Compare retrieval quality with and without reranking.
    """
    print("\n" + "="*80)
    print("RERANKING IMPACT BENCHMARK")
    print("="*80)
    
    # Disable reranking temporarily
    original_setting = retriever.enable_reranking
    
    # Test without reranking
    print("\nWithout reranking:")
    retriever.enable_reranking = False
    without_reranking = benchmark_retrieval_accuracy(retriever, test_cases[:5])  # Use subset
    
    # Test with reranking
    print("\nWith reranking:")
    retriever.enable_reranking = True
    with_reranking = benchmark_retrieval_accuracy(retriever, test_cases[:5])
    
    # Restore original setting
    retriever.enable_reranking = original_setting
    
    # Calculate improvement
    improvement = {
        'top1_improvement': with_reranking['top1_accuracy'] - without_reranking['top1_accuracy'],
        'top3_improvement': with_reranking['top3_accuracy'] - without_reranking['top3_accuracy'],
        'mrr_improvement': with_reranking['mrr'] - without_reranking['mrr']
    }
    
    print("\n" + "-"*80)
    print("IMPROVEMENT:")
    print(f"  Top-1: +{improvement['top1_improvement']:.1f}%")
    print(f"  Top-3: +{improvement['top3_improvement']:.1f}%")
    print(f"  MRR: +{improvement['mrr_improvement']:.3f}")
    
    return improvement


def benchmark_search_strategies(
    retriever: DocumentRetriever
) -> Dict[str, Dict]:
    """
    Compare semantic, keyword, and hybrid search strategies.
    """
    print("\n" + "="*80)
    print("SEARCH STRATEGY COMPARISON")
    print("="*80)
    
    test_queries = [
        ("What is P0420?", "keyword-friendly"),
        ("Explain catalytic converter efficiency issues", "semantic-friendly"),
        ("oil change cost and procedure", "hybrid-friendly")
    ]
    
    results = {}
    
    for query, query_type in test_queries:
        print(f"\nQuery: {query} ({query_type})")
        
        # Semantic
        start = time.time()
        semantic = retriever.vector_store.semantic_search(query, n_results=5)
        semantic_time = (time.time() - start) * 1000
        
        # Keyword
        start = time.time()
        keyword = retriever.vector_store.keyword_search(query, n_results=5)
        keyword_time = (time.time() - start) * 1000
        
        # Hybrid
        start = time.time()
        hybrid = retriever.vector_store.hybrid_search(query, n_results=5)
        hybrid_time = (time.time() - start) * 1000
        
        print(f"  Semantic: {semantic_time:.2f}ms (top score: {semantic[0].score:.3f})")
        print(f"  Keyword:  {keyword_time:.2f}ms (top score: {keyword[0].score:.3f})")
        print(f"  Hybrid:   {hybrid_time:.2f}ms (top score: {hybrid[0].score:.3f})")
        
        results[query_type] = {
            'semantic_time': semantic_time,
            'keyword_time': keyword_time,
            'hybrid_time': hybrid_time,
            'semantic_score': semantic[0].score,
            'keyword_score': keyword[0].score,
            'hybrid_score': hybrid[0].score
        }
    
    return results


def generate_report(all_results: Dict) -> str:
    """
    Generate a comprehensive benchmark report.
    """
    report = []
    report.append("\n" + "="*80)
    report.append("FLEETFIX RAG SYSTEM - BENCHMARK REPORT")
    report.append("="*80)
    
    # Accuracy
    if 'accuracy' in all_results:
        acc = all_results['accuracy']
        report.append("\n📊 RETRIEVAL ACCURACY")
        report.append(f"  Top-1: {acc['top1_accuracy']:.1f}%")
        report.append(f"  Top-3: {acc['top3_accuracy']:.1f}%")
        report.append(f"  Top-5: {acc['top5_accuracy']:.1f}%")
        report.append(f"  MRR:   {acc['mrr']:.3f}")
    
    # Latency
    if 'latency' in all_results:
        lat = all_results['latency']
        report.append("\n⚡ QUERY LATENCY")
        report.append(f"  Semantic Search Mean: {lat['semantic_mean_ms']:.2f}ms")
        report.append(f"  Hybrid + Reranking Mean: {lat['hybrid_mean_ms']:.2f}ms")
        report.append(f"  P95 Latency: {lat['hybrid_p95_ms']:.2f}ms")
    
    # Embedding Speed
    if 'embedding' in all_results:
        emb = all_results['embedding']
        report.append("\n🚀 EMBEDDING SPEED")
        report.append(f"  Short texts: {emb['short_throughput']:.1f} texts/sec")
        report.append(f"  Medium texts: {emb['medium_throughput']:.1f} texts/sec")
        report.append(f"  Long texts: {emb['long_throughput']:.1f} texts/sec")
    
    # Reranking Impact
    if 'reranking' in all_results:
        rank = all_results['reranking']
        report.append("\n🎯 RERANKING IMPACT")
        report.append(f"  Top-1 Improvement: +{rank['top1_improvement']:.1f}%")
        report.append(f"  Top-3 Improvement: +{rank['top3_improvement']:.1f}%")
        report.append(f"  MRR Improvement: +{rank['mrr_improvement']:.3f}")
    
    report.append("\n" + "="*80)
    
    return "\n".join(report)


def save_results(results: Dict, filename: str = "benchmark_results.json"):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to {filename}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all benchmarks"""
    print("\n" + "="*80)
    print("FLEETFIX RAG SYSTEM BENCHMARK SUITE")
    print("="*80)
    print("\nInitializing system...")
    
    # Initialize
    from document_processor import DocumentProcessor
    
    # Check if vector store exists
    if not Path("chroma_db").exists():
        print("✗ Vector store not found. Please run setup_rag.py first.")
        return
    
    vector_store = VectorStore(
        collection_name="fleetfix_docs",
        persist_directory="./chroma_db",
        embedding_model="local"
    )
    
    retriever = DocumentRetriever(
        vector_store=vector_store,
        max_context_chunks=5,
        enable_reranking=True
    )
    
    print(f"✓ System loaded ({vector_store.collection.count()} chunks)")
    
    # Run benchmarks
    all_results = {}
    
    # 1. Retrieval Accuracy
    all_results['accuracy'] = benchmark_retrieval_accuracy(retriever, TEST_QUERIES)
    
    # 2. Query Latency
    all_results['latency'] = benchmark_query_latency(retriever, num_queries=50)
    
    # 3. Embedding Speed
    all_results['embedding'] = benchmark_embedding_speed(vector_store)
    
    # 4. Reranking Impact
    all_results['reranking'] = benchmark_reranking_impact(retriever, TEST_QUERIES)
    
    # 5. Search Strategy Comparison
    all_results['strategies'] = benchmark_search_strategies(retriever)
    
    # Generate and display report
    report = generate_report(all_results)
    print(report)
    
    # Save results
    save_results(all_results)
    
    print("\n✓ Benchmark complete!")


if __name__ == "__main__":
    main()
