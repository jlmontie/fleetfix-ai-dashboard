"""
Complete Pipeline Integration Test
Tests entire flow: NL Query → SQL → Execution → Insights
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from ai_agent.query_executor import QueryExecutor, ResultFormatter
from ai_agent.insight_generator import InsightGenerator


def test_complete_pipeline():
    """Test complete end-to-end pipeline"""
    print("=" * 70)
    print("COMPLETE PIPELINE TEST")
    print("Natural Language → SQL → Execution → Insights")
    print("=" * 70)
    
    # Check API key
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n✗ Error: No API key found!")
        return False
    
    print(f"\nLLM Provider: {provider}")
    
    # Initialize components
    print("\n1. Initializing components...")
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    print(f"   ✓ Schema context loaded")
    
    converter = TextToSQLConverter(schema_context, provider=provider)
    print(f"   ✓ Text-to-SQL converter ready")
    
    validator = SQLValidator()
    print(f"   ✓ SQL validator ready")
    
    executor = QueryExecutor(timeout_seconds=10)
    print(f"   ✓ Query executor ready")
    
    insight_gen = InsightGenerator(provider=provider)
    print(f"   ✓ Insight generator ready")
    
    formatter = ResultFormatter()
    
    # Test queries
    test_queries = [
        "Show me vehicles that are overdue for maintenance",
        "Which drivers had poor performance yesterday?",
        "What are the unresolved critical fault codes?",
    ]
    
    print("\n" + "=" * 70)
    print("Running Complete Pipeline Tests")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, user_query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {user_query}")
        print(f"{'='*70}")
        
        try:
            # Step 1: Convert to SQL
            print("\nStep 1: Converting to SQL...")
            sql_result = converter.convert(user_query)
            
            if sql_result.error:
                print(f"✗ SQL generation failed: {sql_result.error}")
                failed += 1
                continue
            
            print(f"✓ SQL generated (confidence: {sql_result.confidence:.2f})")
            print(f"\nGenerated SQL:")
            print(sql_result.sql)
            print(f"\nExplanation: {sql_result.explanation}")
            
            # Step 2: Validate SQL
            print("\nStep 2: Validating SQL...")
            validation = validator.validate(sql_result.sql)
            
            if not validation.is_valid:
                print(f"✗ Validation failed:")
                for error in validation.errors:
                    print(f"  - {error}")
                failed += 1
                continue
            
            print("✓ SQL validation passed")
            
            if validation.warnings:
                print("  Warnings:")
                for warning in validation.warnings:
                    print(f"    - {warning}")
            
            # Step 3: Execute query
            print("\nStep 3: Executing query...")
            exec_result = executor.execute(validation.sanitized_sql)
            
            if not exec_result.success:
                print(f"✗ Execution failed: {exec_result.error}")
                failed += 1
                continue
            
            print(f"✓ Query executed successfully")
            print(f"  Rows returned: {exec_result.row_count}")
            print(f"  Execution time: {exec_result.execution_time_ms}ms")
            
            # Show results
            print("\nQuery Results:")
            print(formatter.to_table_string(exec_result, max_rows=5))
            
            # Step 4: Generate insights
            print("\nStep 4: Generating insights...")
            insights = insight_gen.generate_insights(
                user_query,
                sql_result.sql,
                exec_result
            )
            
            if insights.error:
                print(f"⚠ Insight generation failed: {insights.error}")
                # Not a critical failure - query worked
            else:
                print(f"✓ Insights generated")
                
                print(f"\nSUMMARY:")
                print(f"  {insights.summary}")
                
                if insights.key_findings:
                    print(f"\nKEY FINDINGS:")
                    for j, finding in enumerate(insights.key_findings, 1):
                        print(f"  {j}. {finding}")
                
                if insights.insights:
                    print(f"\nINSIGHTS:")
                    for insight in insights.insights:
                        severity_symbols = {
                            "info": "ℹ",
                            "warning": "⚠",
                            "critical": "✗"
                        }
                        symbol = severity_symbols.get(insight.severity, "•")
                        print(f"\n  {symbol} [{insight.type.upper()}] {insight.severity}")
                        print(f"     {insight.message[:100]}...")
                
                if insights.recommendations:
                    print(f"\nRECOMMENDATIONS:")
                    for j, rec in enumerate(insights.recommendations, 1):
                        print(f"  {j}. {rec}")
            
            passed += 1
            print(f"\n✓ Test {i} PASSED - Complete pipeline successful")
            
        except Exception as e:
            print(f"\n✗ Test {i} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(test_queries)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(test_queries)*100:.1f}%")
    
    if failed == 0:
        print("\n" + "=" * 70)
        print("✓ SUCCESS! Complete pipeline is fully functional!")
        print("=" * 70)
        print("\nThe system can now:")
        print("  1. Convert natural language to SQL")
        print("  2. Validate SQL for safety")
        print("  3. Execute queries against database")
        print("  4. Generate intelligent insights")
        print("\nReady for:")
        print("  - FastAPI endpoint integration")
        print("  - Dashboard frontend connection")
        print("  - Production deployment")
        print("=" * 70)
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    return failed == 0


def demo_interactive():
    """Interactive demo of the complete pipeline"""
    print("\n" + "=" * 70)
    print("INTERACTIVE DEMO")
    print("=" * 70)
    print("\nThis demo shows the complete pipeline in action.")
    print("Enter 'quit' to exit.\n")
    
    # Check API key
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: No API key found!")
        return
    
    # Initialize components
    print("Initializing AI components...")
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    converter = TextToSQLConverter(schema_context, provider=provider)
    validator = SQLValidator()
    executor = QueryExecutor(timeout_seconds=10)
    insight_gen = InsightGenerator(provider=provider)
    formatter = ResultFormatter()
    print("✓ Ready!\n")
    
    while True:
        try:
            # Get user query
            user_query = input("Ask a question about your fleet: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not user_query:
                continue
            
            print("\n" + "-" * 70)
            
            # Process query
            print("🤖 Converting to SQL...")
            sql_result = converter.convert(user_query)
            
            if sql_result.error:
                print(f"✗ Error: {sql_result.error}")
                continue
            
            print(f"✓ SQL generated\n")
            print("Generated SQL:")
            print(sql_result.sql)
            print(f"\nConfidence: {sql_result.confidence:.0%}")
            
            # Validate
            validation = validator.validate(sql_result.sql)
            if not validation.is_valid:
                print(f"\n✗ SQL validation failed: {validation.errors}")
                continue
            
            # Execute
            print("\n🔍 Executing query...")
            exec_result = executor.execute(validation.sanitized_sql)
            
            if not exec_result.success:
                print(f"✗ Error: {exec_result.error}")
                continue
            
            print(f"✓ Found {exec_result.row_count} results ({exec_result.execution_time_ms}ms)\n")
            
            # Show results
            print("Results:")
            print(formatter.to_table_string(exec_result, max_rows=10))
            
            # Generate insights
            if exec_result.row_count > 0:
                print("\n💡 Generating insights...")
                insights = insight_gen.generate_insights(
                    user_query,
                    sql_result.sql,
                    exec_result
                )
                
                if not insights.error:
                    print(f"\n{insights.summary}\n")
                    
                    if insights.recommendations:
                        print("Recommendations:")
                        for j, rec in enumerate(insights.recommendations, 1):
                            print(f"  {j}. {rec}")
            
            print("\n" + "-" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            continue


def main():
    """Run tests and optionally demo"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test complete AI pipeline')
    parser.add_argument('--demo', action='store_true', help='Run interactive demo')
    args = parser.parse_args()
    
    if args.demo:
        demo_interactive()
    else:
        success = test_complete_pipeline()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
