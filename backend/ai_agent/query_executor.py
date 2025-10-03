"""
FleetFix Query Executor
Safely executes SQL queries and formats results
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.config import db_config


@dataclass
class QueryResult:
    """Result of query execution"""
    success: bool
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None


class QueryExecutor:
    """
    Executes SQL queries safely with timeout and error handling
    """
    
    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize executor
        
        Args:
            timeout_seconds: Maximum query execution time
        """
        self.timeout_seconds = timeout_seconds
    
    def execute(self, sql: str, session: Optional[Session] = None) -> QueryResult:
        """
        Execute SQL query and return formatted results
        
        Args:
            sql: SQL query to execute (should be validated first)
            session: Optional database session (creates new if not provided)
        
        Returns:
            QueryResult with execution details
        """
        start_time = datetime.now()
        
        # Use provided session or create new one
        close_session = session is None
        if session is None:
            session = db_config.get_session()
        
        try:
            # Set query timeout
            session.execute(text(f"SET statement_timeout = {self.timeout_seconds * 1000}"))
            
            # Execute query
            result = session.execute(text(sql))
            
            # Fetch results
            rows = result.fetchall()
            columns = list(result.keys()) if rows else []
            
            # Convert rows to dictionaries with serializable values
            formatted_rows = []
            for row in rows:
                row_dict = {}
                for col_name, value in zip(columns, row):
                    row_dict[col_name] = self._serialize_value(value)
                formatted_rows.append(row_dict)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                success=True,
                rows=formatted_rows,
                columns=columns,
                row_count=len(formatted_rows),
                execution_time_ms=round(execution_time, 2),
                error=None
            )
        
        except SQLAlchemyError as e:
            # Database error
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = self._format_db_error(e)
            
            return QueryResult(
                success=False,
                rows=[],
                columns=[],
                row_count=0,
                execution_time_ms=round(execution_time, 2),
                error=error_msg
            )
        
        except Exception as e:
            # Unexpected error
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                success=False,
                rows=[],
                columns=[],
                row_count=0,
                execution_time_ms=round(execution_time, 2),
                error=f"Unexpected error: {str(e)}"
            )
        
        finally:
            if close_session:
                session.close()
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Convert database values to JSON-serializable types
        
        Args:
            value: Database value
        
        Returns:
            JSON-serializable value
        """
        if value is None:
            return None
        
        # Handle date/time types
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, time):
            return value.isoformat()
        
        # Handle numeric types
        elif isinstance(value, Decimal):
            return float(value)
        
        # Handle bytes
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        
        # Everything else
        return value
    
    def _format_db_error(self, error: SQLAlchemyError) -> str:
        """
        Format database error for user display
        
        Args:
            error: SQLAlchemy error
        
        Returns:
            User-friendly error message
        """
        error_str = str(error)
        
        # Common error patterns
        if 'timeout' in error_str.lower():
            return f"Query timeout: Query took longer than {self.timeout_seconds} seconds"
        
        if 'syntax error' in error_str.lower():
            return f"SQL syntax error: {error_str}"
        
        if 'does not exist' in error_str.lower():
            return f"Table or column not found: {error_str}"
        
        if 'permission denied' in error_str.lower():
            return "Permission denied: Insufficient database privileges"
        
        # Generic error
        return f"Database error: {error_str}"
    
    def execute_with_limit(
        self,
        sql: str,
        max_rows: int = 1000,
        session: Optional[Session] = None
    ) -> QueryResult:
        """
        Execute query with automatic LIMIT to prevent large result sets
        
        Args:
            sql: SQL query
            max_rows: Maximum rows to return
            session: Optional database session
        
        Returns:
            QueryResult
        """
        # Add LIMIT if not present
        sql_upper = sql.upper().strip()
        
        if 'LIMIT' not in sql_upper:
            # Remove trailing semicolon if present
            sql = sql.rstrip().rstrip(';')
            sql = f"{sql} LIMIT {max_rows};"
        
        return self.execute(sql, session)
    
    def get_sample_results(
        self,
        sql: str,
        sample_size: int = 5,
        session: Optional[Session] = None
    ) -> QueryResult:
        """
        Execute query and return only sample results
        Useful for preview without loading entire dataset
        
        Args:
            sql: SQL query
            sample_size: Number of sample rows
            session: Optional database session
        
        Returns:
            QueryResult with limited rows
        """
        return self.execute_with_limit(sql, max_rows=sample_size, session=session)


class ResultFormatter:
    """
    Formats query results for different output types
    """
    
    @staticmethod
    def to_table_string(result: QueryResult, max_rows: int = 20) -> str:
        """
        Format results as ASCII table
        
        Args:
            result: Query result
            max_rows: Maximum rows to display
        
        Returns:
            Formatted table string
        """
        if not result.success:
            return f"Error: {result.error}"
        
        if result.row_count == 0:
            return "No results found"
        
        # Calculate column widths
        col_widths = {}
        for col in result.columns:
            col_widths[col] = len(col)
        
        for row in result.rows[:max_rows]:
            for col in result.columns:
                value_str = str(row.get(col, ''))
                col_widths[col] = max(col_widths[col], len(value_str))
        
        # Build table
        lines = []
        
        # Header
        header = " | ".join(col.ljust(col_widths[col]) for col in result.columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for row in result.rows[:max_rows]:
            row_str = " | ".join(
                str(row.get(col, '')).ljust(col_widths[col])
                for col in result.columns
            )
            lines.append(row_str)
        
        # Footer
        if result.row_count > max_rows:
            lines.append(f"\n... {result.row_count - max_rows} more rows")
        
        lines.append(f"\nTotal: {result.row_count} rows ({result.execution_time_ms}ms)")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_summary(result: QueryResult) -> Dict[str, Any]:
        """
        Create summary statistics of results
        
        Args:
            result: Query result
        
        Returns:
            Summary dictionary
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error
            }
        
        summary = {
            "success": True,
            "row_count": result.row_count,
            "column_count": len(result.columns),
            "columns": result.columns,
            "execution_time_ms": result.execution_time_ms,
            "has_data": result.row_count > 0
        }
        
        # Add column type inference
        if result.rows:
            column_types = {}
            first_row = result.rows[0]
            
            for col in result.columns:
                value = first_row.get(col)
                if value is None:
                    column_types[col] = "null"
                elif isinstance(value, bool):
                    column_types[col] = "boolean"
                elif isinstance(value, int):
                    column_types[col] = "integer"
                elif isinstance(value, float):
                    column_types[col] = "float"
                elif isinstance(value, str):
                    # Check if it looks like a date
                    if any(char in value for char in ['-', '/', ':']):
                        column_types[col] = "datetime"
                    else:
                        column_types[col] = "string"
                else:
                    column_types[col] = "unknown"
            
            summary["column_types"] = column_types
        
        return summary


def main():
    """Test query executor"""
    print("=" * 70)
    print("FleetFix Query Executor - Test")
    print("=" * 70)
    
    executor = QueryExecutor(timeout_seconds=10)
    formatter = ResultFormatter()
    
    # Test queries
    test_queries = [
        ("SELECT * FROM vehicles LIMIT 5", "Simple SELECT with LIMIT"),
        ("SELECT make, model, COUNT(*) as count FROM vehicles GROUP BY make, model", "Aggregation"),
        ("SELECT COUNT(*) as total_vehicles FROM vehicles", "Count query"),
        ("SELECT * FROM vehicles WHERE status = 'nonexistent'", "Empty result set"),
        ("SELECT * FROM invalid_table", "Invalid table (should error)"),
    ]
    
    print("\nExecuting test queries...")
    print("=" * 70)
    
    for sql, description in test_queries:
        print(f"\n{description}")
        print(f"SQL: {sql}")
        print("-" * 70)
        
        result = executor.execute(sql)
        
        if result.success:
            print(f"✓ Success ({result.row_count} rows, {result.execution_time_ms}ms)")
            print(formatter.to_table_string(result, max_rows=5))
        else:
            print(f"✗ Error: {result.error}")
    
    # Test with limit
    print("\n" + "=" * 70)
    print("Testing automatic LIMIT")
    print("=" * 70)
    
    sql_no_limit = "SELECT * FROM telemetry"
    print(f"\nQuery without LIMIT: {sql_no_limit}")
    
    result = executor.execute_with_limit(sql_no_limit, max_rows=10)
    print(f"✓ Automatically limited to {result.row_count} rows")
    
    # Test sample results
    print("\n" + "=" * 70)
    print("Testing sample results")
    print("=" * 70)
    
    result = executor.get_sample_results("SELECT * FROM drivers", sample_size=3)
    print(formatter.to_table_string(result))
    
    # Test summary
    print("\n" + "=" * 70)
    print("Testing result summary")
    print("=" * 70)
    
    result = executor.execute("SELECT * FROM vehicles LIMIT 5")
    summary = formatter.to_summary(result)
    
    print("Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("Query executor ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()
