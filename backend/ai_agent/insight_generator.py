"""
FleetFix Insight Generator
Analyzes query results and generates intelligent insights
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.query_executor import QueryResult

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
class Insight:
    """Single insight about query results"""
    type: str  # "observation", "pattern", "anomaly", "recommendation"
    severity: str  # "info", "warning", "critical"
    message: str
    confidence: float  # 0.0 to 1.0


@dataclass
class InsightResult:
    """Complete insight analysis"""
    summary: str
    insights: List[Insight]
    key_findings: List[str]
    recommendations: List[str]
    error: Optional[str] = None


class InsightGenerator:
    """
    Analyzes query results using LLM to generate insights
    """
    
    def __init__(self, provider: str = "anthropic", model: Optional[str] = None):
        """
        Initialize insight generator
        
        Args:
            provider: "anthropic" or "openai"
            model: Specific model to use (optional)
        """
        self.provider = provider.lower()
        
        # Set up API client
        if self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed")
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
            
        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4o"
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate_insights(
        self,
        user_query: str,
        sql: str,
        result: QueryResult
    ) -> InsightResult:
        """
        Generate insights about query results
        
        Args:
            user_query: Original natural language query
            sql: SQL query that was executed
            result: Query execution result
        
        Returns:
            InsightResult with analysis
        """
        if not result.success:
            return InsightResult(
                summary="Query execution failed",
                insights=[],
                key_findings=[],
                recommendations=[],
                error=result.error
            )
        
        if result.row_count == 0:
            return self._generate_empty_result_insights(user_query, sql)
        
        try:
            # Build prompt
            prompt = self._build_insight_prompt(user_query, sql, result)
            
            # Call LLM
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)
            
            # Parse response
            return self._parse_insight_response(response)
        
        except Exception as e:
            return InsightResult(
                summary=f"Found {result.row_count} results",
                insights=[],
                key_findings=[],
                recommendations=[],
                error=f"Error generating insights: {str(e)}"
            )
    
    def _build_insight_prompt(
        self,
        user_query: str,
        sql: str,
        result: QueryResult
    ) -> str:
        """Build prompt for insight generation"""
        
        # Prepare result summary
        result_preview = result.rows[:10]  # First 10 rows
        
        prompt = f"""You are analyzing query results for FleetFix, a fleet management system.

# User's Question
"{user_query}"

# SQL Query
```sql
{sql}
```

# Query Results
- Total rows: {result.row_count}
- Columns: {', '.join(result.columns)}
- Execution time: {result.execution_time_ms}ms

# Sample Data (first 10 rows)
```json
{result_preview}
```

# Your Task

Analyze these results and provide insights that help the user understand what the data means and what actions they should take.

# Response Format

Provide your analysis in this exact format:

SUMMARY:
[One sentence summary of what the data shows]

KEY FINDINGS:
1. [First key finding]
2. [Second key finding]
3. [Third key finding]

INSIGHTS:
[TYPE: observation|pattern|anomaly|recommendation]
[SEVERITY: info|warning|critical]
[CONFIDENCE: 0.0-1.0]
[MESSAGE: The insight message]

[Repeat for each insight - provide 2-5 insights total]

RECOMMENDATIONS:
1. [First actionable recommendation]
2. [Second actionable recommendation]
3. [Third actionable recommendation]

# Guidelines

- Be specific and actionable
- Reference actual numbers from the data
- Identify patterns, trends, or anomalies
- Provide context about what's normal vs abnormal
- Focus on business impact (cost, safety, efficiency)
- Keep insights concise and clear
- If data shows problems, explain severity and urgency

# Example

SUMMARY:
3 vehicles are overdue for maintenance, with one critically overdue by 15 days.

KEY FINDINGS:
1. Vehicle KC-7392 (Ford Transit) is 15 days overdue - highest risk
2. Two vehicles overdue by 5-7 days
3. All overdue vehicles are cargo vans with high mileage (40k+ miles)

INSIGHTS:
[TYPE: anomaly]
[SEVERITY: critical]
[CONFIDENCE: 0.95]
[MESSAGE: Vehicle KC-7392 is critically overdue (15 days past due date). Risk of breakdown is 3x higher than normal, potentially causing delivery delays and repair costs of $500-2000.]

[TYPE: pattern]
[SEVERITY: warning]
[CONFIDENCE: 0.85]
[MESSAGE: All overdue vehicles are cargo vans, suggesting these vehicles may need more frequent maintenance schedules due to higher usage patterns.]

[TYPE: recommendation]
[SEVERITY: warning]
[CONFIDENCE: 0.90]
[MESSAGE: Schedule immediate maintenance for KC-7392 to prevent breakdown. Consider increasing maintenance frequency for cargo vans from 5000 to 4000 mile intervals.]

RECOMMENDATIONS:
1. Schedule KC-7392 for immediate maintenance (within 24 hours)
2. Contact drivers of other 2 overdue vehicles to schedule within 3 days
3. Review cargo van maintenance intervals - consider reducing from 5000 to 4000 miles

Now analyze the actual query results above."""

        return prompt
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,  # Slightly creative for insights
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
                "content": "You are a fleet management data analyst providing insights."
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _parse_insight_response(self, response: str) -> InsightResult:
        """Parse LLM response into InsightResult"""
        lines = response.split('\n')
        
        summary = ""
        key_findings = []
        insights = []
        recommendations = []
        
        current_section = None
        current_insight = {}
        
        for line in lines:
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Section headers
            if line_upper.startswith('SUMMARY:'):
                current_section = 'summary'
                continue
            elif line_upper.startswith('KEY FINDINGS:'):
                current_section = 'key_findings'
                continue
            elif line_upper.startswith('INSIGHTS:'):
                current_section = 'insights'
                continue
            elif line_upper.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
                continue
            
            # Parse content
            if current_section == 'summary' and line_stripped:
                summary = line_stripped
            
            elif current_section == 'key_findings' and line_stripped:
                # Remove numbering
                finding = line_stripped.lstrip('0123456789. ')
                if finding:
                    key_findings.append(finding)
            
            elif current_section == 'insights':
                if line_upper.startswith('[TYPE:'):
                    # Save previous insight if exists
                    if current_insight:
                        insights.append(Insight(**current_insight))
                        current_insight = {}
                    
                    # Start new insight
                    insight_type = line_stripped[6:].strip(']').strip()
                    current_insight['type'] = insight_type
                
                elif line_upper.startswith('[SEVERITY:'):
                    severity = line_stripped[10:].strip(']').strip()
                    current_insight['severity'] = severity
                
                elif line_upper.startswith('[CONFIDENCE:'):
                    try:
                        confidence = float(line_stripped[12:].strip(']').strip())
                        current_insight['confidence'] = confidence
                    except:
                        current_insight['confidence'] = 0.7
                
                elif line_upper.startswith('[MESSAGE:'):
                    message = line_stripped[9:].strip(']').strip()
                    current_insight['message'] = message
            
            elif current_section == 'recommendations' and line_stripped:
                # Remove numbering
                rec = line_stripped.lstrip('0123456789. ')
                if rec:
                    recommendations.append(rec)
        
        # Add last insight
        if current_insight:
            insights.append(Insight(**current_insight))
        
        return InsightResult(
            summary=summary or f"Found {len(insights)} insights",
            insights=insights,
            key_findings=key_findings,
            recommendations=recommendations
        )
    
    def _generate_empty_result_insights(
        self,
        user_query: str,
        sql: str
    ) -> InsightResult:
        """Generate insights for empty result sets"""
        return InsightResult(
            summary="No results found for this query",
            insights=[
                Insight(
                    type="observation",
                    severity="info",
                    message="The query returned no results. This could mean the data doesn't exist, or the filters are too restrictive.",
                    confidence=0.9
                )
            ],
            key_findings=[
                "Query executed successfully but returned 0 rows",
                "No data matches the specified criteria"
            ],
            recommendations=[
                "Check if the filters are correct",
                "Try broadening the search criteria",
                "Verify the data exists in the database"
            ]
        )


def main():
    """Test insight generator"""
    print("=" * 70)
    print("FleetFix Insight Generator - Test")
    print("=" * 70)
    
    # Check for API key
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n✗ Error: No API key found!")
        return
    
    print(f"\nUsing provider: {provider}")
    
    generator = InsightGenerator(provider=provider)
    
    # Mock query result for testing
    from ai_agent.query_executor import QueryResult
    
    mock_result = QueryResult(
        success=True,
        rows=[
            {"license_plate": "KC-7392", "make": "Ford", "model": "Transit", "days_overdue": 15},
            {"license_plate": "KC-1847", "make": "Ram", "model": "ProMaster", "days_overdue": 7},
            {"license_plate": "KC-9284", "make": "Mercedes", "model": "Sprinter", "days_overdue": 5},
        ],
        columns=["license_plate", "make", "model", "days_overdue"],
        row_count=3,
        execution_time_ms=45.2
    )
    
    user_query = "Show me vehicles overdue for maintenance"
    sql = "SELECT license_plate, make, model, CURRENT_DATE - next_service_due as days_overdue FROM vehicles WHERE next_service_due < CURRENT_DATE ORDER BY days_overdue DESC;"
    
    print("\nGenerating insights...")
    print("-" * 70)
    
    insights = generator.generate_insights(user_query, sql, mock_result)
    
    if insights.error:
        print(f"✗ Error: {insights.error}")
        return
    
    print(f"\n✓ Insights generated successfully\n")
    
    print("SUMMARY:")
    print(f"  {insights.summary}\n")
    
    print("KEY FINDINGS:")
    for i, finding in enumerate(insights.key_findings, 1):
        print(f"  {i}. {finding}")
    
    print("\nINSIGHTS:")
    for insight in insights.insights:
        severity_symbol = {"info": "ℹ", "warning": "⚠", "critical": "✗"}
        symbol = severity_symbol.get(insight.severity, "•")
        print(f"\n  {symbol} [{insight.type.upper()}] (confidence: {insight.confidence:.2f})")
        print(f"     {insight.message}")
    
    print("\nRECOMMENDATIONS:")
    for i, rec in enumerate(insights.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 70)
    print("Insight generator ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()
