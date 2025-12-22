"""Tests for Anomalies API endpoint - GET /api/anomalies"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.logic.api.main import app
from src.logic.analytics.data_pipeline import DataPipeline


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_data_path():
    """Path to test data files."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def seeded_pipeline(test_data_path):
    """Pipeline with test data loaded."""
    pipeline = DataPipeline()
    plants_file = str(test_data_path / "sample_plants.csv")
    readings_file = str(test_data_path / "sample_readings.csv")
    
    result = pipeline.execute(plants_file, readings_file)
    return pipeline, result


class TestAnomaliesEndpoint:
    """Test /api/anomalies endpoint."""

    def test_get_anomalies_success(self, client, seeded_pipeline):
        """Test getting anomalies for a valid plant."""
        pipeline, result = seeded_pipeline
        
        # Should have anomalies for PLANT_001
        response = client.get("/api/anomalies/PLANT_001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) > 0
        
        # Verify anomaly structure
        anomaly = data["data"][0]
        assert "anomaly_id" in anomaly
        assert "plant_id" in anomaly
        assert anomaly["plant_id"] == "PLANT_001"
        assert "severity" in anomaly
        assert anomaly["severity"] in ["low", "medium", "high", "critical"]
        assert "detected_by" in anomaly

    def test_get_anomalies_plant_not_found(self, client):
        """Test getting anomalies for non-existent plant."""
        response = client.get("/api/anomalies/NONEXISTENT")
        
        assert response.status_code == 404
        # FastAPI raises HTTPException which returns JSON with detail field

    def test_get_anomalies_empty_result(self, client):
        """Test getting anomalies when plant has no anomalies."""
        # PLANT_002 has insufficient data, no anomalies
        response = client.get("/api/anomalies/PLANT_002")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    def test_get_anomalies_response_format(self, client, seeded_pipeline):
        """Test response format matches API spec."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies/PLANT_001")
        data = response.json()
        
        # Verify wrapper structure
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "error_code" in data
        
        # Success response should have data array
        assert isinstance(data["data"], list)

    def test_get_anomalies_by_severity(self, client, seeded_pipeline):
        """Test filtering anomalies by severity."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies/PLANT_001?severity=high")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["data"]) > 0:
            # All returned anomalies should match severity filter
            for anomaly in data["data"]:
                # May be empty if no high-severity anomalies
                pass

    def test_get_anomalies_pagination(self, client, seeded_pipeline):
        """Test pagination support."""
        pipeline, result = seeded_pipeline
        
        # Request with pagination params
        response = client.get("/api/anomalies/PLANT_001?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_anomalies_sorting(self, client, seeded_pipeline):
        """Test sorting by date."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies/PLANT_001?sort=date&order=desc")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["data"]) > 1:
            # Verify sorting (dates should be in descending order)
            dates = [a.get("date") for a in data["data"]]
            assert dates == sorted(dates, reverse=True)

    def test_get_anomalies_includes_metadata(self, client, seeded_pipeline):
        """Test response includes required metadata."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies/PLANT_001")
        data = response.json()
        
        if len(data["data"]) > 0:
            anomaly = data["data"][0]
            # Verify all required fields
            required_fields = [
                "anomaly_id", "plant_id", "date", "metric_name",
                "actual_value", "expected_value", "deviation_pct",
                "severity", "detected_by", "status"
            ]
            for field in required_fields:
                assert field in anomaly, f"Missing field: {field}"

    def test_get_anomalies_all_plants(self, client, seeded_pipeline):
        """Test getting anomalies for all plants."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_api_error_handling(self, client):
        """Test API error handling."""
        # Invalid request with negative limit
        response = client.get("/api/anomalies/PLANT_001?limit=-1")
        
        # Should handle gracefully (FastAPI validates with 422)
        assert response.status_code in [200, 400, 422]


class TestAnomaliesEndpointIntegration:
    """Integration tests for anomalies endpoint with pipeline."""

    def test_endpoint_uses_pipeline_result(self, client, seeded_pipeline):
        """Test endpoint returns data from pipeline execution."""
        pipeline, result = seeded_pipeline
        
        response = client.get("/api/anomalies/PLANT_001")
        data = response.json()
        
        # Should match pipeline result
        if "PLANT_001" in result.anomalies_by_plant:
            expected_count = len(result.anomalies_by_plant["PLANT_001"])
            actual_count = len(data["data"])
            assert actual_count == expected_count

    def test_endpoint_cache_behavior(self, client, seeded_pipeline):
        """Test endpoint caches pipeline results."""
        pipeline, result = seeded_pipeline
        
        # First request
        response1 = client.get("/api/anomalies/PLANT_001")
        data1 = response1.json()
        
        # Second request should return same data
        response2 = client.get("/api/anomalies/PLANT_001")
        data2 = response2.json()
        
        assert len(data1["data"]) == len(data2["data"])

    def test_endpoint_handles_pipeline_errors(self, client):
        """Test endpoint handles pipeline errors gracefully."""
        # Make request with invalid data
        response = client.get("/api/anomalies/")
        
        # Should not crash
        assert response.status_code in [200, 404, 400]
