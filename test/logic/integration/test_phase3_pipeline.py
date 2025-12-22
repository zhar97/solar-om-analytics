"""Integration tests for Phase 3 - CSV → Baseline → Anomalies pipeline."""
import pytest
from pathlib import Path

from src.logic.ingestion.csv_loader import CsvLoader
from src.logic.analytics.baseline_calculator import BaselineCalculator
from src.logic.analytics.anomaly_detector import AnomalyDetector
from src.logic.analytics.data_validator import DataValidator


class TestPhase3Pipeline:
    """Test end-to-end anomaly detection pipeline."""

    @pytest.fixture
    def test_data_path(self):
        """Path to test data files."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def csv_loader(self):
        """CSV loader instance."""
        return CsvLoader()

    @pytest.fixture
    def validator(self):
        """Data validator instance."""
        return DataValidator()

    @pytest.fixture
    def baseline_calculator(self):
        """Baseline calculator instance."""
        return BaselineCalculator()

    @pytest.fixture
    def anomaly_detector(self):
        """Anomaly detector instance."""
        return AnomalyDetector()

    def test_full_pipeline_csv_to_anomalies(
        self,
        test_data_path,
        csv_loader,
        validator,
        baseline_calculator,
        anomaly_detector,
    ):
        """Test complete pipeline: load CSV → validate → calculate baseline → detect anomalies."""
        plants_file = test_data_path / "sample_plants.csv"
        readings_file = test_data_path / "sample_readings.csv"

        # Step 1: Load data from CSV
        assert plants_file.exists(), f"Plants file not found: {plants_file}"
        assert readings_file.exists(), f"Readings file not found: {readings_file}"

        plants = csv_loader.load_plants(str(plants_file))
        readings_dict = csv_loader.load_readings(str(readings_file))

        assert len(plants) > 0, "No plants loaded"
        assert len(readings_dict) > 0, "No readings loaded"

        # Step 2: Get readings for first plant
        first_plant_id = list(plants.keys())[0]
        plant = plants[first_plant_id]
        readings = readings_dict.get(first_plant_id, [])

        assert len(readings) > 0, f"No readings found for plant {first_plant_id}"

        # Step 3: Validate readings
        validation_results = validator.validate_batch(readings)
        valid_readings = [readings[i] for i, r in enumerate(validation_results) if r.is_valid]

        assert len(valid_readings) > 0, "No valid readings after validation"

        # Step 4: Remove duplicates
        unique_readings = validator.remove_duplicates(valid_readings)
        assert len(unique_readings) > 0, "No unique readings after deduplication"

        # Step 5: Calculate baseline
        baseline = baseline_calculator.calculate(
            unique_readings,
            plant_id=first_plant_id,
            metric="power_output_kwh"
        )

        assert baseline is not None, "Baseline calculation failed"
        assert baseline.mean > 0, "Baseline mean should be positive"
        assert baseline.std_dev >= 0, "Baseline std_dev should be non-negative"
        assert baseline.q1 <= baseline.q2 <= baseline.q3, "Quartiles should be ordered"

        # Step 6: Detect anomalies
        anomalies = anomaly_detector.detect(unique_readings, baseline)

        # Verify we detected at least 1 anomaly (sample_readings.csv has 1 anomalous reading)
        assert len(anomalies) >= 1, "Should detect at least 1 anomaly in test data"

        # Verify anomaly attributes
        for anomaly in anomalies:
            assert anomaly.plant_id == first_plant_id
            assert anomaly.detected_by in ["zscore", "iqr"]
            assert anomaly.severity in ["low", "medium", "high", "critical"]
            assert anomaly.status == "open"

    def test_pipeline_data_quality(
        self,
        test_data_path,
        csv_loader,
        validator,
    ):
        """Test data quality checks in pipeline."""
        readings_file = test_data_path / "sample_readings.csv"
        csv_loader = CsvLoader()
        readings_dict = csv_loader.load_readings(str(readings_file))

        all_readings = []
        for readings in readings_dict.values():
            all_readings.extend(readings)

        # Test outlier detection
        outliers = validator.detect_outliers(all_readings, method="zscore", threshold=2.0)
        # Should detect at least 1 outlier (the anomalous reading)
        assert len(outliers) >= 1, "Should detect outliers in test data"

        # Test duplicate handling
        duplicates_removed = validator.remove_duplicates(all_readings)
        assert len(duplicates_removed) <= len(all_readings), "Deduplication should not increase count"

    def test_pipeline_with_date_gaps(
        self,
        csv_loader,
        validator,
        baseline_calculator,
        test_data_path,
    ):
        """Test pipeline with date gap filling."""
        readings_file = test_data_path / "sample_readings.csv"
        readings_dict = csv_loader.load_readings(str(readings_file))

        first_plant_id = list(readings_dict.keys())[0]
        readings = readings_dict[first_plant_id]

        # Fill date gaps
        filled_readings = validator.fill_date_gaps(readings, method="interpolate")

        # Verify readings are continuous
        if len(filled_readings) > 1:
            assert len(filled_readings) >= len(readings), "Gap filling should not reduce readings"

        # Calculate baseline on filled data
        baseline = baseline_calculator.calculate(
            filled_readings,
            plant_id=first_plant_id,
            metric="power_output_kwh"
        )
        assert baseline is not None, "Baseline calculation on filled data should succeed"

    def test_pipeline_batch_processing(
        self,
        test_data_path,
        csv_loader,
        validator,
        baseline_calculator,
        anomaly_detector,
    ):
        """Test pipeline processing multiple plants."""
        plants_file = test_data_path / "sample_plants.csv"
        readings_file = test_data_path / "sample_readings.csv"

        plants = csv_loader.load_plants(str(plants_file))
        readings_dict = csv_loader.load_readings(str(readings_file))

        assert len(plants) >= 2, "Test data should have at least 2 plants"

        # Process each plant
        all_anomalies = []
        processed_count = 0
        
        for plant_id in plants:
            readings = readings_dict.get(plant_id, [])
            if not readings:
                continue

            # Validate and deduplicate
            validation_results = validator.validate_batch(readings)
            valid_readings = [readings[i] for i, r in enumerate(validation_results) if r.is_valid]
            unique_readings = validator.remove_duplicates(valid_readings)

            # Skip plants with insufficient data (< 13 readings required)
            if len(unique_readings) < 13:
                continue
            
            processed_count += 1

            # Calculate baseline and detect anomalies
            baseline = baseline_calculator.calculate(
                unique_readings,
                plant_id=plant_id,
                metric="power_output_kwh"
            )
            anomalies = anomaly_detector.detect(unique_readings, baseline)
            all_anomalies.extend(anomalies)

        # Verify we processed at least 1 plant
        assert processed_count >= 1, "Should process at least 1 plant with sufficient data"
        # Verify aggregated results
        assert len(all_anomalies) >= 1, "Should detect anomalies from processed plants"

        # Verify anomalies cover at least 1 plant
        anomaly_plants = {a.plant_id for a in all_anomalies}
        assert len(anomaly_plants) >= 1, "Should have anomalies from at least 1 plant"
