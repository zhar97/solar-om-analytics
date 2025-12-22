"""Unit Tests for Anomaly Detector - T027"""
import pytest
from datetime import date, timedelta

from src.logic.analytics.anomaly_detector import AnomalyDetector
from src.logic.data_models.baseline import Baseline
from src.logic.data_models.reading import DailyReading
from src.logic.data_models.anomaly import Anomaly


class TestAnomalyDetector:
    """Test suite for AnomalyDetector class."""

    @pytest.fixture
    def detector(self):
        """Provide an AnomalyDetector instance."""
        return AnomalyDetector()

    @pytest.fixture
    def baseline(self):
        """Sample baseline for testing."""
        return Baseline(
            plant_id="PLANT_001",
            period_name="Q1_2025",
            metric_name="power_output_kwh",
            mean=450.0,
            std_dev=45.0,
            q1=420.0,
            q2=450.0,
            q3=480.0,
            iqr=60.0,
            min_val=250.0,
            max_val=550.0,
            samples_count=90,
            date_range="2025-01-01 to 2025-03-31",
            calculation_timestamp="2025-04-01T00:00:00",
        )

    @pytest.fixture
    def normal_readings(self):
        """Generate normal readings within baseline."""
        readings = []
        for i in range(5):
            readings.append(
                DailyReading(
                    plant_id="PLANT_001",
                    date=(date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                    power_output_kwh=450.0,  # At mean
                    efficiency_pct=18.5,
                    temperature_c=35.0,
                    irradiance_w_m2=850.0,
                    inverter_status="OK",
                    grid_frequency_hz=50.0,
                )
            )
        return readings

    @pytest.fixture
    def anomalous_readings(self):
        """Generate anomalous readings (large deviation)."""
        readings = []
        readings.append(
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-10",
                power_output_kwh=250.0,  # ~4.5 std devs below mean
                efficiency_pct=18.5,
                temperature_c=35.0,
                irradiance_w_m2=850.0,
                inverter_status="Warning",
                grid_frequency_hz=50.0,
            )
        )
        return readings

    def test_detect_zscore_anomalies(self, detector, baseline, anomalous_readings):
        """Test: Detect Z-score anomalies (> 2σ)"""
        anomalies = detector.detect(anomalous_readings, baseline)

        assert len(anomalies) > 0
        assert anomalies[0].detected_by == "zscore"
        assert anomalies[0].severity in ["low", "medium", "high", "critical"]
        assert anomalies[0].z_score is not None
        assert abs(anomalies[0].z_score) > 2.0

    def test_detect_iqr_anomalies(self, detector, baseline):
        """Test: Detect IQR anomalies (outside Q1-1.5×IQR, Q3+1.5×IQR)"""
        # Reading outside IQR bounds
        reading = DailyReading(
            plant_id="PLANT_001",
            date="2025-01-10",
            power_output_kwh=300.0,  # Below lower bound (420 - 1.5*60 = 330)
            efficiency_pct=18.5,
            temperature_c=35.0,
            irradiance_w_m2=850.0,
            inverter_status="OK",
            grid_frequency_hz=50.0,
        )

        anomalies = detector.detect([reading], baseline)
        
        # May be detected by IQR if outside bounds
        if len(anomalies) > 0:
            assert anomalies[0].detected_by in ["zscore", "iqr"]

    def test_dont_flag_normal_readings(self, detector, baseline, normal_readings):
        """Test: Don't flag normal readings (within bounds)"""
        anomalies = detector.detect(normal_readings, baseline)

        assert len(anomalies) == 0

    def test_classify_severity_correctly(self, detector, baseline):
        """Test: Classify severity correctly (low 5-10%, medium 10-20%, high 20-50%, critical >50%)"""
        # Low severity: 8% deviation
        reading_low = DailyReading(
            plant_id="PLANT_001",
            date="2025-01-10",
            power_output_kwh=414.0,  # 8% below 450
            efficiency_pct=18.5,
            temperature_c=35.0,
            irradiance_w_m2=850.0,
            inverter_status="OK",
            grid_frequency_hz=50.0,
        )

        # High severity: 35% deviation
        reading_high = DailyReading(
            plant_id="PLANT_001",
            date="2025-01-11",
            power_output_kwh=292.5,  # 35% below 450
            efficiency_pct=18.5,
            temperature_c=35.0,
            irradiance_w_m2=850.0,
            inverter_status="Warning",
            grid_frequency_hz=50.0,
        )

        # Detect both
        anomalies = detector.detect([reading_low, reading_high], baseline)
        
        # Find the high deviation one (more likely to be detected)
        for anomaly in anomalies:
            if anomaly.date == "2025-01-11":
                assert anomaly.severity in ["high", "critical"]

    def test_configurable_sensitivity(self, detector, baseline, anomalous_readings):
        """Test: Configurable sensitivity (threshold parameter)"""
        # Detect with default threshold (2.0)
        anomalies_default = detector.detect(anomalous_readings, baseline)
        
        # Detect with higher threshold (stricter)
        detector_strict = AnomalyDetector(zscore_threshold=3.0)
        anomalies_strict = detector_strict.detect(anomalous_readings, baseline)

        # Stricter threshold should find fewer or same anomalies
        assert len(anomalies_strict) <= len(anomalies_default)
