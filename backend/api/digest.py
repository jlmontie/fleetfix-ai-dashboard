"""
Daily Digest API Endpoint

Generates adaptive daily insights by analyzing recent fleet changes
and identifying the most important issues requiring attention.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.sql import text

# Import from existing modules
try:
    from database.config import get_db_connection, db_config
    from visualizer.plotly_generator import PlotlyGenerator
    from ai_agent.insight_generator import InsightGenerator
except ModuleNotFoundError:
    from backend.database.config import get_db_connection, db_config
    from backend.visualizer.plotly_generator import PlotlyGenerator
    from backend.ai_agent.insight_generator import InsightGenerator


class ChangeDetection:
    """Detects significant changes in fleet data over last 24 hours"""
    
    def __init__(self):
        self.changes = []
    
    def detect_all_changes(self) -> List[Dict[str, Any]]:
        """Run all change detection queries and return significant changes"""
        self.changes = []
        
        # Run all detection methods
        self._detect_new_fault_codes()
        self._detect_overdue_maintenance()
        self._detect_driver_performance_drops()
        self._detect_fuel_efficiency_changes()
        self._detect_high_downtime()
        
        return self.changes
    
    def _detect_new_fault_codes(self):
        """Detect new fault codes in last 24 hours"""
        query = """
        SELECT 
            COUNT(*) as new_fault_codes,
            COUNT(DISTINCT vehicle_id) as affected_vehicles,
            COUNT(CASE WHEN severity = 'HIGH' THEN 1 END) as critical_codes,
            array_agg(DISTINCT code) as fault_codes
        FROM fault_codes
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
          AND resolved = false
        """
        
        with db_config.session_scope() as session:
            result = session.execute(text(query)).fetchone()
            
            if result and result.new_fault_codes > 0:
                self.changes.append({
                    'type': 'fault_codes',
                    'priority': 'high' if result.critical_codes > 0 else 'medium',
                    'count': result.new_fault_codes,
                    'affected_vehicles': result.affected_vehicles,
                    'critical': result.critical_codes,
                    'codes': result.fault_codes[:5] if result.fault_codes else [],
                    'title': f"{result.new_fault_codes} New Fault Codes Detected",
                    'data': {
                        'new_fault_codes': result.new_fault_codes,
                        'affected_vehicles': result.affected_vehicles,
                        'critical_codes': result.critical_codes
                    }
                })
    
    def _detect_overdue_maintenance(self):
        """Detect vehicles overdue for maintenance"""
        query = """
        SELECT 
            COUNT(DISTINCT v.id) as overdue_count,
            array_agg(DISTINCT v.make || ' ' || v.model) as vehicle_types,
            MAX(CURRENT_DATE - v.next_service_due) as days_overdue,
            array_agg(v.id) as vehicle_ids
        FROM vehicles v
        JOIN maintenance_records m ON v.id = m.vehicle_id
        WHERE v.next_service_due < CURRENT_DATE
          AND v.next_service_due >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY v.id
        HAVING COUNT(*) > 0
        """
        
        with db_config.session_scope() as session:
            result = session.execute(text(query)).fetchone()
            
            if result and result.overdue_count > 0:
                priority = 'high' if result.days_overdue > 7 else 'medium'
                
                self.changes.append({
                    'type': 'maintenance_overdue',
                    'priority': priority,
                    'count': result.overdue_count,
                    'days_overdue': result.days_overdue,
                    'vehicle_types': result.vehicle_types[:3] if result.vehicle_types else [],
                    'vehicle_ids': result.vehicle_ids,
                    'title': f"{result.overdue_count} Vehicles Overdue for Maintenance",
                    'data': {
                        'overdue_count': result.overdue_count,
                        'max_days_overdue': result.days_overdue
                    }
                })
    
    def _detect_driver_performance_drops(self):
        """Detect drivers with significant performance drops"""
        query = """
        WITH recent_scores AS (
            SELECT 
                driver_id,
                AVG(CASE WHEN date >= CURRENT_DATE - INTERVAL '3 days' THEN score END) as recent_avg,
                AVG(CASE WHEN date >= CURRENT_DATE - INTERVAL '10 days' 
                          AND date < CURRENT_DATE - INTERVAL '3 days' THEN score END) as previous_avg,
                COUNT(*) as record_count
            FROM driver_performance
            WHERE date >= CURRENT_DATE - INTERVAL '10 days'
            GROUP BY driver_id
            HAVING COUNT(*) >= 5
        )
        SELECT 
            COUNT(*) as affected_drivers,
            AVG(previous_avg - recent_avg) as avg_drop,
            array_agg(driver_id) as driver_ids
        FROM recent_scores
        WHERE recent_avg < previous_avg - 10
        """
        
        with db_config.session_scope() as session:
            result = session.execute(text(query)).fetchone()
            
            if result and result.affected_drivers > 0:
                self.changes.append({
                    'type': 'driver_performance',
                    'priority': 'medium',
                    'count': result.affected_drivers,
                    'avg_drop': round(result.avg_drop, 1) if result.avg_drop else 0,
                    'driver_ids': result.driver_ids,
                    'title': f"{result.affected_drivers} Drivers Show Performance Decline",
                    'data': {
                        'affected_drivers': result.affected_drivers,
                        'avg_score_drop': round(result.avg_drop, 1) if result.avg_drop else 0
                    }
                })
    
    def _detect_fuel_efficiency_changes(self):
        """Detect significant fuel efficiency changes"""
        query = """
        WITH efficiency_data AS (
            SELECT 
                vehicle_id,
                AVG(CASE WHEN timestamp >= NOW() - INTERVAL '3 days' THEN fuel_level END) as recent_fuel,
                AVG(CASE WHEN timestamp >= NOW() - INTERVAL '10 days' 
                          AND timestamp < NOW() - INTERVAL '3 days' THEN fuel_level END) as previous_fuel
            FROM telemetry
            WHERE timestamp >= NOW() - INTERVAL '10 days'
            GROUP BY vehicle_id
        )
        SELECT 
            COUNT(*) as affected_vehicles,
            AVG((previous_fuel - recent_fuel) / previous_fuel * 100) as avg_change_pct
        FROM efficiency_data
        WHERE previous_fuel > 0 
          AND ABS((previous_fuel - recent_fuel) / previous_fuel * 100) > 5
        """
        
        with db_config.session_scope() as session:
            result = session.execute(text(query)).fetchone()
            
            if result and result.affected_vehicles > 0:
                priority = 'medium' if abs(result.avg_change_pct or 0) > 10 else 'low'
                
                self.changes.append({
                    'type': 'fuel_efficiency',
                    'priority': priority,
                    'count': result.affected_vehicles,
                    'change_pct': round(result.avg_change_pct, 1) if result.avg_change_pct else 0,
                    'title': f"Fuel Efficiency Changed in {result.affected_vehicles} Vehicles",
                    'data': {
                        'affected_vehicles': result.affected_vehicles,
                        'avg_change_pct': round(result.avg_change_pct, 1) if result.avg_change_pct else 0
                    }
                })
    
    def _detect_high_downtime(self):
        """Detect vehicles with high downtime today"""
        query = """
        SELECT 
            COUNT(DISTINCT vehicle_id) as vehicles_with_downtime,
            SUM(EXTRACT(EPOCH FROM (NOW() - timestamp)) / 3600) as total_hours
        FROM fault_codes
        WHERE timestamp >= CURRENT_DATE
          AND severity IN ('HIGH', 'CRITICAL')
          AND resolved = false
        HAVING SUM(EXTRACT(EPOCH FROM (NOW() - timestamp)) / 3600) > 4
        """
        
        with db_config.session_scope() as session:
            result = session.execute(text(query)).fetchone()
            
            if result and result.vehicles_with_downtime > 0:
                self.changes.append({
                    'type': 'high_downtime',
                    'priority': 'high',
                    'count': result.vehicles_with_downtime,
                    'hours': round(result.total_hours, 1) if result.total_hours else 0,
                    'title': f"{result.vehicles_with_downtime} Vehicles with High Downtime Today",
                    'data': {
                        'vehicles_with_downtime': result.vehicles_with_downtime,
                        'total_hours': round(result.total_hours, 1) if result.total_hours else 0
                    }
                })


class PriorityScorer:
    """Assigns priority scores to changes"""
    
    @staticmethod
    def score_changes(changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign scores and sort by priority"""
        for change in changes:
            score = PriorityScorer._calculate_score(change)
            change['score'] = score
        
        # Sort by score (descending) and return top changes
        changes.sort(key=lambda x: x['score'], reverse=True)
        return changes[:5]  # Top 5 changes
    
    @staticmethod
    def _calculate_score(change: Dict[str, Any]) -> int:
        """Calculate priority score (higher = more important)"""
        score = 0
        
        # Base score by type
        type_scores = {
            'fault_codes': 40,
            'maintenance_overdue': 50,
            'driver_performance': 30,
            'fuel_efficiency': 25,
            'high_downtime': 60,
        }
        score += type_scores.get(change['type'], 20)
        
        # Priority multiplier
        priority_multipliers = {
            'high': 2.0,
            'medium': 1.5,
            'low': 1.0,
        }
        score *= priority_multipliers.get(change['priority'], 1.0)
        
        # Count factor (more affected entities = higher priority)
        count = change.get('count', 1)
        score += min(count * 2, 20)  # Cap at +20
        
        # Recency factor (already recent, but can add time-based adjustments)
        
        return int(score)


class DigestInsightGenerator:
    """Generates insights using LLM based on detected changes"""
    
    def __init__(self):
        self.insight_generator = InsightGenerator()
        self.plotly_generator = PlotlyGenerator()
    
    def generate_insights(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights for top changes"""
        insights = []
        
        for change in changes[:3]:  # Top 3 changes
            insight = self._generate_single_insight(change)
            if insight:
                insights.append(insight)
        
        return insights
    
    def _generate_single_insight(self, change: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a single insight with visualization"""
        # Create prompt for LLM
        prompt = f"""
        Analyze this fleet management issue and provide actionable insights:
        
        Issue Type: {change['type']}
        Priority: {change['priority']}
        Title: {change['title']}
        Data: {change.get('data', {})}
        
        Provide:
        1. A 2-3 sentence description explaining the issue and why it matters
        2. A specific, actionable recommendation (1-2 sentences)
        3. Estimated cost if applicable (e.g., "$1,200-1,800")
        
        Format your response as JSON:
        {{
            "description": "...",
            "recommendation": "...",
            "estimated_cost": "..." (optional)
        }}
        """
        
        try:
            # Get AI-generated insight
            ai_response = self.insight_generator.generate_insight(
                query_results=[change.get('data', {})],
                context=f"Fleet change detection: {change['title']}"
            )
            
            # Parse response (simplified - in production would use structured output)
            import json
            try:
                parsed = json.loads(ai_response)
                description = parsed.get('description', change['title'])
                recommendation = parsed.get('recommendation', 'Review and take appropriate action.')
                estimated_cost = parsed.get('estimated_cost')
            except:
                # Fallback to simple extraction
                description = change['title']
                recommendation = f"Review {change['count']} affected items and take appropriate action."
                estimated_cost = None
            
            # Generate visualization
            chart = self._generate_chart(change)
            
            return {
                'priority': change['priority'],
                'title': change['title'],
                'description': description,
                'recommendation': recommendation,
                'chart': chart,
                'affected_vehicles': change.get('vehicle_ids', []),
                'estimated_cost': estimated_cost,
            }
        except Exception as e:
            print(f"Error generating insight: {e}")
            # Return basic insight without AI enhancement
            return {
                'priority': change['priority'],
                'title': change['title'],
                'description': f"Detected {change['count']} instances requiring attention.",
                'recommendation': "Review and take appropriate action.",
                'chart': self._generate_chart(change),
            }
    
    def _generate_chart(self, change: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate appropriate visualization for the change"""
        try:
            # Create simple bar chart for the change
            data = change.get('data', {})
            
            if not data:
                return None
            
            # Convert data to format for bar chart
            labels = list(data.keys())
            values = list(data.values())
            
            chart_data = [{'label': labels[i], 'value': values[i]} for i in range(len(labels))]
            
            # Generate plotly chart
            chart_config = {
                'type': 'bar',
                'title': change['title'],
                'x_column': 'label',
                'y_columns': ['value']
            }
            
            return self.plotly_generator.generate_chart(chart_data, chart_config)
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None


# Cache for daily digest (simple in-memory cache)
_digest_cache = {
    'digest': None,
    'generated_at': None,
}


def get_daily_digest(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get daily digest with adaptive insights
    
    Args:
        force_refresh: Force regeneration even if cache is valid
        
    Returns:
        Dictionary with generated_at timestamp and list of insights
    """
    # Check cache (valid for 24 hours)
    if not force_refresh and _digest_cache['generated_at']:
        cache_age = datetime.now() - _digest_cache['generated_at']
        if cache_age < timedelta(hours=24):
            return _digest_cache['digest']
    
    # Generate new digest
    print("Generating new daily digest...")
    
    # Step 1: Detect changes
    detector = ChangeDetection()
    changes = detector.detect_all_changes()
    
    if not changes:
        # No significant changes
        digest = {
            'generated_at': datetime.now().isoformat(),
            'insights': [],
        }
    else:
        # Step 2: Score and prioritize changes
        scorer = PriorityScorer()
        top_changes = scorer.score_changes(changes)
        
        # Step 3: Generate insights
        generator = DigestInsightGenerator()
        insights = generator.generate_insights(top_changes)
        
        digest = {
            'generated_at': datetime.now().isoformat(),
            'insights': insights,
        }
    
    # Update cache
    _digest_cache['digest'] = digest
    _digest_cache['generated_at'] = datetime.now()
    
    return digest

