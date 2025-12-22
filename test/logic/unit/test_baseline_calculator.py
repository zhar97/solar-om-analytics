"""Unit Tests for Baseline Calculator - T025"""
import pytest
from datetime import date, timedelta
import numpy as np

from src.logic.analytics.baseline_calculator import BaselineCalculator
from src.logic.data_models.baseline import Baseline
from src.logic.data_models.reading import DailyReading


class TestBaselineCalculator:
    """Test suite for BaselineCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Provide a BaselineCalculator instance."""
        return BaselineCalculator()

    @pytest.fixture
    def sample_readings_90_days(self):
        """Generate 90 days of readings for baseline calculation."""
        readings = []
        start_date = date(2025, 1, 1)
        mean_value = 450.0
        std_dev = 45.0

        for i in range(90):
            current_date = start_date + timedelta(days=i)
            # Generate normally distributed values
            value = np.random.normal(mean_value, std_dev)
            readings.append(
                DailyReading(
                    plant_id="PLANT_001",
                    date=current_date.isoformat(),
                    power_output_kwh=max(0, value),  # Ensure non-negative
                    efficiency_pct=18.5,
                    temperature_c=35.0,
                    irradiance_w_m2=850.0,
                    inverter_status="OK",
                    grid_frequency_hz=50.0,
                )
            )
        return readings

    def test_calculate_baseline_valid_readings(self, calculator, sample_readings_90_days):
        """Test: Calculate baseline from readings -> Baseline with correct mean, std_dev, quartiles"""
        baseline = calculator.calculate(sample_readings_90_days, "PLANT_001", "power_output_kwh")

        assert baseline.plant_id == "PLANT_001"
        assert baseline.metric_name == "power_output_kwh"
        assert baseline.samples_count == 90
        assert baseline.mean > 0
        assert baseline.std_dev >= 0
        assert baseline.q1 < baseline.q2 < baseline.q3
        assert baseline.min_val <= baseline.q1
        assert baseline.max_val >= baseline.q3

    def test_calculate_baseline_insufficient_data(self, calculator):
        """Test: Require >= 3 months data -> reject if insufficient"""
        # Only 10 days of data
        readings = []
        for i in range(10):
            readings.append(
                DailyReading(
                    plant_id="PLANT_001",
                    date=(date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                    power_output_kwh=450.0,
                    efficiency_pct=18.5,
                    temperature_c=35.0,
                    irradiance_w_m2=850.0,
                    inverter_status="OK",
                    grid_frequency_hz=50.0,
                )
            )

        with pytest.raises(ValueError):
            calculator.calculate(readings, "PLANT_001", "power_output_kwh")

    def test_calculate_baseline_quartile_order(self, calculator, sample_readings_90_days):
        """Test: Validate quartile order min <= q1 <= q2 <= q3 <= max"""
        baseline = calculator.calculate(sample_readings_90_days, "PLANT_001", "power_output_kwh")

        assert baseline.min_val <= baseline.q1, "min should be <= q1"
        assert baseline.q1 <= baseline.q2, "q1 should be <= q2"
        assert baseline.q2 <= baseline.q3, "q2 should be <= q3"
        assert baseline.q3 <= baseline.max_val, "q3 should be <= max"

    def test_calculate_different_metrics(self, calculator, sample_readings_90_days):
        """Test: Handle single metric calculation (power_output_kwh, efficiency_pct, etc.)"""
        baseline_power = calculator.calculate(
            sample_readings_90_days, "PLANT_001", "power_output_kwh"
        )
        baseline_efficiency = calculator.calculate(
            sample_readings_90_days, "PLANT_001", "efficiency_pct"
        )

        assert baseline_power.metric_name == "power_output_kwh"
        assert baseline_efficiency.metric_name == "efficiency_pct"
        assert baseline_power.mean != baseline_efficiency.mean
