"""
Integration test for Text-to-SQL system
Tests: Schema Context → LLM → SQL Validator → Database Execution
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from database.config import db_config
from sqlalchemy import text


def test_end_to_end():
    """Test complete pipeline: NL query → SQL → Validation → Execution"""
    print("=" * 70)
    print("Text-to-SQL Integration Test")
    print("=" * 70)
    
    # Step 1: Build schema context
    print("\n1. Building schema context...")
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    print(f"✓ Schema context built ({len(schema_context)} chars, ~{len(schema_context)//4} tokens)")
    
    # Step 2: Initialize converter
    print("\n2. Initializing LLM converter...")
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: No API key found!")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file")
        return False
    
    converter = TextToSQLConverter(schema_context, provider=provider)
    print(f"✓ Using {provider} LLM")
    
    # Step 3: Initialize validator
    print("\n3. Initializing SQL validator...")
    validator = SQLValidator()
    print("✓ SQL validator ready")
    
    # Test queries
    test_queries = [
        {
            "query": "Show me vehicles that are overdue for maintenance",
            "should_have": ["vehicles", "next_service_due", "CURRENT_DATE"],
            "description": "Time-based filtering with CURRENT_DATE"
        },
        {
            "query": "Which drivers had harsh braking events yesterday?",
            "should_have": ["drivers", "driver_performance", "harsh_braking", "yesterday"],
            "description": "JOIN query with relative date"
        },
        {
            "query": "What are the top 5 most expensive maintenance services?",
            "should_have": ["maintenance_records", "cost", "ORDER BY", "LIMIT"],
            "description": "Aggregation with sorting and limiting"
        },
        {
            "query": "List all critical unresolved fault codes",
            "should_have": ["fault_codes", "severity", "critical", "resolved", "FALSE"],
            "description": "Filtering by multiple conditions"
        },
        {
            "query": "Show me average driver score by vehicle type over last 30 days",
            "should_have": ["AVG", "driver_performance", "vehicles", "vehicle_type", "GROUP BY"],
            "description": "Complex aggregation with JOIN and date filter"
        }
    ]
    
    print("\n" + "=" * 70)
    print("Running Test Queries")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'='*70}")
        print(f"Query: \"{test['query']}\"")
        print("-" * 70)
        
        try:
            # Generate SQL
            print("\nGenerating SQL with LLM...")
            result = converter.convert(test['query'])
            
            if result.error:
                print(f"✗ LLM Error: {result.error}")
                failed += 1
                continue
            
            print(f"✓ SQL generated (confidence: {result.confidence:.2f})")
            print(f"\nGenerated SQL:")
            print(result.sql)
            
            # Validate SQL
            print("\nValidating SQL...")
            validation = validator.validate(result.sql)
            
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
            
            # Check for expected keywords
            print("\nChecking for expected keywords...")
            sql_upper = result.sql.upper()
            missing = [kw for kw in test['should_have'] if kw.upper() not in sql_upper]
            
            if missing:
                print(f"⚠ Missing expected keywords: {', '.join(missing)}")
            else:
                print("✓ All expected keywords present")
            
            # Execute SQL
            print("\nExecuting SQL against database...")
            with db_config.session_scope() as session:
                query_result = session.execute(text(validation.sanitized_sql))
                rows = query_result.fetchall()
                
                print(f"✓ Query executed successfully")
                print(f"  Rows returned: {len(rows)}")
                
                # Show sample results
                if rows:
                    columns = query_result.keys()
                    print(f"  Columns: {', '.join(columns)}")
                    print("\n  Sample results (first 3 rows):")
                    for j, row in enumerate(rows[:3], 1):
                        print(f"    Row {j}: {dict(zip(columns, row))}")
                else:
                    print("  (No rows returned)")
            
            # Show explanation
            print(f"\nExplanation:")
            print(f"  {result.explanation}")
            
            passed += 1
            print(f"\n✓ Test {i} PASSED")
            
        except Exception as e:
            print(f"\n✗ Test {i} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests: {len(test_queries)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(test_queries)*100:.1f}%")
    
    if failed == 0:
        print("\n✓ All integration tests passed!")
        print("\nThe text-to-SQL pipeline is working correctly:")
        print("  1. Schema context is comprehensive")
        print("  2. LLM generates valid SQL")
        print("  3. SQL passes safety validation")
        print("  4. Queries execute successfully against database")
    else:
        print(f"\n⚠ {failed} test(s) failed - review errors above")
    
    print("=" * 70)
    
    return failed == 0


def test_malicious_queries():
    """Test that malicious queries are blocked"""
    print("\n" + "=" * 70)
    print("Security Test: Malicious Query Prevention")
    print("=" * 70)
    
    validator = SQLValidator()
    
    # Actually malicious queries that should be blocked
    malicious_queries = [
        ("DELETE FROM vehicles WHERE id = 1", "DELETE statement"),
        ("DROP TABLE drivers", "DROP statement"),
        ("UPDATE vehicles SET status = 'inactive'", "UPDATE statement"),
        ("INSERT INTO vehicles VALUES (1, 'test')", "INSERT statement"),
        ("SELECT * FROM vehicles; DELETE FROM drivers;", "Multiple statements"),
        ("SELECT * FROM vehicles WHERE status = 'active' -- ; DROP TABLE vehicles", "Hidden command in comment"),
        ("SELECT * FROM vehicles UNION SELECT * FROM users WHERE password = '123'", "UNION injection"),
    ]
    
    # Queries that LOOK suspicious but are safe in LLM context
    safe_but_suspicious = [
        ("SELECT * FROM vehicles WHERE 1=1", "Always-true condition (legitimate)"),
        ("SELECT * FROM vehicles WHERE 1=1 OR '1'='1'", "Classic injection pattern but safe here"),
    ]
    
    print("\nTesting malicious query blocking...")
    all_blocked = True
    
    for query, description in malicious_queries:
        result = validator.validate(query)
        status = "✓ BLOCKED" if not result.is_valid else "✗ ALLOWED"
        print(f"{status}: {description}")
        print(f"         {query[:60]}...")
        
        if result.is_valid:
            all_blocked = False
            print(f"  WARNING: This dangerous query was not blocked!")
    
    print("\nTesting safe queries that look suspicious...")
    all_allowed = True
    
    for query, description in safe_but_suspicious:
        result = validator.validate(query)
        status = "✓ ALLOWED" if result.is_valid else "✗ BLOCKED"
        print(f"{status}: {description}")
        print(f"         {query[:60]}...")
        
        if not result.is_valid:
            all_allowed = False
            print(f"  WARNING: This safe query was incorrectly blocked!")
            print(f"  Errors: {result.errors}")
    
    success = all_blocked and all_allowed
    
    if success:
        print("\n✓ Security validation working correctly:")
        print("  - All malicious queries blocked")
        print("  - Safe queries allowed (even if they look suspicious)")
    else:
        if not all_blocked:
            print("\n✗ Some malicious queries were not blocked!")
        if not all_allowed:
            print("\n✗ Some safe queries were incorrectly blocked!")
    
    return success


def test_conversation_context():
    """Test follow-up queries with conversation history"""
    print("\n" + "=" * 70)
    print("Conversation Context Test")
    print("=" * 70)
    
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("✗ Skipping (no API key)")
        return False
    
    converter = TextToSQLConverter(schema_context, provider=provider)
    
    print("\nSimulating multi-turn conversation:")
    
    # First query
    query1 = "Show me vehicles with critical fault codes"
    print(f"\nUser: {query1}")
    result1 = converter.convert(query1)
    print(f"SQL: {result1.sql[:80]}...")
    
    # Follow-up query with context
    query2 = "Now show me their maintenance history"
    print(f"\nUser: {query2} (follow-up)")
    
    conversation_history = [(query1, result1.sql)]
    result2 = converter.convert_with_conversation_history(query2, conversation_history)
    
    print(f"SQL: {result2.sql[:80]}...")
    
    # Check if it understands context
    if "maintenance" in result2.sql.lower():
        print("\n✓ Conversation context working - query references maintenance")
        return True
    else:
        print("\n⚠ Context might not be working - review SQL")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("FLEETFIX TEXT-TO-SQL SYSTEM")
    print("Complete Integration Test Suite")
    print("=" * 70)
    
    results = []
    
    # Test 1: End-to-end integration
    try:
        result = test_end_to_end()
        results.append(("Integration Test", result))
    except Exception as e:
        print(f"✗ Integration test failed with exception: {e}")
        results.append(("Integration Test", False))
    
    # Test 2: Security
    try:
        result = test_malicious_queries()
        results.append(("Security Test", result))
    except Exception as e:
        print(f"✗ Security test failed with exception: {e}")
        results.append(("Security Test", False))
    
    # Test 3: Conversation context
    try:
        result = test_conversation_context()
        results.append(("Conversation Context", result))
    except Exception as e:
        print(f"✗ Conversation test failed with exception: {e}")
        results.append(("Conversation Context", False))
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n" + "=" * 70)
        print("SUCCESS! Text-to-SQL system is fully functional!")
        print("=" * 70)
        print("\nReady for:")
        print("  1. FastAPI endpoint integration")
        print("  2. Dashboard frontend connection")
        print("  3. Daily digest generation")
        print("=" * 70)
    else:
        print(f"\n⚠ {total_tests - total_passed} test suite(s) failed")
        print("Review errors above before proceeding")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
