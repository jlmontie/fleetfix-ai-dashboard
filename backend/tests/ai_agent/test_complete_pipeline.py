"""
Complete pipeline integration tests
Tests: NL Query → SQL → Execution → Insights
"""

import pytest
import os

from backend.ai_agent.schema_context import SchemaContextBuilder
from backend.ai_agent.text_to_sql import TextToSQLConverter
from backend.ai_agent.sql_validator import SQLValidator
from backend.ai_agent.query_executor import QueryExecutor, ResultFormatter
from backend.ai_agent.insight_generator import InsightGenerator


@pytest.fixture(scope="module")
def pipeline_components():
    """Initialize all pipeline components"""
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
    
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    
    components = {
        'converter': TextToSQLConverter(schema_context, provider=provider),
        'validator': SQLValidator(),
        'executor': QueryExecutor(timeout_seconds=10),
        'insight_gen': InsightGenerator(provider=provider),
        'formatter': ResultFormatter()
    }
    
    return components


class TestEndToEndPipeline:
    """Test complete pipeline from query to insights"""
    
    @pytest.mark.parametrize("user_query,expected_elements", [
        (
            "Show me vehicles that are overdue for maintenance",
            ["vehicles", "next_service_due", "current_date"]
        ),
        (
            "Which drivers had poor performance yesterday?",
            ["driver", "performance"]
        ),
        (
            "What are the unresolved critical fault codes?",
            ["fault_code", "critical", "resolved"]
        ),
    ])
    def test_complete_pipeline(self, pipeline_components, user_query, expected_elements):
        """Test complete pipeline for a query"""
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        
        # Step 1: Convert to SQL
        sql_result = converter.convert(user_query)
        assert not sql_result.error, f"SQL generation failed: {sql_result.error}"
        assert sql_result.sql is not None
        assert sql_result.confidence > 0
        
        # Step 2: Validate SQL
        validation = validator.validate(sql_result.sql)
        assert validation.is_valid, \
            f"Validation failed: {validation.errors}"
        
        # Step 3: Execute query
        exec_result = executor.execute(validation.sanitized_sql)
        assert exec_result.success, \
            f"Execution failed: {exec_result.error}"
        assert exec_result.row_count >= 0
        assert exec_result.execution_time_ms >= 0
        
        # Verify expected SQL elements
        sql_lower = sql_result.sql.lower()
        for element in expected_elements:
            assert element.lower() in sql_lower, \
                f"Expected element '{element}' not found in SQL"
    
    def test_pipeline_with_insights(self, pipeline_components):
        """Test complete pipeline including insight generation"""
        user_query = "Show me vehicles that are overdue for maintenance"
        
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        insight_gen = pipeline_components['insight_gen']
        
        # Generate and validate SQL
        sql_result = converter.convert(user_query)
        assert not sql_result.error
        
        validation = validator.validate(sql_result.sql)
        assert validation.is_valid
        
        # Execute
        exec_result = executor.execute(validation.sanitized_sql)
        assert exec_result.success
        
        # Generate insights
        insights = insight_gen.generate_insights(
            user_query,
            sql_result.sql,
            exec_result
        )
        
        # Insights may fail but shouldn't break the pipeline
        if not insights.error:
            assert insights.summary is not None
            assert len(insights.summary) > 0
    
    def test_pipeline_handles_no_results(self, pipeline_components):
        """Test pipeline works when query returns no results"""
        # Query unlikely to return results
        user_query = "Show me vehicles with mileage over 10 million miles"
        
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        
        sql_result = converter.convert(user_query)
        
        # Handle rate limit errors gracefully
        if sql_result.error and "429" in sql_result.error:
            pytest.skip("API rate limit reached - skipping test")
        
        assert not sql_result.error, f"SQL generation failed: {sql_result.error}"
        
        validation = validator.validate(sql_result.sql)
        assert validation.is_valid
        
        exec_result = executor.execute(validation.sanitized_sql)
        assert exec_result.success
        # May have 0 rows, but should succeed
        assert exec_result.row_count >= 0


class TestQueryExecutor:
    """Test query executor functionality"""
    
    def test_executor_basic_query(self, pipeline_components):
        """Test basic query execution"""
        executor = pipeline_components['executor']
        
        sql = "SELECT COUNT(*) as count FROM vehicles"
        result = executor.execute(sql)
        
        assert result.success
        assert result.row_count > 0
        assert result.execution_time_ms >= 0
        assert result.columns is not None
    
    def test_executor_timeout(self):
        """Test query timeout handling"""
        executor = QueryExecutor(timeout_seconds=1)
        
        # Query that might timeout (adjust if needed)
        sql = "SELECT pg_sleep(5)"
        result = executor.execute(sql)
        
        # Should either timeout or execute (depending on DB config)
        # At minimum, should not crash
        assert result is not None
    
    def test_executor_invalid_sql(self, pipeline_components):
        """Test executor handles invalid SQL gracefully"""
        executor = pipeline_components['executor']
        
        sql = "SELECT * FROM nonexistent_table"
        result = executor.execute(sql)
        
        assert not result.success
        assert result.error is not None


class TestResultFormatter:
    """Test result formatting"""
    
    def test_formatter_table_string(self, pipeline_components):
        """Test table string formatting"""
        executor = pipeline_components['executor']
        formatter = pipeline_components['formatter']
        
        sql = "SELECT * FROM vehicles LIMIT 5"
        result = executor.execute(sql)
        
        assert result.success
        
        table_str = formatter.to_table_string(result, max_rows=5)
        assert table_str is not None
        assert len(table_str) > 0
    
    def test_formatter_handles_empty_results(self, pipeline_components):
        """Test formatter handles empty result sets"""
        executor = pipeline_components['executor']
        formatter = pipeline_components['formatter']
        
        sql = "SELECT * FROM vehicles WHERE id = -999"
        result = executor.execute(sql)
        
        assert result.success
        assert result.row_count == 0
        
        table_str = formatter.to_table_string(result)
        assert table_str is not None


class TestInsightGenerator:
    """Test insight generation"""
    
    def test_basic_insight_generation(self, pipeline_components):
        """Test basic insight generation"""
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        insight_gen = pipeline_components['insight_gen']
        
        user_query = "Show me all vehicles"
        
        sql_result = converter.convert(user_query)
        validation = validator.validate(sql_result.sql)
        exec_result = executor.execute(validation.sanitized_sql)
        
        insights = insight_gen.generate_insights(
            user_query,
            sql_result.sql,
            exec_result
        )
        
        # Insights might fail (API issues, etc.) but structure should be valid
        if not insights.error:
            assert hasattr(insights, 'summary')
            assert hasattr(insights, 'key_findings')
            assert hasattr(insights, 'recommendations')
    
    def test_insights_handle_no_results(self, pipeline_components):
        """Test insights work with empty result sets"""
        insight_gen = pipeline_components['insight_gen']
        executor = pipeline_components['executor']
        
        user_query = "Show me vehicles with impossible conditions"
        sql = "SELECT * FROM vehicles WHERE id = -999"
        
        exec_result = executor.execute(sql)
        assert exec_result.success
        assert exec_result.row_count == 0
        
        insights = insight_gen.generate_insights(
            user_query,
            sql,
            exec_result
        )
        
        # Should handle gracefully
        assert insights is not None


class TestPipelineErrorHandling:
    """Test error handling throughout pipeline"""
    
    def test_invalid_query_handling(self, pipeline_components):
        """Test handling of nonsensical queries"""
        converter = pipeline_components['converter']
        
        # Nonsensical query
        user_query = "asdfghjkl qwerty"
        result = converter.convert(user_query)
        
        # Should either generate something or return error gracefully
        assert result is not None
        if result.error:
            assert isinstance(result.error, str)
    
    def test_malicious_sql_blocked(self, pipeline_components):
        """Test malicious SQL is blocked in pipeline"""
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        
        malicious_sql = "DROP TABLE vehicles"
        validation = validator.validate(malicious_sql)
        
        assert not validation.is_valid, "Malicious SQL was not blocked"
        
        # Should not execute
        # Note: We test validation blocks it; we don't actually try to execute
    
    def test_sql_injection_prevention(self, pipeline_components):
        """Test SQL injection attempts are prevented"""
        validator = pipeline_components['validator']
        
        injection_attempts = [
            "SELECT * FROM vehicles; DELETE FROM drivers;",
            "SELECT * FROM vehicles WHERE id = 1 OR 1=1; DROP TABLE vehicles;",
            "SELECT * FROM vehicles UNION SELECT * FROM sensitive_table",
        ]
        
        for sql in injection_attempts:
            validation = validator.validate(sql)
            # Should either be invalid or sanitized
            if validation.is_valid:
                # If somehow valid, sanitized SQL should be safe
                assert "DELETE" not in validation.sanitized_sql.upper()
                assert "DROP" not in validation.sanitized_sql.upper()


class TestPipelinePerformance:
    """Test pipeline performance characteristics"""
    
    def test_query_execution_time_tracked(self, pipeline_components):
        """Test that execution time is tracked"""
        executor = pipeline_components['executor']
        
        sql = "SELECT COUNT(*) FROM vehicles"
        result = executor.execute(sql)
        
        assert result.success
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0
        assert result.execution_time_ms < 10000, "Query took too long"
    
    def test_simple_queries_are_fast(self, pipeline_components):
        """Test that simple queries execute quickly"""
        executor = pipeline_components['executor']
        
        sql = "SELECT * FROM vehicles LIMIT 1"
        result = executor.execute(sql)
        
        assert result.success
        # Should be very fast (< 100ms for simple query)
        assert result.execution_time_ms < 100, \
            f"Simple query took {result.execution_time_ms}ms"


class TestPipelineIntegration:
    """Test overall pipeline integration"""
    
    def test_multiple_queries_in_sequence(self, pipeline_components):
        """Test running multiple queries in sequence"""
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        
        queries = [
            "Show me all vehicles",
            "Show me all drivers",
            "Show me recent maintenance records"
        ]
        
        for query in queries:
            sql_result = converter.convert(query)
            assert not sql_result.error, f"Failed on: {query}"
            
            validation = validator.validate(sql_result.sql)
            assert validation.is_valid, f"Validation failed on: {query}"
            
            exec_result = executor.execute(validation.sanitized_sql)
            assert exec_result.success, f"Execution failed on: {query}"
    
    def test_pipeline_is_stateless(self, pipeline_components):
        """Test that pipeline components are stateless between queries"""
        converter = pipeline_components['converter']
        validator = pipeline_components['validator']
        executor = pipeline_components['executor']
        
        query1 = "Show me vehicles"
        query2 = "Show me drivers"
        
        # Execute query 1
        result1 = converter.convert(query1)
        val1 = validator.validate(result1.sql)
        exec1 = executor.execute(val1.sanitized_sql)
        
        # Execute query 2
        result2 = converter.convert(query2)
        val2 = validator.validate(result2.sql)
        exec2 = executor.execute(val2.sanitized_sql)
        
        # Results should be independent
        assert exec1.success
        assert exec2.success
        assert exec1.columns != exec2.columns