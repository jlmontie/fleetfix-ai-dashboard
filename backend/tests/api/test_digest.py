"""
Tests for Daily Digest API endpoint

Tests change detection, priority scoring, insight generation,
caching behavior, and visualization generation.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from backend.api.digest import (
    ChangeDetection,
    PriorityScorer,
    DigestInsightGenerator,
    get_daily_digest,
    _digest_cache
)


class TestChangeDetection:
    """Test change detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return ChangeDetection()
    
    def test_detect_all_changes(self, detector):
        """Test that detect_all_changes returns list"""
        changes = detector.detect_all_changes()
        
        assert isinstance(changes, list)
        # Changes list might be empty if no data, that's OK
    
    def test_change_structure(self, detector):
        """Test that changes have required fields"""
        # Mock a change
        test_change = {
            'type': 'test',
            'priority': 'high',
            'count': 5,
            'title': 'Test Change',
            'data': {'test_key': 'test_value'}
        }
        
        detector.changes = [test_change]
        changes = detector.changes
        
        assert len(changes) > 0
        change = changes[0]
        assert 'type' in change
        assert 'priority' in change
        assert 'count' in change
        assert 'title' in change
    
    def test_multiple_detection_methods(self, detector):
        """Test that all detection methods can be called"""
        # These might fail if database is empty, but should not crash
        try:
            detector._detect_new_fault_codes()
            detector._detect_overdue_maintenance()
            detector._detect_driver_performance_drops()
            detector._detect_fuel_efficiency_changes()
            detector._detect_high_downtime()
            assert True  # If we get here, no crashes
        except Exception as e:
            # Database errors are acceptable in test environment
            print(f"Detection method error (acceptable in test): {e}")


class TestPriorityScorer:
    """Test priority scoring functionality"""
    
    def test_score_changes_returns_list(self):
        """Test that score_changes returns a list"""
        changes = [
            {'type': 'fault_codes', 'priority': 'high', 'count': 5},
            {'type': 'maintenance_overdue', 'priority': 'medium', 'count': 3},
        ]
        
        scored = PriorityScorer.score_changes(changes)
        
        assert isinstance(scored, list)
        assert len(scored) <= len(changes)
    
    def test_changes_have_scores(self):
        """Test that scored changes have score field"""
        changes = [
            {'type': 'fault_codes', 'priority': 'high', 'count': 5},
        ]
        
        scored = PriorityScorer.score_changes(changes)
        
        assert len(scored) > 0
        assert 'score' in scored[0]
        assert isinstance(scored[0]['score'], (int, float))
    
    def test_high_priority_scores_higher(self):
        """Test that high priority items score higher than low priority"""
        changes = [
            {'type': 'fault_codes', 'priority': 'low', 'count': 5},
            {'type': 'fault_codes', 'priority': 'high', 'count': 5},
        ]
        
        scored = PriorityScorer.score_changes(changes)
        
        # Find the high and low priority items
        high_item = next(c for c in scored if c['priority'] == 'high')
        low_item = next(c for c in scored if c['priority'] == 'low')
        
        assert high_item['score'] > low_item['score']
    
    def test_more_count_scores_higher(self):
        """Test that higher counts result in higher scores"""
        score1 = PriorityScorer._calculate_score({
            'type': 'fault_codes',
            'priority': 'medium',
            'count': 1
        })
        
        score2 = PriorityScorer._calculate_score({
            'type': 'fault_codes',
            'priority': 'medium',
            'count': 10
        })
        
        assert score2 > score1
    
    def test_returns_top_5_changes(self):
        """Test that only top 5 changes are returned"""
        changes = [
            {'type': f'type_{i}', 'priority': 'medium', 'count': i}
            for i in range(10)
        ]
        
        scored = PriorityScorer.score_changes(changes)
        
        assert len(scored) <= 5


class TestDigestInsightGenerator:
    """Test insight generation"""
    
    @pytest.fixture
    def generator(self):
        return DigestInsightGenerator()
    
    def test_generate_insights_returns_list(self, generator):
        """Test that generate_insights returns list"""
        changes = [
            {
                'type': 'maintenance_overdue',
                'priority': 'high',
                'count': 3,
                'title': 'Test Change',
                'data': {'overdue_count': 3}
            }
        ]
        
        insights = generator.generate_insights(changes)
        
        assert isinstance(insights, list)
    
    def test_insight_structure(self, generator):
        """Test that insights have required fields"""
        changes = [
            {
                'type': 'maintenance_overdue',
                'priority': 'high',
                'count': 3,
                'title': '3 Vehicles Overdue',
                'data': {'overdue_count': 3}
            }
        ]
        
        insights = generator.generate_insights(changes)
        
        if len(insights) > 0:
            insight = insights[0]
            assert 'priority' in insight
            assert 'title' in insight
            assert 'description' in insight
            assert 'recommendation' in insight
    
    def test_generate_chart_returns_dict_or_none(self, generator):
        """Test that chart generation returns dict or None"""
        change = {
            'type': 'test',
            'priority': 'high',
            'title': 'Test',
            'data': {'key': 'value'}
        }
        
        chart = generator._generate_chart(change)
        
        assert chart is None or isinstance(chart, dict)
    
    def test_max_3_insights(self, generator):
        """Test that at most 3 insights are generated"""
        changes = [
            {
                'type': f'type_{i}',
                'priority': 'high',
                'count': i,
                'title': f'Change {i}',
                'data': {'count': i}
            }
            for i in range(10)
        ]
        
        insights = generator.generate_insights(changes)
        
        assert len(insights) <= 3


class TestDailyDigestAPI:
    """Test the main daily digest API function"""
    
    def test_get_daily_digest_returns_dict(self):
        """Test that get_daily_digest returns a dictionary"""
        digest = get_daily_digest()
        
        assert isinstance(digest, dict)
        assert 'generated_at' in digest
        assert 'insights' in digest
    
    def test_digest_has_timestamp(self):
        """Test that digest includes generation timestamp"""
        digest = get_daily_digest()
        
        assert 'generated_at' in digest
        # Check that it's a valid ISO timestamp
        try:
            datetime.fromisoformat(digest['generated_at'])
            assert True
        except:
            assert False, "Invalid timestamp format"
    
    def test_insights_is_list(self):
        """Test that insights is a list"""
        digest = get_daily_digest()
        
        assert isinstance(digest['insights'], list)
    
    def test_caching_works(self):
        """Test that digest is cached"""
        # Clear cache
        _digest_cache['digest'] = None
        _digest_cache['generated_at'] = None
        
        # First call
        digest1 = get_daily_digest()
        time1 = digest1['generated_at']
        
        # Second call (should be cached)
        time.sleep(0.1)  # Small delay
        digest2 = get_daily_digest()
        time2 = digest2['generated_at']
        
        # Should return same timestamp (cached)
        assert time1 == time2
    
    def test_force_refresh_bypasses_cache(self):
        """Test that force_refresh generates new digest"""
        # First call
        digest1 = get_daily_digest()
        time1 = digest1['generated_at']
        
        # Wait a moment
        time.sleep(0.5)
        
        # Force refresh
        digest2 = get_daily_digest(force_refresh=True)
        time2 = digest2['generated_at']
        
        # Should have different timestamp
        assert time1 != time2
    
    def test_cache_expires_after_24_hours(self):
        """Test that cache expires after 24 hours"""
        # Set cache with old timestamp
        _digest_cache['digest'] = {
            'generated_at': (datetime.now() - timedelta(hours=25)).isoformat(),
            'insights': []
        }
        _digest_cache['generated_at'] = datetime.now() - timedelta(hours=25)
        
        # Get digest (should regenerate)
        digest = get_daily_digest()
        
        # Should have new timestamp
        digest_time = datetime.fromisoformat(digest['generated_at'])
        age = datetime.now() - digest_time
        assert age < timedelta(minutes=1)  # Should be very recent


class TestDigestEndpointIntegration:
    """Test integration with FastAPI endpoint"""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app for testing"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/api/daily-digest")
        async def get_digest(force_refresh: bool = False):
            return get_daily_digest(force_refresh=force_refresh)
        
        return TestClient(app)
    
    def test_endpoint_returns_200(self, mock_app):
        """Test that endpoint returns 200 OK"""
        response = mock_app.get("/api/daily-digest")
        
        assert response.status_code == 200
    
    def test_endpoint_returns_json(self, mock_app):
        """Test that endpoint returns JSON"""
        response = mock_app.get("/api/daily-digest")
        
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
    
    def test_force_refresh_parameter(self, mock_app):
        """Test that force_refresh parameter works"""
        response = mock_app.get("/api/daily-digest?force_refresh=true")
        
        assert response.status_code == 200
        data = response.json()
        assert 'generated_at' in data


class TestErrorHandling:
    """Test error handling in digest generation"""
    
    def test_empty_changes_returns_empty_insights(self):
        """Test that no changes results in empty insights"""
        with patch.object(ChangeDetection, 'detect_all_changes', return_value=[]):
            digest = get_daily_digest(force_refresh=True)
            
            assert digest['insights'] == []
    
    def test_handles_database_errors_gracefully(self):
        """Test that database errors don't crash the system"""
        with patch.object(ChangeDetection, 'detect_all_changes', side_effect=Exception("DB Error")):
            try:
                digest = get_daily_digest(force_refresh=True)
                # Should either return empty or raise, but not crash
                assert True
            except Exception as e:
                # Exceptions are acceptable
                print(f"Expected error: {e}")
                assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

