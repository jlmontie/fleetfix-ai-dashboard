"""
Text-to-SQL integration tests
"""

import pytest
import os
from sqlalchemy import text

from ai_agent.schema_context import SchemaContextBuilder
from ai_agent.text_to_sql import TextToSQLConverter
from ai_agent.sql_validator import SQLValidator
from database.config import db_config


@pytest.fixture(scope="module")
def schema_context():
    """Build schema context once for all tests"""
    builder = SchemaContextBuilder()
    return builder.build_schema_context()


@pytest.fixture(scope="module")
def converter(schema_context):
    """Create text-to-SQL converter"""
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key found (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
    
    return TextToSQLConverter(schema_context, provider=provider)


@pytest.fixture(scope="module")
def validator():
    """Create SQL validator"""
    return SQLValidator()


class TestSQLGeneration:
    """Test SQL generation from natural language"""
    
    def test_simple_filtering_query(self, converter, validator):
        """Test: vehicles overdue for maintenance"""
        query = "Show me vehicles that are overdue for maintenance"
        result = converter.convert(query)
        
        assert not result.error, f"SQL generation failed: {result.error}"
        assert result.sql is not None
        assert result.confidence > 0
        
        # Validate SQL
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        # Check for expected elements
        sql_upper = result.sql.upper()
        assert "VEHICLES" in sql_upper
        assert "NEXT_SERVICE_DUE" in sql_upper or "SERVICE" in sql_upper
    
    def test_join_query(self, converter, validator):
        """Test: drivers with harsh braking events"""
        query = "Which drivers had harsh braking events yesterday?"
        result = converter.convert(query)
        
        assert not result.error, f"SQL generation failed: {result.error}"
        
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        sql_upper = result.sql.upper()
        assert "DRIVER" in sql_upper
        assert "HARSH_BRAKING" in sql_upper or "BRAKING" in sql_upper
    
    def test_aggregation_query(self, converter, validator):
        """Test: top 5 most expensive maintenance services"""
        query = "What are the top 5 most expensive maintenance services?"
        result = converter.convert(query)
        
        assert not result.error, f"SQL generation failed: {result.error}"
        
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        sql_upper = result.sql.upper()
        assert "MAINTENANCE" in sql_upper
        assert "COST" in sql_upper
        assert "ORDER BY" in sql_upper
        assert "LIMIT" in sql_upper or "TOP" in sql_upper
    
    def test_multiple_conditions_query(self, converter, validator):
        """Test: critical unresolved fault codes"""
        query = "List all critical unresolved fault codes"
        result = converter.convert(query)
        
        assert not result.error, f"SQL generation failed: {result.error}"
        
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        sql_upper = result.sql.upper()
        assert "FAULT_CODE" in sql_upper or "FAULT" in sql_upper
        assert "CRITICAL" in sql_upper
        assert "RESOLVED" in sql_upper or "FALSE" in sql_upper
    
    def test_complex_aggregation_with_join(self, converter, validator):
        """Test: average driver score by vehicle type"""
        query = "Show me average driver score by vehicle type over last 30 days"
        result = converter.convert(query)
        
        assert not result.error, f"SQL generation failed: {result.error}"
        
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        sql_upper = result.sql.upper()
        assert "AVG" in sql_upper or "AVERAGE" in sql_upper
        assert "DRIVER" in sql_upper
        assert "GROUP BY" in sql_upper


class TestSQLExecution:
    """Test that generated SQL executes successfully"""
    
    @pytest.mark.parametrize("query", [
        "Show me vehicles that are overdue for maintenance",
        "What are the top 5 most expensive maintenance services?",
        "List all critical unresolved fault codes",
    ])
    def test_query_executes(self, converter, validator, query):
        """Test that queries execute without errors"""
        result = converter.convert(query)
        assert not result.error, f"SQL generation failed: {result.error}"
        
        validation = validator.validate(result.sql)
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        # Execute the query
        with db_config.session_scope() as session:
            query_result = session.execute(text(validation.sanitized_sql))
            rows = query_result.fetchall()
            
            # Should not raise exception
            assert rows is not None
            
            # Should have column names
            columns = query_result.keys()
            assert len(columns) > 0


class TestSQLSecurity:
    """Test SQL injection prevention"""
    
    def test_delete_statement_blocked(self, validator):
        """Test DELETE statements are blocked"""
        sql = "DELETE FROM vehicles WHERE id = 1"
        validation = validator.validate(sql)
        
        assert not validation.is_valid, "DELETE statement should be blocked"
        assert any("DELETE" in str(err).upper() for err in validation.errors)
    
    def test_drop_statement_blocked(self, validator):
        """Test DROP statements are blocked"""
        sql = "DROP TABLE drivers"
        validation = validator.validate(sql)
        
        assert not validation.is_valid, "DROP statement should be blocked"
        assert any("DROP" in str(err).upper() for err in validation.errors)
    
    def test_update_statement_blocked(self, validator):
        """Test UPDATE statements are blocked"""
        sql = "UPDATE vehicles SET status = 'inactive'"
        validation = validator.validate(sql)
        
        assert not validation.is_valid, "UPDATE statement should be blocked"
        assert any("UPDATE" in str(err).upper() for err in validation.errors)
    
    def test_insert_statement_blocked(self, validator):
        """Test INSERT statements are blocked"""
        sql = "INSERT INTO vehicles VALUES (1, 'test')"
        validation = validator.validate(sql)
        
        assert not validation.is_valid, "INSERT statement should be blocked"
        assert any("INSERT" in str(err).upper() for err in validation.errors)
    
    def test_multiple_statements_blocked(self, validator):
        """Test multiple statements are blocked"""
        sql = "SELECT * FROM vehicles; DELETE FROM drivers;"
        validation = validator.validate(sql)
        
        assert not validation.is_valid, "Multiple statements should be blocked"
    
    def test_union_injection_blocked(self, validator):
        """Test UNION-based injection attempts are blocked"""
        sql = "SELECT * FROM vehicles UNION SELECT * FROM users WHERE password = '123'"
        validation = validator.validate(sql)
        
        # Should either block UNION or the non-existent users table
        # At minimum should not execute successfully
        assert not validation.is_valid or "users" not in sql.lower()
    
    def test_safe_queries_allowed(self, validator):
        """Test legitimate queries are allowed"""
        safe_queries = [
            "SELECT * FROM vehicles WHERE status = 'active'",
            "SELECT COUNT(*) FROM drivers",
            "SELECT make, model FROM vehicles WHERE year > 2020",
        ]
        
        for sql in safe_queries:
            validation = validator.validate(sql)
            assert validation.is_valid, \
                f"Safe query blocked: {sql}\nErrors: {validation.errors}"


class TestConversationContext:
    """Test follow-up query handling"""
    
    def test_follow_up_query(self, converter, validator):
        """Test that follow-up queries work with conversation history"""
        # First query
        query1 = "Show me vehicles with critical fault codes"
        result1 = converter.convert(query1)
        
        assert not result1.error
        
        # Follow-up query
        query2 = "Now show me their maintenance history"
        conversation_history = [(query1, result1.sql)]
        result2 = converter.convert_with_conversation_history(
            query2, conversation_history
        )
        
        assert not result2.error
        
        # Should reference maintenance in some way
        assert "maintenance" in result2.sql.lower(), \
            "Follow-up query didn't understand context"
    
    def test_conversation_history_improves_query(self, converter):
        """Test that conversation history helps disambiguate queries"""
        # Ambiguous follow-up without context
        query = "Show me their performance"
        result_no_context = converter.convert(query)
        
        # Same query with context
        history = [
            ("Which drivers had harsh braking?", 
             "SELECT * FROM drivers WHERE harsh_braking > 5")
        ]
        result_with_context = converter.convert_with_conversation_history(
            query, history
        )
        
        # Both should work, but with context should be more specific
        assert not result_no_context.error
        assert not result_with_context.error


class TestSQLQuality:
    """Test quality of generated SQL"""
    
    def test_sql_has_explanation(self, converter):
        """Test that SQL generation includes explanation"""
        query = "Show me vehicles that are overdue for maintenance"
        result = converter.convert(query)
        
        assert not result.error
        assert result.explanation is not None
        assert len(result.explanation) > 10, "Explanation is too short"
    
    def test_confidence_score_reasonable(self, converter):
        """Test that confidence scores are reasonable"""
        query = "Show me all vehicles"
        result = converter.convert(query)
        
        assert not result.error
        assert 0 <= result.confidence <= 1, \
            f"Confidence {result.confidence} outside [0,1] range"
    
    def test_sql_is_formatted(self, converter):
        """Test that SQL is reasonably formatted"""
        query = "Show me vehicles that are overdue for maintenance"
        result = converter.convert(query)
        
        assert not result.error
        # Should have some structure (newlines or proper spacing)
        assert len(result.sql.split()) > 3, "SQL seems malformed"
