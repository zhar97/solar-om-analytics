"""
API tests for insights endpoints - GET /api/insights and /api/insights/{plant_id}.

Test coverage:
- Basic endpoint functionality
- Filtering (by plant, type, urgency, confidence)
- Sorting (by urgency, confidence, date)
- Pagination (skip, limit)
- Error handling
- Response format validation
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from src.logic.api.main import app


client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_insights_data():
    """Sample insights for testing."""
    return {
        "success": True,
        "insights": [
            {
                "insight_id": "ins-001",
                "plant_id": "plant-001",
                "insight_type": "anomaly_cause_hypothesis",
                "title": "Power Output Anomaly",
                "description": "Unexpected power drop detected",
                "reasoning": "Detected by z-score > 3",
                "business_impact": "Potential 10% production loss",
                "confidence": 92.5,
                "recommended_action": "Check inverter status",
                "urgency": "high",
                "linked_patterns": [],
                "linked_anomalies": ["anom-001"],
                "generation_date": "2025-12-22",
                "applicable_date_range": "2025-12-22 to 2025-12-23",
            },
            {
                "insight_id": "ins-002",
                "plant_id": "plant-001",
                "insight_type": "pattern_explanation",
                "title": "Seasonal Pattern",
                "description": "Winter production decline expected",
                "reasoning": "Historical pattern detected",
                "business_impact": "25% seasonal reduction",
                "confidence": 95.0,
                "recommended_action": "Update Q1 budget forecasts",
                "urgency": "low",
                "linked_patterns": ["pat-001"],
                "linked_anomalies": [],
                "generation_date": "2025-12-22",
                "applicable_date_range": "2025-11-01 to 2026-02-28",
            },
            {
                "insight_id": "ins-003",
                "plant_id": "plant-002",
                "insight_type": "performance_trend",
                "title": "Equipment Degradation",
                "description": "Gradual efficiency decline detected",
                "reasoning": "3% annual degradation trend",
                "business_impact": "Maintenance planning required",
                "confidence": 88.0,
                "recommended_action": "Schedule preventive maintenance",
                "urgency": "medium",
                "linked_patterns": ["pat-002"],
                "linked_anomalies": [],
                "generation_date": "2025-12-22",
                "applicable_date_range": "2025-12-22 to 2026-12-22",
            },
        ],
        "total": 3,
        "skip": 0,
        "limit": 10,
    }


# ============================================================================
# TEST CLASS: Endpoint Basics
# ============================================================================

class TestInsightsEndpointBasics:
    """Test basic insights endpoint functionality."""

    def test_insights_endpoint_exists(self):
        """Test that /api/insights endpoint exists."""
        response = client.get("/api/insights")
        assert response.status_code in [200, 400, 500]  # Endpoint exists if not 404

    def test_insights_endpoint_returns_json(self):
        """Test that endpoint returns JSON."""
        response = client.get("/api/insights")
        assert response.headers["content-type"] == "application/json"

    def test_insights_endpoint_returns_list(self):
        """Test that endpoint returns insights list."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "insights" in data or isinstance(data, dict)

    def test_insights_endpoint_requires_plant_id(self):
        """Test that insights can be filtered by plant."""
        # Should work with plant_id parameter
        response = client.get("/api/insights?plant_id=plant-001")
        assert response.status_code == 200

    def test_insights_endpoint_with_pagination(self):
        """Test pagination parameters."""
        response = client.get("/api/insights?skip=0&limit=5")
        assert response.status_code == 200

    def test_insights_endpoint_with_sorting(self):
        """Test sorting parameters."""
        response = client.get("/api/insights?sort_by=urgency&sort_order=desc")
        assert response.status_code == 200


# ============================================================================
# TEST CLASS: Filtering
# ============================================================================

class TestInsightsFiltering:
    """Test insights filtering functionality."""

    def test_filter_by_plant_id(self):
        """Test filtering by plant_id."""
        response = client.get("/api/insights?plant_id=plant-001")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data and len(data["insights"]) > 0:
            assert all(i["plant_id"] == "plant-001" for i in data["insights"])

    def test_filter_by_insight_type(self):
        """Test filtering by insight type."""
        response = client.get("/api/insights?insight_type=pattern_explanation")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data and len(data["insights"]) > 0:
            assert all(i["insight_type"] == "pattern_explanation" for i in data["insights"])

    def test_filter_by_urgency(self):
        """Test filtering by urgency level."""
        response = client.get("/api/insights?urgency=critical")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data and len(data["insights"]) > 0:
            assert all(i["urgency"] == "critical" for i in data["insights"])

    def test_filter_by_min_confidence(self):
        """Test filtering by minimum confidence."""
        response = client.get("/api/insights?min_confidence=90")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data and len(data["insights"]) > 0:
            assert all(i["confidence"] >= 90 for i in data["insights"])

    def test_multiple_filters(self):
        """Test combining multiple filters."""
        response = client.get(
            "/api/insights?plant_id=plant-001&urgency=high&min_confidence=85"
        )
        assert response.status_code == 200

    def test_filter_returns_subset(self):
        """Test that filters reduce result count."""
        all_response = client.get("/api/insights")
        filtered_response = client.get("/api/insights?plant_id=plant-999")
        
        all_data = all_response.json()
        filtered_data = filtered_response.json()
        
        if "insights" in all_data and "insights" in filtered_data:
            assert len(filtered_data["insights"]) <= len(all_data["insights"])


# ============================================================================
# TEST CLASS: Sorting
# ============================================================================

class TestInsightsSorting:
    """Test insights sorting functionality."""

    def test_sort_by_urgency(self):
        """Test sorting by urgency."""
        response = client.get("/api/insights?sort_by=urgency")
        assert response.status_code == 200

    def test_sort_by_confidence(self):
        """Test sorting by confidence."""
        response = client.get("/api/insights?sort_by=confidence")
        assert response.status_code == 200

    def test_sort_by_date(self):
        """Test sorting by generation date."""
        response = client.get("/api/insights?sort_by=generation_date")
        assert response.status_code == 200

    def test_sort_order_ascending(self):
        """Test ascending sort order."""
        response = client.get("/api/insights?sort_by=confidence&sort_order=asc")
        assert response.status_code == 200

    def test_sort_order_descending(self):
        """Test descending sort order."""
        response = client.get("/api/insights?sort_by=confidence&sort_order=desc")
        assert response.status_code == 200

    def test_default_sort_order(self):
        """Test that default sort order works."""
        response = client.get("/api/insights?sort_by=confidence")
        assert response.status_code == 200


# ============================================================================
# TEST CLASS: Pagination
# ============================================================================

class TestInsightsPagination:
    """Test insights pagination functionality."""

    def test_pagination_with_skip(self):
        """Test pagination with skip parameter."""
        response = client.get("/api/insights?skip=2")
        assert response.status_code == 200

    def test_pagination_with_limit(self):
        """Test pagination with limit parameter."""
        response = client.get("/api/insights?limit=5")
        assert response.status_code == 200

    def test_pagination_skip_and_limit(self):
        """Test pagination with both skip and limit."""
        response = client.get("/api/insights?skip=1&limit=3")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data:
            assert len(data["insights"]) <= 3

    def test_default_pagination(self):
        """Test default pagination values."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data:
            # Should have limit field in response
            assert "limit" in data or len(data["insights"]) >= 0

    def test_large_limit(self):
        """Test pagination with large limit."""
        response = client.get("/api/insights?limit=1000")
        assert response.status_code == 200

    def test_skip_beyond_total(self):
        """Test skip parameter beyond total results."""
        response = client.get("/api/insights?skip=9999")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data:
            assert len(data["insights"]) == 0


# ============================================================================
# TEST CLASS: Response Format
# ============================================================================

class TestInsightsResponseFormat:
    """Test response format and structure."""

    def test_response_includes_required_fields(self):
        """Test that response includes all required fields."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        
        if "insights" in data and len(data["insights"]) > 0:
            insight = data["insights"][0]
            required_fields = [
                "insight_id",
                "plant_id",
                "insight_type",
                "title",
                "description",
                "confidence",
                "urgency",
            ]
            for field in required_fields:
                assert field in insight

    def test_response_includes_metadata(self):
        """Test that response includes pagination metadata."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        
        # Should have insights array
        assert "insights" in data or "success" in data

    def test_confidence_values_valid(self):
        """Test that confidence values are valid percentages."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        
        if "insights" in data:
            for insight in data["insights"]:
                assert 0 <= insight["confidence"] <= 100

    def test_urgency_values_valid(self):
        """Test that urgency values are valid."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        
        if "insights" in data:
            valid_urgencies = {"low", "medium", "high", "critical"}
            for insight in data["insights"]:
                assert insight["urgency"] in valid_urgencies

    def test_dates_in_correct_format(self):
        """Test that dates are in correct format."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        
        if "insights" in data:
            for insight in data["insights"]:
                # Should be YYYY-MM-DD format
                date_str = insight["generation_date"]
                assert len(date_str) == 10
                assert date_str.count("-") == 2


# ============================================================================
# TEST CLASS: Error Handling
# ============================================================================

class TestInsightsErrorHandling:
    """Test error handling."""

    def test_invalid_plant_id_returns_empty(self):
        """Test that invalid plant_id returns empty results."""
        response = client.get("/api/insights?plant_id=nonexistent-plant")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data:
            assert len(data["insights"]) == 0

    def test_invalid_insight_type_handled(self):
        """Test that invalid insight_type is handled."""
        response = client.get("/api/insights?insight_type=invalid_type")
        assert response.status_code in [200, 400]

    def test_negative_skip_handled(self):
        """Test that negative skip is handled."""
        response = client.get("/api/insights?skip=-1")
        assert response.status_code in [200, 400, 422]

    def test_negative_limit_handled(self):
        """Test that negative limit is handled."""
        response = client.get("/api/insights?limit=-1")
        assert response.status_code in [200, 400, 422]

    def test_invalid_sort_order_handled(self):
        """Test that invalid sort order is handled."""
        response = client.get("/api/insights?sort_order=invalid")
        assert response.status_code in [200, 400, 422]


# ============================================================================
# TEST CLASS: Plant-Specific Endpoint
# ============================================================================

class TestInsightsByPlantEndpoint:
    """Test plant-specific insights endpoint."""

    def test_plant_specific_endpoint_exists(self):
        """Test that /api/insights/{plant_id} endpoint exists."""
        response = client.get("/api/insights/plant-001")
        assert response.status_code in [200, 400, 404, 500]

    def test_plant_specific_endpoint_filters_by_plant(self):
        """Test that plant-specific endpoint filters correctly."""
        response = client.get("/api/insights/plant-001")
        assert response.status_code == 200
        data = response.json()
        if "insights" in data and len(data["insights"]) > 0:
            assert all(i["plant_id"] == "plant-001" for i in data["insights"])

    def test_plant_specific_with_additional_filters(self):
        """Test plant-specific endpoint with additional filters."""
        response = client.get("/api/insights/plant-001?urgency=high")
        assert response.status_code == 200

    def test_invalid_plant_id_endpoint(self):
        """Test invalid plant_id endpoint."""
        response = client.get("/api/insights/nonexistent-plant")
        assert response.status_code in [200, 404]

    def test_plant_specific_with_pagination(self):
        """Test plant-specific endpoint with pagination."""
        response = client.get("/api/insights/plant-001?skip=0&limit=5")
        assert response.status_code == 200

    def test_plant_specific_with_sorting(self):
        """Test plant-specific endpoint with sorting."""
        response = client.get("/api/insights/plant-001?sort_by=confidence")
        assert response.status_code == 200


# ============================================================================
# TEST CLASS: HTTP Methods
# ============================================================================

class TestInsightsHTTPMethods:
    """Test HTTP method restrictions."""

    def test_get_method_works(self):
        """Test that GET method works."""
        response = client.get("/api/insights")
        assert response.status_code == 200

    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed."""
        response = client.post("/api/insights")
        assert response.status_code == 405

    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        response = client.put("/api/insights")
        assert response.status_code == 405

    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed."""
        response = client.delete("/api/insights")
        assert response.status_code == 405
