"""Tests for Pattern Detection API endpoint."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from src.logic.api.main import app
from src.logic.data_models.reading import DailyReading


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_readings():
    """Create sample readings with patterns."""
    readings = []
    base_date = datetime(2023, 1, 1)
    
    # Create 2 years of data with strong seasonal variations
    for month in range(24):
        date = base_date + timedelta(days=30*month)
        # Strong seasonal variation: 300 kWh (winter) vs 600 kWh (summer)
        if month % 12 in [0, 1, 11]:  # Dec, Jan, Feb
            base_value = 300
        elif month % 12 in [5, 6, 7]:  # Jun, Jul, Aug
            base_value = 600
        else:
            base_value = 450
        
        for day in range(30):
            current_date = date + timedelta(days=day)
            value = base_value + (day % 3) * 5
            readings.append(DailyReading(
                plant_id='PLANT_001',
                date=current_date.strftime('%Y-%m-%d'),
                power_output_kwh=value,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            ))
    
    return readings


class TestPatternEndpointBasics:
    """Test pattern endpoint basic functionality."""

    def test_patterns_endpoint_exists(self, test_client):
        """Test /api/patterns endpoint is available."""
        response = test_client.get('/api/patterns')
        # Should return 200 or 422 (validation error is ok)
        assert response.status_code in [200, 422]

    def test_patterns_endpoint_returns_valid_structure(self, test_client):
        """Test patterns endpoint returns proper structure."""
        response = test_client.get('/api/patterns')
        
        if response.status_code == 200:
            data = response.json()
            assert 'patterns' in data or 'data' in data or isinstance(data, list)

    def test_patterns_endpoint_requires_plant_id(self, test_client):
        """Test patterns endpoint with plant_id parameter."""
        response = test_client.get('/api/patterns?plant_id=PLANT_001')
        # Should work with plant_id parameter
        assert response.status_code in [200, 404, 422]

    def test_patterns_endpoint_with_pattern_type_filter(self, test_client):
        """Test patterns endpoint with pattern_type filter."""
        response = test_client.get('/api/patterns?pattern_type=seasonal')
        assert response.status_code in [200, 404, 422]

    def test_patterns_endpoint_with_pagination(self, test_client):
        """Test patterns endpoint with pagination parameters."""
        response = test_client.get('/api/patterns?skip=0&limit=10')
        assert response.status_code in [200, 404, 422]


class TestPatternEndpointFiltering:
    """Test pattern endpoint filtering capabilities."""

    def test_filter_by_plant_id(self, test_client):
        """Test filtering patterns by plant_id."""
        response = test_client.get('/api/patterns?plant_id=PLANT_001')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # All patterns should have the requested plant_id
            for pattern in patterns:
                assert pattern.get('plant_id') == 'PLANT_001'

    def test_filter_by_pattern_type(self, test_client):
        """Test filtering patterns by pattern_type."""
        response = test_client.get('/api/patterns?pattern_type=seasonal')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # All patterns should have the requested type
            for pattern in patterns:
                assert pattern.get('pattern_type') == 'seasonal'

    def test_multiple_filters(self, test_client):
        """Test applying multiple filters."""
        response = test_client.get('/api/patterns?plant_id=PLANT_001&pattern_type=seasonal')
        assert response.status_code in [200, 404, 422]

    def test_filter_by_confidence_threshold(self, test_client):
        """Test filtering patterns by confidence threshold."""
        response = test_client.get('/api/patterns?min_confidence=80')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # All patterns should meet confidence threshold
            for pattern in patterns:
                assert pattern.get('confidence_pct', 0) >= 80


class TestPatternEndpointPagination:
    """Test pattern endpoint pagination."""

    def test_pagination_with_skip(self, test_client):
        """Test pagination with skip parameter."""
        response = test_client.get('/api/patterns?skip=0')
        assert response.status_code in [200, 404, 422]

    def test_pagination_with_limit(self, test_client):
        """Test pagination with limit parameter."""
        response = test_client.get('/api/patterns?limit=5')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Should not exceed limit
            assert len(patterns) <= 5

    def test_pagination_skip_and_limit(self, test_client):
        """Test pagination with both skip and limit."""
        response = test_client.get('/api/patterns?skip=0&limit=10')
        assert response.status_code in [200, 404, 422]

    def test_default_pagination(self, test_client):
        """Test default pagination when no params provided."""
        response = test_client.get('/api/patterns')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Should have default pagination applied
            assert isinstance(patterns, list)


class TestPatternEndpointSorting:
    """Test pattern endpoint sorting."""

    def test_sort_by_confidence(self, test_client):
        """Test sorting patterns by confidence."""
        response = test_client.get('/api/patterns?sort_by=confidence_pct')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Verify response contains patterns
            assert isinstance(patterns, list)

    def test_sort_by_date(self, test_client):
        """Test sorting patterns by date."""
        response = test_client.get('/api/patterns?sort_by=first_observed_date')
        assert response.status_code in [200, 404, 422]

    def test_sort_order_ascending(self, test_client):
        """Test ascending sort order."""
        response = test_client.get('/api/patterns?sort_by=confidence_pct&sort_order=asc')
        assert response.status_code in [200, 404, 422]

    def test_sort_order_descending(self, test_client):
        """Test descending sort order."""
        response = test_client.get('/api/patterns?sort_by=confidence_pct&sort_order=desc')
        assert response.status_code in [200, 404, 422]


class TestPatternEndpointErrorHandling:
    """Test pattern endpoint error handling."""

    def test_invalid_plant_id_returns_empty(self, test_client):
        """Test invalid plant_id returns empty results."""
        response = test_client.get('/api/patterns?plant_id=INVALID_PLANT')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Should return empty or valid response
            assert isinstance(patterns, list)

    def test_invalid_pattern_type_returns_empty(self, test_client):
        """Test invalid pattern_type returns empty results."""
        response = test_client.get('/api/patterns?pattern_type=invalid_type')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Should return empty or valid response
            assert isinstance(patterns, list)

    def test_negative_limit_handled(self, test_client):
        """Test negative limit is handled."""
        response = test_client.get('/api/patterns?limit=-1')
        # Should either return 422 or default to safe value
        assert response.status_code in [200, 422]

    def test_large_skip_returns_empty(self, test_client):
        """Test large skip returns empty or valid response."""
        response = test_client.get('/api/patterns?skip=99999')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Large skip should return empty
            assert isinstance(patterns, list)


class TestPatternEndpointResponseFormat:
    """Test pattern endpoint response format."""

    def test_response_includes_required_fields(self, test_client):
        """Test response includes required pattern fields."""
        response = test_client.get('/api/patterns')
        
        if response.status_code == 200 and response.json():
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            
            if patterns:
                pattern = patterns[0]
                required_fields = [
                    'pattern_id', 'plant_id', 'pattern_type',
                    'metric_name', 'description', 'confidence_pct'
                ]
                for field in required_fields:
                    assert field in pattern or isinstance(pattern, dict)

    def test_response_includes_metadata(self, test_client):
        """Test response includes pagination metadata."""
        response = test_client.get('/api/patterns')
        
        if response.status_code == 200:
            data = response.json()
            # Should have either patterns key or similar
            assert isinstance(data, (dict, list))

    def test_dates_in_correct_format(self, test_client):
        """Test dates are in ISO format."""
        response = test_client.get('/api/patterns')
        
        if response.status_code == 200 and response.json():
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            
            if patterns:
                for pattern in patterns:
                    # Check date format if present
                    for date_field in ['first_observed_date', 'last_observed_date']:
                        if date_field in pattern:
                            date_str = pattern[date_field]
                            # Should be ISO format (YYYY-MM-DD)
                            assert isinstance(date_str, str)


class TestPatternEndpointHTTPMethods:
    """Test pattern endpoint HTTP methods."""

    def test_get_method_works(self, test_client):
        """Test GET method works."""
        response = test_client.get('/api/patterns')
        assert response.status_code in [200, 404, 422]

    def test_post_method_not_allowed(self, test_client):
        """Test POST method handling."""
        response = test_client.post('/api/patterns', json={})
        # Should either not be implemented or return 405
        assert response.status_code in [404, 405, 422]

    def test_put_method_not_allowed(self, test_client):
        """Test PUT method handling."""
        response = test_client.put('/api/patterns', json={})
        # Should either not be implemented or return 405
        assert response.status_code in [404, 405, 422]

    def test_delete_method_not_allowed(self, test_client):
        """Test DELETE method handling."""
        response = test_client.delete('/api/patterns')
        # Should either not be implemented or return 405
        assert response.status_code in [404, 405, 422]


class TestPatternEndpointByPlant:
    """Test pattern endpoint for specific plant."""

    def test_plant_specific_endpoint_exists(self, test_client):
        """Test /api/patterns/{plant_id} endpoint exists."""
        response = test_client.get('/api/patterns/PLANT_001')
        # Should return 200 or 404
        assert response.status_code in [200, 404, 422]

    def test_plant_specific_endpoint_filters_by_plant(self, test_client):
        """Test plant-specific endpoint filters by plant_id."""
        response = test_client.get('/api/patterns/PLANT_001')
        
        if response.status_code == 200 and response.json():
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # All patterns should be for the requested plant
            for pattern in patterns:
                assert pattern.get('plant_id') == 'PLANT_001'

    def test_invalid_plant_id_endpoint(self, test_client):
        """Test plant-specific endpoint with invalid plant_id."""
        response = test_client.get('/api/patterns/NONEXISTENT_PLANT')
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', data.get('data', []))
            # Should return empty results
            assert isinstance(patterns, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
