"""Additional tests for API endpoints to improve coverage."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.logic.api.main import app, get_pipeline


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_data_path():
    """Path to test data files."""
    return Path(__file__).parent.parent / "fixtures"


class TestHealthCheckEndpoint:
    """Test health check endpoint."""

    def test_root_endpoint_success(self, client):
        """Test root endpoint returns success."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data


class TestGetAllAnomaliesEndpoint:
    """Test /api/anomalies endpoint."""

    def test_get_all_anomalies_pagination(self, client):
        """Test pagination parameters."""
        response = client.get("/api/anomalies?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 10

    def test_get_all_anomalies_with_skip(self, client):
        """Test skip parameter."""
        response1 = client.get("/api/anomalies?skip=0&limit=5")
        response2 = client.get("/api/anomalies?skip=5&limit=5")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # First and second page should have different data
        if len(data1["data"]) > 0 and len(data2["data"]) > 0:
            assert data1["data"][0]["anomaly_id"] != data2["data"][0]["anomaly_id"]

    def test_get_all_anomalies_limit_bounds(self, client):
        """Test limit parameter bounds."""
        # Valid limit
        response = client.get("/api/anomalies?limit=100")
        assert response.status_code == 200
        
        # Invalid limit (too high - should be capped at 1000)
        response = client.get("/api/anomalies?limit=5000")
        assert response.status_code == 422  # Validation error

    def test_get_all_anomalies_response_structure(self, client):
        """Test response contains required fields."""
        response = client.get("/api/anomalies")
        data = response.json()
        
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "error_code" in data
        assert isinstance(data["data"], list)


class TestPlantsEndpoint:
    """Test /api/plants endpoint."""

    def test_get_plants_success(self, client):
        """Test getting all plants."""
        response = client.get("/api/plants")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_plants_structure(self, client):
        """Test plant response structure."""
        response = client.get("/api/plants")
        data = response.json()
        
        if len(data["data"]) > 0:
            plant = data["data"][0]
            assert "plant_id" in plant
            assert "name" in plant
            assert "location" in plant
            assert "capacity_kwp" in plant
            assert "anomaly_count" in plant
            assert isinstance(plant["anomaly_count"], int)

    def test_get_plants_anomaly_count(self, client):
        """Test anomaly count is non-negative."""
        response = client.get("/api/plants")
        data = response.json()
        
        for plant in data["data"]:
            assert plant["anomaly_count"] >= 0


class TestPatternsEndpoint:
    """Test /api/patterns endpoint."""

    def test_get_patterns_success(self, client):
        """Test getting all patterns."""
        response = client.get("/api/patterns")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "patterns" in data
        assert isinstance(data["patterns"], list)

    def test_get_patterns_pagination(self, client):
        """Test patterns pagination."""
        response = client.get("/api/patterns?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) <= 5
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

    def test_get_patterns_filter_by_type(self, client):
        """Test filtering patterns by type."""
        response = client.get("/api/patterns?pattern_type=seasonal")
        
        assert response.status_code == 200
        data = response.json()
        
        for pattern in data["patterns"]:
            assert pattern["pattern_type"] == "seasonal"

    def test_get_patterns_filter_by_confidence(self, client):
        """Test filtering patterns by minimum confidence."""
        response = client.get("/api/patterns?min_confidence=80")
        
        assert response.status_code == 200
        data = response.json()
        
        for pattern in data["patterns"]:
            assert pattern["confidence_pct"] >= 80

    def test_get_patterns_filter_by_plant(self, client):
        """Test filtering patterns by plant_id."""
        # First get all patterns to find a plant_id
        response_all = client.get("/api/patterns")
        all_patterns = response_all.json()["patterns"]
        
        if len(all_patterns) > 0:
            plant_id = all_patterns[0]["plant_id"]
            response = client.get(f"/api/patterns?plant_id={plant_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            for pattern in data["patterns"]:
                assert pattern["plant_id"] == plant_id

    def test_get_patterns_sort_by_confidence(self, client):
        """Test sorting patterns by confidence."""
        response = client.get("/api/patterns?sort_by=confidence_pct&sort_order=desc")
        
        assert response.status_code == 200
        data = response.json()
        patterns = data["patterns"]
        
        # Check descending order
        if len(patterns) > 1:
            for i in range(len(patterns) - 1):
                assert patterns[i]["confidence_pct"] >= patterns[i + 1]["confidence_pct"]

    def test_get_patterns_sort_by_date(self, client):
        """Test sorting patterns by date."""
        response = client.get("/api/patterns?sort_by=first_observed_date&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        patterns = data["patterns"]
        
        # Check ascending order
        if len(patterns) > 1:
            for i in range(len(patterns) - 1):
                assert patterns[i]["first_observed_date"] <= patterns[i + 1]["first_observed_date"]

    def test_get_patterns_sort_by_significance(self, client):
        """Test sorting patterns by significance score."""
        response = client.get("/api/patterns?sort_by=significance_score&sort_order=desc")
        
        assert response.status_code == 200
        data = response.json()
        patterns = data["patterns"]
        
        # Check descending order
        if len(patterns) > 1:
            for i in range(len(patterns) - 1):
                assert patterns[i]["significance_score"] >= patterns[i + 1]["significance_score"]

    def test_get_patterns_response_structure(self, client):
        """Test pattern response structure."""
        response = client.get("/api/patterns")
        data = response.json()
        
        if len(data["patterns"]) > 0:
            pattern = data["patterns"][0]
            assert "pattern_id" in pattern
            assert "plant_id" in pattern
            assert "pattern_type" in pattern
            assert "metric_name" in pattern
            assert "description" in pattern
            assert "frequency" in pattern
            assert "amplitude" in pattern
            assert "significance_score" in pattern
            assert "confidence_pct" in pattern
            assert "first_observed_date" in pattern
            assert "last_observed_date" in pattern
            assert "occurrence_count" in pattern
            assert "affected_plants" in pattern
            assert "is_fleet_wide" in pattern


class TestPatternsByPlantEndpoint:
    """Test /api/patterns/{plant_id} endpoint."""

    def test_get_patterns_by_plant_success(self, client):
        """Test getting patterns for a specific plant."""
        # First find a valid plant_id
        plants_response = client.get("/api/plants")
        plants = plants_response.json()["data"]
        
        if len(plants) > 0:
            plant_id = plants[0]["plant_id"]
            response = client.get(f"/api/patterns/{plant_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "patterns" in data

    def test_get_patterns_by_plant_not_found(self, client):
        """Test 404 for non-existent plant."""
        response = client.get("/api/patterns/NONEXISTENT")
        
        assert response.status_code == 404

    def test_get_patterns_by_plant_with_filters(self, client):
        """Test patterns endpoint with filters."""
        plants_response = client.get("/api/plants")
        plants = plants_response.json()["data"]
        
        if len(plants) > 0:
            plant_id = plants[0]["plant_id"]
            response = client.get(
                f"/api/patterns/{plant_id}?pattern_type=seasonal&min_confidence=70"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            for pattern in data["patterns"]:
                assert pattern["plant_id"] == plant_id
                assert pattern["pattern_type"] == "seasonal"
                assert pattern["confidence_pct"] >= 70


class TestErrorHandling:
    """Test error handling in API."""

    def test_invalid_query_parameters(self, client):
        """Test invalid query parameters."""
        response = client.get("/api/anomalies?limit=invalid")
        
        assert response.status_code == 422  # Validation error

    def test_negative_skip(self, client):
        """Test negative skip parameter."""
        response = client.get("/api/anomalies?skip=-1")
        
        assert response.status_code == 422

    def test_zero_limit(self, client):
        """Test zero limit parameter."""
        response = client.get("/api/anomalies?limit=0")
        
        assert response.status_code == 422

    @patch("src.logic.api.main.get_pipeline")
    def test_pipeline_exception_handling(self, mock_pipeline, client):
        """Test exception handling in endpoints."""
        mock_pipeline.side_effect = Exception("Test error")
        
        response = client.get("/api/anomalies")
        
        # Should handle exception gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data


class TestMissingData:
    """Test endpoints when no data is available."""

    @patch("src.logic.api.main.get_pipeline")
    def test_no_data_available(self, mock_pipeline, client):
        """Test response when no data is available."""
        mock_pipeline.return_value = (MagicMock(), None)
        
        response = client.get("/api/anomalies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "NO_DATA" in data["error_code"]

    @patch("src.logic.api.main.get_pipeline")
    def test_plants_no_data(self, mock_pipeline, client):
        """Test /api/plants when no data available."""
        mock_pipeline.return_value = (MagicMock(), None)
        
        response = client.get("/api/plants")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["data"]) == 0
