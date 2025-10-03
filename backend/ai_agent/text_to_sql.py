"""
FleetFix Text-to-SQL Converter
Converts natural language queries to SQL using LLM
"""

import os
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# LLM API imports
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class SQLGenerationResult:
    """Result of SQL generation"""
    sql: str
    explanation: str
    confidence: float
    warnings: list
    error: Optional[str] = None


class TextToSQLConverter:
    """
    Converts natural language to SQL using LLM
    Supports both Anthropic Claude and OpenAI GPT-4
    """
    
    def __init__(
        self,
        schema_context: str,
        provider: str = "anthropic",
        model: Optional[str] = None
    ):
        """
        Initialize converter
        
        Args:
            schema_context: Database schema description from SchemaContextBuilder
            provider: "anthropic" or "openai"
            model: Specific model to use (optional, uses defaults)
        """
        self.schema_context = schema_context
        self.provider = provider.lower()
        
        # Set up API client
        if self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
            
        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4o"
            
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'anthropic' or 'openai'")
    
    def _build_prompt(self, user_query: str) -> str:
        """
        Build prompt for LLM
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a SQL expert for the FleetFix fleet management database.

{self.schema_context}

# Your Task

Convert the user's natural language query into a safe PostgreSQL SELECT query.

# Important Rules

1. ONLY generate SELECT queries - never DELETE, UPDATE, DROP, INSERT, or other modifications
2. Use proper PostgreSQL syntax
3. Use CURRENT_DATE for "today", "yesterday", etc.
4. Use table and column names exactly as shown in the schema
5. Include appropriate JOINs when querying multiple tables
6. Add WHERE clauses for filtering
7. Use ORDER BY when results should be sorted
8. Add LIMIT if the query implies "top N" or similar
9. Handle NULL values appropriately
10. Use aggregate functions (COUNT, AVG, SUM) when appropriate

# User Query

"{user_query}"

# Your Response Format

Provide your response in this exact format:

SQL:
```sql
[Your SQL query here]
```

EXPLANATION:
[Brief explanation of what the query does and why you structured it this way]

CONFIDENCE:
[A number from 0.0 to 1.0 indicating your confidence in this query]

WARNINGS:
[Any warnings or caveats about this query, or "None" if no warnings]

# Examples

User Query: "Show me vehicles overdue for maintenance"
SQL:
```sql
SELECT id, make, model, license_plate, next_service_due,
       CURRENT_DATE - next_service_due as days_overdue
FROM vehicles
WHERE next_service_due < CURRENT_DATE
ORDER BY days_overdue DESC;
```

EXPLANATION:
This query finds vehicles where the next_service_due date has passed (is less than today's date). It calculates how many days overdue each vehicle is and sorts with the most overdue first.

CONFIDENCE:
0.95

WARNINGS:
None

---

User Query: "Which drivers had poor performance yesterday?"
SQL:
```sql
SELECT d.name, dp.score, dp.harsh_braking_events, dp.speeding_events
FROM drivers d
JOIN driver_performance dp ON d.id = dp.driver_id
WHERE dp.date = CURRENT_DATE - INTERVAL '1 day'
  AND dp.score < 70
ORDER BY dp.score ASC;
```

EXPLANATION:
This query joins drivers with their performance records from yesterday (CURRENT_DATE - 1 day), filters for scores below 70 (poor performance), and sorts by score with worst performers first.

CONFIDENCE:
0.90

WARNINGS:
The threshold of 70 is arbitrary - adjust based on your definition of "poor performance".

---

Now generate the SQL for the user's query above."""

        return prompt
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0,  # Deterministic for SQL generation
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return message.content[0].text
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": "You are a SQL expert for PostgreSQL databases."
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0,  # Deterministic for SQL generation
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> Tuple[str, str, float, list]:
        """
        Parse LLM response to extract SQL, explanation, confidence, warnings
        
        Returns:
            (sql, explanation, confidence, warnings)
        """
        sql = ""
        explanation = ""
        confidence = 0.8  # Default
        warnings = []
        
        lines = response.split('\n')
        current_section = None
        sql_lines = []
        explanation_lines = []
        warning_lines = []
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Detect section headers
            if line_upper.startswith('SQL:'):
                current_section = 'sql'
                continue
            elif line_upper.startswith('EXPLANATION:'):
                current_section = 'explanation'
                continue
            elif line_upper.startswith('CONFIDENCE:'):
                current_section = 'confidence'
                continue
            elif line_upper.startswith('WARNINGS:'):
                current_section = 'warnings'
                continue
            
            # Extract content based on current section
            if current_section == 'sql':
                # Skip markdown code fence
                if line.strip() in ['```sql', '```']:
                    continue
                if line.strip():
                    sql_lines.append(line)
            
            elif current_section == 'explanation':
                if line.strip() and not line_upper.startswith('CONFIDENCE:'):
                    explanation_lines.append(line.strip())
            
            elif current_section == 'confidence':
                # Extract number
                try:
                    # Handle formats like "0.95" or "95%" or "Confidence: 0.95"
                    import re
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        num = float(match.group(1))
                        confidence = num if num <= 1.0 else num / 100.0
                except:
                    pass
            
            elif current_section == 'warnings':
                if line.strip() and line.strip().lower() != 'none':
                    warning_lines.append(line.strip())
        
        sql = '\n'.join(sql_lines).strip()
        explanation = ' '.join(explanation_lines).strip()
        warnings = [w for w in warning_lines if w]
        
        return sql, explanation, confidence, warnings
    
    def convert(self, user_query: str) -> SQLGenerationResult:
        """
        Convert natural language to SQL
        
        Args:
            user_query: Natural language query
        
        Returns:
            SQLGenerationResult with sql, explanation, confidence, warnings
        """
        try:
            # Build prompt
            prompt = self._build_prompt(user_query)
            
            # Call LLM
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)
            
            # Parse response
            sql, explanation, confidence, warnings = self._parse_response(response)
            
            if not sql:
                return SQLGenerationResult(
                    sql="",
                    explanation="",
                    confidence=0.0,
                    warnings=[],
                    error="Failed to extract SQL from LLM response"
                )
            
            return SQLGenerationResult(
                sql=sql,
                explanation=explanation,
                confidence=confidence,
                warnings=warnings
            )
        
        except Exception as e:
            return SQLGenerationResult(
                sql="",
                explanation="",
                confidence=0.0,
                warnings=[],
                error=f"Error generating SQL: {str(e)}"
            )
    
    def convert_with_conversation_history(
        self,
        user_query: str,
        conversation_history: list
    ) -> SQLGenerationResult:
        """
        Convert query with conversation context
        Useful for follow-up questions like "show me more details"
        
        Args:
            user_query: Current query
            conversation_history: List of (user_query, sql_result) tuples
        
        Returns:
            SQLGenerationResult
        """
        # Add conversation history to prompt
        history_text = "\n# Previous Queries\n"
        for i, (prev_query, prev_sql) in enumerate(conversation_history[-3:], 1):
            history_text += f"\nQuery {i}: {prev_query}\nSQL: {prev_sql}\n"
        
        # Temporarily append to schema context
        original_context = self.schema_context
        self.schema_context = self.schema_context + "\n" + history_text
        
        try:
            result = self.convert(user_query)
            return result
        finally:
            # Restore original context
            self.schema_context = original_context


def main():
    """Test the text-to-SQL converter"""
    print("=" * 70)
    print("FleetFix Text-to-SQL Converter - Test")
    print("=" * 70)
    
    # Load schema context
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_agent.schema_context import SchemaContextBuilder
    
    builder = SchemaContextBuilder()
    schema_context = builder.build_schema_context()
    
    # Determine which provider to use
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n✗ Error: No API key found!")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file")
        return
    
    print(f"\nUsing provider: {provider}")
    print(f"Schema context loaded: {len(schema_context)} characters")
    
    # Initialize converter
    converter = TextToSQLConverter(schema_context, provider=provider)
    
    # Test queries
    test_queries = [
        "Show me vehicles that are overdue for maintenance",
        "Which drivers had the worst performance yesterday?",
        "What's our fleet's average fuel efficiency over the last 7 days?",
        "List all critical unresolved fault codes",
        "Show me vehicles that haven't been serviced in over 6 months"
    ]
    
    print("\n" + "=" * 70)
    print("Testing Queries")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 70)
        
        result = converter.convert(query)
        
        if result.error:
            print(f"✗ Error: {result.error}")
            continue
        
        print(f"✓ SQL Generated (confidence: {result.confidence:.2f})")
        print(f"\nSQL:\n{result.sql}")
        print(f"\nExplanation:\n{result.explanation}")
        
        if result.warnings:
            print(f"\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
    
    print("\n" + "=" * 70)
    print("Text-to-SQL converter ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()