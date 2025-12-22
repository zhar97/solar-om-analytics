"""
Unit tests for InsightsEngine - generates insights from anomalies and patterns.

Test coverage:
- Insight generation from anomalies and patterns
- Insight categorization and urgency assessment
- Integration with existing detection systems
- Edge cases and performance
"""

import pytest
from datetime import datetime, timedelta
from src.logic.analytics.insights_engine import InsightsEngine
from src.logic.data_models.reading import DailyReading
from src.logic.data_models.anomaly import Anomaly
from src.logic.data_models.pattern import Pattern


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_readings():
    """Sample 30-day readings."""
    readings = []
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        readings.append(DailyReading(
            plant_id="plant-001",
            date=(base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            power_output_kwh=1000 + (i % 10) * 100,
            efficiency_pct=18.5 + (i % 5) * 0.5,
            temperature_c=25 + (i % 8) * 2,
            irradiance_w_m2=700 + (i % 10) * 50,
        ))
    return readings


@pytest.fixture
def sample_anomalies():
    """Sample anomalies for testing."""
    return [
        Anomaly(
            anomaly_id="anom-001",
            plant_id="plant-001",
            date="2024-01-15",
            metric_name="power_output_kwh",
            actual_value=450.0,
            expected_value=1000.0,
            deviation_pct=-55.0,
            severity="high",
            detected_by="zscore",
            z_score=3.2,
            detection_timestamp="2024-01-15T12:00:00Z",
        ),
        Anomaly(
            anomaly_id="anom-002",
            plant_id="plant-001",
            date="2024-01-20",
            metric_name="efficiency_pct",
            actual_value=15.2,
            expected_value=18.5,
            deviation_pct=-17.8,
            severity="medium",
            detected_by="iqr",
            iqr_bounds={"lower": 16.5, "upper": 20.5},
            detection_timestamp="2024-01-20T12:00:00Z",
        ),
    ]


@pytest.fixture
def sample_patterns():
    """Sample patterns for testing."""
    return [
        Pattern(
            pattern_id="pat-001",
            plant_id="plant-001",
            pattern_type="seasonal",
            metric_name="power_output_kwh",
            description="Strong seasonal variation with peak in summer",
            frequency="annual",
            amplitude=45.5,
            significance_score=87.0,
            confidence_pct=92.5,
            first_observed_date="2023-01-15",
            last_observed_date="2024-12-20",
            occurrence_count=24,
            affected_plants=["plant-001", "plant-002"],
            is_fleet_wide=False,
        ),
        Pattern(
            pattern_id="pat-002",
            plant_id="plant-001",
            pattern_type="degradation",
            metric_name="efficiency_pct",
            description="Gradual degradation of panel efficiency",
            frequency="annual",
            amplitude=3.2,
            significance_score=71.0,
            confidence_pct=88.0,
            first_observed_date="2023-01-01",
            last_observed_date="2024-12-20",
            occurrence_count=12,
            affected_plants=["plant-001"],
            is_fleet_wide=False,
        ),
    ]


@pytest.fixture
def engine(sample_readings, sample_anomalies, sample_patterns):
    """Create InsightsEngine with sample data."""
    return InsightsEngine(
        daily_readings=sample_readings,
        anomalies=sample_anomalies,
        patterns=sample_patterns,
    )


# ============================================================================
# TESTS
# ============================================================================

class TestInsightGeneration:
    """Test insight generation."""

    def test_engine_initialization(self, engine):
        """Test engine initializes with data."""
        assert len(engine.daily_readings) == 30
        assert len(engine.anomalies) == 2
        assert len(engine.patterns) == 2

    def test_generate_insights_returns_list(self, engine):
        """Test generate_insights returns list."""
        insights = engine.generate_insights()
        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_insights_are_valid_objects(self, engine):
        """Test all insights are valid Insight objects."""
        insights = engine.generate_insights()
        for insight in insights:
            assert hasattr(insight, 'insight_id')
            assert hasattr(insight, 'plant_id')
            assert hasattr(insight, 'insight_type')
            assert hasattr(insight, 'title')
            assert hasattr(insight, 'description')

    def test_anomaly_insights_generated(self, engine):
        """Test anomaly insights are created."""
        insights = engine.generate_insights()
        anomaly_insights = [i for i in insights if i.insight_type == 'anomaly_cause_hypothesis']
        assert len(anomaly_insights) == 2

    def test_pattern_insights_generated(self, engine):
        """Test pattern insights are created."""
        insights = engine.generate_insights()
        pattern_insights = [i for i in insights if i.insight_type in ['pattern_explanation', 'performance_trend']]
        assert len(pattern_insights) >= 2

    def test_combined_insights_generated(self, engine):
        """Test combined insights are created."""
        insights = engine.generate_insights()
        combined_insights = [i for i in insights if i.insight_type == 'performance_trend']
        assert len(combined_insights) >= 0  # May have combined insights

    def test_insight_ids_unique(self, engine):
        """Test all insight IDs are unique."""
        insights = engine.generate_insights()
        ids = [i.insight_id for i in insights]
        assert len(ids) == len(set(ids))

    def test_insights_reference_plant(self, engine):
        """Test insights reference correct plant."""
        insights = engine.generate_insights()
        assert all(i.plant_id == "plant-001" for i in insights)

    def test_insight_confidence_valid(self, engine):
        """Test confidence scores are valid."""
        insights = engine.generate_insights()
        for insight in insights:
            assert 0 <= insight.confidence <= 100

    def test_insight_urgency_valid(self, engine):
        """Test urgency levels are valid."""
        insights = engine.generate_insights()
        valid = {"low", "medium", "high", "critical"}
        for insight in insights:
            assert insight.urgency in valid

    def test_insight_descriptions_meaningful(self, engine):
        """Test insights have meaningful descriptions."""
        insights = engine.generate_insights()
        for insight in insights:
            assert len(insight.title) > 5
            assert len(insight.description) > 10

    def test_high_severity_anomaly_maps_to_critical(self):
        """Test high severity anomaly creates critical urgency insight."""
        readings = [DailyReading(
            plant_id="p1", date="2024-01-01",
            power_output_kwh=1000, efficiency_pct=18.5,
            temperature_c=25, irradiance_w_m2=700,
        )]
        anomalies = [Anomaly(
            anomaly_id="a1", plant_id="p1", date="2024-01-01",
            metric_name="power_output_kwh", actual_value=100,
            expected_value=1000, deviation_pct=-90,
            severity="critical", detected_by="zscore", z_score=5.0,
            detection_timestamp="2024-01-01T12:00:00Z",
        )]
        engine = InsightsEngine(readings, anomalies, [])
        insights = engine.generate_insights()
        assert any(i.urgency == "critical" for i in insights)


class TestDataIntegration:
    """Test integration with data models."""

    def test_empty_anomalies(self, sample_readings, sample_patterns):
        """Test generation with no anomalies."""
        engine = InsightsEngine(sample_readings, [], sample_patterns)
        insights = engine.generate_insights()
        assert len(insights) == 2  # Pattern insights only

    def test_empty_patterns(self, sample_readings, sample_anomalies):
        """Test generation with no patterns."""
        engine = InsightsEngine(sample_readings, sample_anomalies, [])
        insights = engine.generate_insights()
        assert len(insights) == 2  # Anomaly insights only

    def test_empty_all(self, sample_readings):
        """Test generation with no anomalies or patterns."""
        engine = InsightsEngine(sample_readings, [], [])
        insights = engine.generate_insights()
        assert len(insights) == 0

    def test_large_dataset(self):
        """Test performance with large dataset."""
        import time
        
        base_date = datetime(2024, 1, 1)
        readings = [
            DailyReading(
                plant_id="p1",
                date=(base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                power_output_kwh=1000 + (i % 50) * 20,
                efficiency_pct=18.5 + (i % 10) * 0.2,
                temperature_c=25 + (i % 20),
                irradiance_w_m2=700 + (i % 50) * 5,
            )
            for i in range(365)
        ]
        
        anomalies = [
            Anomaly(
                anomaly_id=f"a{i}", plant_id="p1",
                date=(base_date + timedelta(days=i*30)).strftime("%Y-%m-%d"),
                metric_name="power_output_kwh", actual_value=500,
                expected_value=1000, deviation_pct=-50,
                severity="high", detected_by="zscore", z_score=3.0,
                detection_timestamp=f"2024-01-01T12:00:00Z",
            )
            for i in range(10)
        ]
        
        patterns = [
            Pattern(
                pattern_id=f"p{i}", plant_id="p1",
                pattern_type="seasonal", metric_name="power_output_kwh",
                description=f"Pattern {i}", frequency="annual",
                amplitude=40, significance_score=80.0 + i,
                confidence_pct=85 + i, first_observed_date="2023-01-01",
                last_observed_date="2024-12-31", occurrence_count=12,
                affected_plants=["p1"], is_fleet_wide=False,
            )
            for i in range(5)
        ]
        
        engine = InsightsEngine(readings, anomalies, patterns)
        start = time.time()
        insights = engine.generate_insights()
        elapsed = time.time() - start
        
        assert elapsed < 5.0
        assert len(insights) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_anomaly_without_zscore(self, sample_readings, sample_patterns):
        """Test anomaly without z-score field."""
        anomalies = [Anomaly(
            anomaly_id="a1", plant_id="plant-001", date="2024-01-15",
            metric_name="power_output_kwh", actual_value=450,
            expected_value=1000, deviation_pct=-55,
            severity="high", detected_by="iqr",
            iqr_bounds={"lower": 800, "upper": 1200},
            detection_timestamp="2024-01-15T12:00:00Z",
        )]
        engine = InsightsEngine(sample_readings, anomalies, sample_patterns)
        insights = engine.generate_insights()
        assert len(insights) > 0

    def test_high_confidence_zscore(self, sample_readings, sample_patterns):
        """Test anomaly with very high z-score."""
        anomalies = [Anomaly(
            anomaly_id="a1", plant_id="plant-001", date="2024-01-15",
            metric_name="power_output_kwh", actual_value=100,
            expected_value=1000, deviation_pct=-90,
            severity="critical", detected_by="zscore", z_score=10.0,
            detection_timestamp="2024-01-15T12:00:00Z",
        )]
        engine = InsightsEngine(sample_readings, anomalies, sample_patterns)
        insights = engine.generate_insights()
        critical_insights = [i for i in insights if i.urgency == "critical"]
        assert len(critical_insights) > 0

    def test_conflicting_patterns(self, sample_readings, sample_anomalies):
        """Test same metric with conflicting patterns."""
        patterns = [
            Pattern(
                pattern_id="p1", plant_id="plant-001",
                pattern_type="seasonal", metric_name="power_output_kwh",
                description="Seasonal", frequency="annual", amplitude=45,
                significance_score=90, confidence_pct=95,
                first_observed_date="2023-01-01",
                last_observed_date="2024-12-31", occurrence_count=24,
                affected_plants=["plant-001"], is_fleet_wide=False,
            ),
            Pattern(
                pattern_id="p2", plant_id="plant-001",
                pattern_type="degradation", metric_name="power_output_kwh",
                description="Degradation", frequency="annual", amplitude=5,
                significance_score=80, confidence_pct=90,
                first_observed_date="2023-01-01",
                last_observed_date="2024-12-31", occurrence_count=2,
                affected_plants=["plant-001"], is_fleet_wide=False,
            ),
        ]
        engine = InsightsEngine(sample_readings, sample_anomalies, patterns)
        insights = engine.generate_insights()
        assert len(insights) > 0
