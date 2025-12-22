"""Tests for DataPipeline - Orchestrates full data analysis workflow."""
import pytest
from pathlib import Path

from src.logic.analytics.data_pipeline import DataPipeline


class TestDataPipeline:
    """Test data pipeline orchestration."""

    @pytest.fixture
    def test_data_path(self):
        """Path to test data files."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def pipeline(self):
        """Pipeline instance."""
        return DataPipeline()

    def test_pipeline_initialization(self):
        """Test pipeline initializes with default components."""
        pipeline = DataPipeline()
        assert pipeline.csv_loader is not None
        assert pipeline.validator is not None
        assert pipeline.baseline_calculator is not None
        assert pipeline.anomaly_detector is not None

    def test_execute_full_pipeline(self, pipeline, test_data_path):
        """Test executing full pipeline end-to-end."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)

        assert result.success is True
        assert len(result.plants) == 3
        assert len(result.readings_by_plant) > 0
        assert len(result.baselines_by_plant) > 0
        assert len(result.anomalies_by_plant) > 0
        assert len(result.errors) == 0

    def test_pipeline_plants_loaded(self, pipeline, test_data_path):
        """Test plants are loaded correctly."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)

        assert "PLANT_001" in result.plants
        assert "PLANT_002" in result.plants
        assert "PLANT_003" in result.plants

    def test_pipeline_readings_processed(self, pipeline, test_data_path):
        """Test readings are processed and stored."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)

        # PLANT_001 should have 13 readings
        assert "PLANT_001" in result.readings_by_plant
        assert len(result.readings_by_plant["PLANT_001"]) == 13

    def test_pipeline_baselines_calculated(self, pipeline, test_data_path):
        """Test baselines are calculated for plants with sufficient data."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)

        # PLANT_001 should have baseline
        assert "PLANT_001" in result.baselines_by_plant
        assert "power_output_kwh" in result.baselines_by_plant["PLANT_001"]

        baseline = result.baselines_by_plant["PLANT_001"]["power_output_kwh"]
        assert baseline.mean > 0
        assert baseline.std_dev >= 0

    def test_pipeline_anomalies_detected(self, pipeline, test_data_path):
        """Test anomalies are detected."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)

        # Should detect at least 1 anomaly (PLANT_001 has anomalous reading on 2025-01-13)
        assert len(result.anomalies_by_plant["PLANT_001"]) >= 1

        anomaly = result.anomalies_by_plant["PLANT_001"][0]
        assert anomaly.plant_id == "PLANT_001"
        assert anomaly.severity in ["low", "medium", "high", "critical"]
        assert anomaly.detected_by in ["zscore", "iqr"]

    def test_pipeline_with_validation(self, pipeline, test_data_path):
        """Test pipeline with validation enabled."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file, validate=True)

        assert result.success is True
        assert len(result.readings_by_plant) > 0

    def test_pipeline_without_validation(self, pipeline, test_data_path):
        """Test pipeline with validation disabled."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file, validate=False)

        assert result.success is True
        # Should still process plants
        assert len(result.readings_by_plant) > 0

    def test_pipeline_multiple_metrics(self, pipeline, test_data_path):
        """Test pipeline analyzing multiple metrics."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        metrics = ["power_output_kwh", "efficiency_pct", "temperature_c"]
        result = pipeline.execute(plants_file, readings_file, metrics=metrics)

        assert result.success is True
        # PLANT_001 should have baselines for all metrics (has 13 readings)
        assert "PLANT_001" in result.baselines_by_plant
        baselines = result.baselines_by_plant["PLANT_001"]
        assert "power_output_kwh" in baselines
        assert "efficiency_pct" in baselines
        assert "temperature_c" in baselines
        
        # Other plants have insufficient data but shouldn't cause errors
        assert len(result.errors) == 0

    def test_pipeline_anomaly_summary(self, pipeline, test_data_path):
        """Test anomaly summary generation."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file)
        summary = pipeline.get_anomaly_summary(result)

        assert "total_anomalies" in summary
        assert "by_severity" in summary
        assert "by_plant" in summary
        assert summary["total_anomalies"] >= 1
        assert "PLANT_001" in summary["by_plant"]

    def test_pipeline_missing_plants_file(self, pipeline):
        """Test pipeline handles missing plants file."""
        result = pipeline.execute("/nonexistent/plants.csv", "/nonexistent/readings.csv")

        assert result.success is False
        assert len(result.errors) > 0

    def test_pipeline_error_handling(self, pipeline, test_data_path):
        """Test pipeline handles errors gracefully."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        # Execute with invalid metric (should not crash)
        result = pipeline.execute(plants_file, readings_file, metrics=["invalid_metric"])

        # Should have errors for the invalid metric
        assert len(result.errors) > 0 or len(result.warnings) > 0

    def test_pipeline_with_date_gap_filling(self, pipeline, test_data_path):
        """Test pipeline with date gap filling enabled."""
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")

        result = pipeline.execute(plants_file, readings_file, fill_gaps=True)

        assert result.success is True
        # Should still process plants even with gap filling
        assert len(result.readings_by_plant) > 0
