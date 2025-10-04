"""
Integration test for Text-to-SQL system
Tests: Schema Context → LLM → SQL Validator → Database Execution
"""

import os
import pytest
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from database.config import db_config
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.api
def test_end_to_end():
    """Test complete pipeline: NL query → SQL → Validation → Execution"""
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found - skipping integration test")
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    # Step 1: Build schema context
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    assert len(schema_context) > 1000, "Schema context should be substantial"
    
    # Step 2: Initialize converter
    converter = TextToSQLConverter(schema_context, provider=provider)
    assert converter is not None, "Converter should initialize"
    
    # Step 3: Test simple query
    test_query = "How many vehicles are there?"
    result = converter.convert(test_query)
    
    assert result is not None, "Conversion should succeed"
    assert hasattr(result, 'sql'), "Result should have sql attribute"
    assert hasattr(result, 'explanation'), "Result should have explanation attribute"
    
    sql_query = result.sql
    assert 'SELECT' in sql_query.upper(), "Should generate SELECT query"
    
    # Step 4: Validate SQL
    validator = SQLValidator()
    validation = validator.validate(sql_query)
    assert validation.is_valid, f"SQL should be valid: {validation.error or ''}"
    
    # Step 5: Execute query
    with db_config.session_scope() as session:
        try:
            result = session.execute(text(sql_query)).fetchall()
            assert result is not None, "Query should execute successfully"
        except Exception as e:
            pytest.fail(f"Query execution failed: {e}")


@pytest.mark.integration
@pytest.mark.api
def test_malicious_queries():
    """Test that malicious queries are rejected"""
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found - skipping security test")
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    converter = TextToSQLConverter(schema_context, provider=provider)
    validator = SQLValidator()
    
    malicious_queries = [
        "DROP TABLE drivers;",
        "DELETE FROM vehicles;",
        "UPDATE drivers SET name = 'hacked';",
        "INSERT INTO drivers VALUES (999, 'hacker', 'FAKE123', '2024-01-01');"
    ]
    
    for query in malicious_queries:
        # Try to convert (should fail or be sanitized)
        result = converter.convert(query)
        if result and hasattr(result, 'sql'):
            sql = result.sql
            # Validate that dangerous operations are not present
            dangerous_ops = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
            for op in dangerous_ops:
                assert op not in sql.upper(), f"Malicious query should not contain {op}: {sql}"


@pytest.mark.integration
@pytest.mark.api
def test_conversation_context():
    """Test that conversation context is handled properly"""
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found - skipping context test")
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    converter = TextToSQLConverter(schema_context, provider=provider)
    
    # Test follow-up query
    initial_query = "Show me all vehicles"
    follow_up = "How many of them are active?"
    
    # First query
    result1 = converter.convert(initial_query)
    assert result1 is not None, "Initial query should succeed"
    
    # Follow-up query (should understand context)
    result2 = converter.convert(follow_up)
    assert result2 is not None, "Follow-up query should succeed"
    
    # Both should generate valid SQL
    assert hasattr(result1, 'sql'), "Initial result should have sql attribute"
    assert hasattr(result2, 'sql'), "Follow-up result should have sql attribute"
