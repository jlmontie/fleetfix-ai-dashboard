"""
Complete Pipeline Integration Test
Tests entire flow: NL Query → SQL → Execution → Insights
"""

import os
import pytest
from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from ai_agent.query_executor import QueryExecutor, ResultFormatter
from ai_agent.insight_generator import InsightGenerator


@pytest.mark.pipeline
@pytest.mark.api
def test_complete_pipeline():
    """Test complete end-to-end pipeline with multiple queries"""
    # Check API key
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found - skipping pipeline test")
    
    # Initialize components
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    assert len(schema_context) > 1000, "Schema context should be substantial"
    
    converter = TextToSQLConverter(schema_context, provider=provider)
    validator = SQLValidator()
    executor = QueryExecutor(timeout_seconds=10)
    insight_gen = InsightGenerator(provider=provider)
    formatter = ResultFormatter()
    
    # Test multiple queries like the original
    test_queries = [
        "Show me vehicles that are overdue for maintenance",
        "Which drivers had poor performance yesterday?",
        "What are the unresolved critical fault codes?",
    ]
    
    for user_query in test_queries:
        # Step 1: Convert to SQL
        sql_result = converter.convert(user_query)
        assert sql_result is not None, f"SQL conversion should succeed for: {user_query}"
        assert not sql_result.error, f"SQL generation should not have errors: {sql_result.error}"
        assert hasattr(sql_result, 'sql'), "Result should have sql attribute"
        assert hasattr(sql_result, 'explanation'), "Result should have explanation attribute"
        assert hasattr(sql_result, 'confidence'), "Result should have confidence attribute"
        
        sql_query = sql_result.sql
        assert 'SELECT' in sql_query.upper(), "Generated SQL should be a SELECT query"
        
        # Step 2: Validate SQL
        validation = validator.validate(sql_query)
        assert validation.is_valid, f"SQL should be valid: {validation.error or ''}"
        
        # Step 3: Execute query
        exec_result = executor.execute(validation.sanitized_sql)
        assert exec_result.success, f"Query execution should succeed: {exec_result.error or ''}"
        assert exec_result.row_count >= 0, "Should return non-negative row count"
        
        # Step 4: Generate insights
        insights = insight_gen.generate_insights(
            user_query,
            sql_result.sql,
            exec_result
        )
        assert insights is not None, "Insights should be generated"
        assert not insights.error, f"Insight generation should not have errors: {insights.error}"
        assert hasattr(insights, 'summary'), "Insights should have summary"
        assert hasattr(insights, 'insights'), "Insights should have insights attribute"
        assert hasattr(insights, 'key_findings'), "Insights should have key_findings"
        assert hasattr(insights, 'recommendations'), "Insights should have recommendations"


@pytest.mark.pipeline
@pytest.mark.api
def test_pipeline_components_initialization():
    """Test that all pipeline components can be initialized"""
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found - skipping component test")
    
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    # Test schema context builder
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    assert len(schema_context) > 0, "Schema context should be generated"
    
    # Test text-to-SQL converter
    converter = TextToSQLConverter(schema_context, provider=provider)
    assert converter is not None, "Text-to-SQL converter should initialize"
    
    # Test SQL validator
    validator = SQLValidator()
    assert validator is not None, "SQL validator should initialize"
    
    # Test query executor
    executor = QueryExecutor(timeout_seconds=10)
    assert executor is not None, "Query executor should initialize"
    
    # Test insight generator
    insight_gen = InsightGenerator(provider=provider)
    assert insight_gen is not None, "Insight generator should initialize"


@pytest.mark.pipeline
def test_schema_context_generation():
    """Test schema context generation without API calls"""
    builder = SchemaContextBuilder()
    
    # Test full context
    full_context = builder.build_schema_context()
    assert len(full_context) > 1000, "Full context should be substantial"
    assert "FleetFix Database Schema" in full_context, "Should contain schema title"
    
    # Test concise context
    concise_context = builder.build_concise_context()
    assert len(concise_context) < len(full_context), "Concise should be shorter"
    assert len(concise_context) > 100, "Concise should still be meaningful"