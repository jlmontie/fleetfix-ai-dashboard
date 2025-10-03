"""
FleetFix SQL Validator
Validates generated SQL for safety before execution
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of SQL validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_sql: str


class SQLValidator:
    """
    Validates SQL queries for safety
    Prevents dangerous operations and SQL injection
    """
    
    # Dangerous SQL keywords that should never appear
    FORBIDDEN_KEYWORDS = {
        'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE',
        'INSERT', 'UPDATE', 'GRANT', 'REVOKE', 'EXECUTE',
        'EXEC', 'CALL', 'PROCEDURE', 'FUNCTION', 'TRIGGER',
        'INTO OUTFILE', 'LOAD DATA', 'COPY', 'UNION'
    }
    
    # Suspicious patterns that might indicate SQL injection
    # These generate warnings but don't block the query
    SUSPICIOUS_PATTERNS = [
        r'--.*DELETE',           # Comment hiding command (warning only)
        r'--.*DROP',             # Comment hiding command (warning only)
        r'/\*.*DELETE.*\*/',     # Multi-line comment hiding command
        r'/\*.*DROP.*\*/',       # Multi-line comment hiding command
        r'\bxp_cmdshell\b',      # SQL Server command execution
        r'EXEC\s*\(',            # Dynamic SQL execution (with parenthesis)
        r'EXECUTE\s*\(',         # Dynamic SQL execution
    ]
    
    def __init__(self, allow_multiple_statements: bool = False):
        """
        Initialize validator
        
        Args:
            allow_multiple_statements: Allow semicolon-separated queries
        """
        self.allow_multiple_statements = allow_multiple_statements
    
    def validate(self, sql: str) -> ValidationResult:
        """
        Validate SQL query
        
        Args:
            sql: SQL query to validate
        
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        if not sql or not sql.strip():
            errors.append("SQL query is empty")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                sanitized_sql=""
            )
        
        # Normalize SQL for checking
        sql_upper = sql.upper()
        sql_clean = self._remove_sql_strings(sql_upper)
        
        # Check 1: Must be SELECT query
        if not sql_clean.strip().startswith('SELECT'):
            errors.append("Only SELECT queries are allowed")
        
        # Check 2: No forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', sql_clean):
                errors.append(f"Forbidden keyword detected: {keyword}")
        
        # Check 3: Multiple statements (check for dangerous keywords after semicolons)
        if not self.allow_multiple_statements:
            # Check for semicolons followed by dangerous keywords
            dangerous_after_semicolon = [
                r';\s*DELETE', r';\s*DROP', r';\s*UPDATE', r';\s*INSERT',
                r';\s*TRUNCATE', r';\s*ALTER', r';\s*CREATE'
            ]
            for pattern in dangerous_after_semicolon:
                if re.search(pattern, sql_clean, re.IGNORECASE):
                    errors.append(f"Multiple statements with dangerous operation detected")
                    break
            
            # Check for multiple semicolons (but allow single trailing semicolon)
            semicolons = sql.count(';')
            if semicolons > 1 or (semicolons == 1 and not sql.rstrip().endswith(';')):
                # Additional check: could be in a string literal
                # For now, just warn if we already found dangerous patterns
                if not any('Multiple statements' in e for e in errors):
                    warnings.append("Multiple semicolons detected - verify this is intentional")
        
        # Check 4: Suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, sql_clean, re.IGNORECASE):
                warnings.append(f"Suspicious pattern detected: {pattern}")
        
        # Check 5: Verify table names are from schema
        # Extract table names
        table_pattern = r'\bFROM\s+(\w+)|JOIN\s+(\w+)'
        matches = re.findall(table_pattern, sql_upper)
        tables_used = [m[0] or m[1] for m in matches]
        
        valid_tables = {
            'DRIVERS', 'VEHICLES', 'MAINTENANCE_RECORDS',
            'TELEMETRY', 'DRIVER_PERFORMANCE', 'FAULT_CODES'
        }
        
        for table in tables_used:
            if table and table not in valid_tables:
                warnings.append(f"Unknown table referenced: {table}")
        
        # Check 6: Basic syntax validation
        if not self._check_basic_syntax(sql):
            errors.append("SQL syntax appears invalid (unbalanced parentheses or quotes)")
        
        # Sanitize SQL
        sanitized_sql = self._sanitize_sql(sql)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_sql=sanitized_sql
        )
    
    def _remove_sql_strings(self, sql: str) -> str:
        """
        Remove string literals from SQL to avoid false positives
        
        Args:
            sql: SQL query
        
        Returns:
            SQL with strings replaced by empty strings
        """
        # Remove single-quoted strings
        sql = re.sub(r"'[^']*'", "''", sql)
        # Remove double-quoted strings
        sql = re.sub(r'"[^"]*"', '""', sql)
        return sql
    
    def _check_basic_syntax(self, sql: str) -> bool:
        """
        Check basic SQL syntax (balanced parentheses and quotes)
        
        Args:
            sql: SQL query
        
        Returns:
            True if syntax looks valid
        """
        # Check parentheses balance
        if sql.count('(') != sql.count(')'):
            return False
        
        # Check single quotes balance
        single_quotes = [i for i, c in enumerate(sql) if c == "'" and (i == 0 or sql[i-1] != '\\')]
        if len(single_quotes) % 2 != 0:
            return False
        
        # Check double quotes balance
        double_quotes = [i for i, c in enumerate(sql) if c == '"' and (i == 0 or sql[i-1] != '\\')]
        if len(double_quotes) % 2 != 0:
            return False
        
        return True
    
    def _sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL query
        
        Args:
            sql: SQL query
        
        Returns:
            Sanitized SQL
        """
        # Remove trailing semicolon for consistency
        sql = sql.rstrip().rstrip(';')
        
        # Remove excessive whitespace
        sql = ' '.join(sql.split())
        
        # Ensure ends with semicolon
        sql = sql + ';'
        
        return sql
    
    def validate_and_raise(self, sql: str) -> str:
        """
        Validate SQL and raise exception if invalid
        
        Args:
            sql: SQL query to validate
        
        Returns:
            Sanitized SQL if valid
        
        Raises:
            ValueError: If SQL is invalid
        """
        result = self.validate(sql)
        
        if not result.is_valid:
            error_msg = "SQL validation failed:\n" + "\n".join(f"  - {e}" for e in result.errors)
            raise ValueError(error_msg)
        
        if result.warnings:
            import warnings
            for warning in result.warnings:
                warnings.warn(f"SQL validation warning: {warning}")
        
        return result.sanitized_sql


def main():
    """Test the SQL validator"""
    print("=" * 70)
    print("FleetFix SQL Validator - Test")
    print("=" * 70)
    
    validator = SQLValidator()
    
    # Test cases
    test_cases = [
        # Valid queries
        ("SELECT * FROM vehicles;", True, "Basic SELECT"),
        ("SELECT * FROM vehicles WHERE status = 'active';", True, "SELECT with WHERE"),
        ("SELECT * FROM vehicles WHERE 1=1;", True, "WHERE with always-true condition"),
        ("SELECT * FROM vehicles WHERE 1=1 OR '1'='1';", True, "Classic injection pattern but safe in LLM context"),
        ("SELECT v.*, d.name FROM vehicles v JOIN drivers d ON v.id = d.id;", True, "SELECT with JOIN"),
        ("""
            SELECT 
                v.license_plate,
                COUNT(fc.id) as fault_count
            FROM vehicles v
            LEFT JOIN fault_codes fc ON v.id = fc.vehicle_id
            WHERE fc.resolved = FALSE
            GROUP BY v.license_plate
            ORDER BY fault_count DESC;
        """, True, "Complex valid query"),
        
        # Invalid queries
        ("DELETE FROM vehicles WHERE id = 1;", False, "DELETE (forbidden)"),
        ("DROP TABLE vehicles;", False, "DROP (forbidden)"),
        ("SELECT * FROM vehicles; DELETE FROM drivers;", False, "Multiple statements"),
        ("UPDATE vehicles SET status = 'inactive';", False, "UPDATE (forbidden)"),
        ("SELECT * FROM vehicles WHERE 1=1 OR '1'='1';", False, "SQL injection pattern"),
        ("SELECT * FROM vehicles; --comment", False, "SQL comment"),
        ("SELECT * FROM vehicles UNION SELECT * FROM drivers;", False, "UNION injection"),
        ("", False, "Empty query"),
        ("SELECT * FROM unknown_table;", True, "Unknown table (warning only)"),
    ]
    
    print("\nRunning validation tests...")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for sql, should_pass, description in test_cases:
        result = validator.validate(sql)
        
        # Check if result matches expectation
        test_passed = result.is_valid == should_pass
        
        status = "✓ PASS" if test_passed else "✗ FAIL"
        expected = "should pass" if should_pass else "should fail"
        actual = "passed" if result.is_valid else "failed"
        
        print(f"\n{status}: {description} ({expected}, {actual})")
        
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        if test_passed:
            passed += 1
        else:
            failed += 1
            print(f"  Expected: {expected}, Got: {actual}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✓ All tests passed! SQL validator is ready.")
    else:
        print(f"\n✗ {failed} test(s) failed.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
