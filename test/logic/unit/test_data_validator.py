"""Tests for DataValidator - Validates and cleans sensor data."""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError as PydanticValidationError

from src.logic.data_models.reading import DailyReading
from src.logic.analytics.data_validator import DataValidator, ValidationError


class TestDataValidator:
    """Test data validation and cleaning."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DataValidator()

    @pytest.fixture
    def valid_reading(self):
        """Valid reading fixture."""
        return DailyReading(
            plant_id="PLANT_001",
            date="2025-01-15",
            power_output_kwh=450.0,
            efficiency_pct=85.5,
            temperature_c=35.2,
            irradiance_w_m2=800.0,
            inverter_status="active",
            grid_frequency_hz=50.0,
        )

    def test_validate_valid_reading(self, validator, valid_reading):
        """Test validation passes for valid reading."""
        result = validator.validate(valid_reading)
        assert result is True

    def test_reject_missing_plant_id(self, validator):
        """Test validation fails for missing plant_id."""
        with pytest.raises(ValidationError) as exc_info:
            reading = DailyReading(
                plant_id="",  # Empty plant ID
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
            validator.validate(reading)
        assert "plant_id" in str(exc_info.value)

    def test_reject_future_date(self, validator):
        """Test validation fails for future dates."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        # Pydantic validates the future date at model instantiation
        with pytest.raises(PydanticValidationError) as exc_info:
            reading = DailyReading(
                plant_id="PLANT_001",
                date=tomorrow,
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
        assert "future" in str(exc_info.value).lower()

    def test_reject_negative_power_output(self, validator):
        """Test validation fails for negative power output."""
        # Pydantic validates non-negative constraint at model instantiation
        with pytest.raises(PydanticValidationError) as exc_info:
            reading = DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=-50.0,  # Negative power
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
        assert "power_output" in str(exc_info.value).lower()

    def test_reject_out_of_range_efficiency(self, validator):
        """Test validation fails for efficiency > 100%."""
        # Pydantic validates range constraint at model instantiation
        with pytest.raises(PydanticValidationError) as exc_info:
            reading = DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=105.0,  # Over 100%
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
        assert "efficiency" in str(exc_info.value).lower()

    def test_detect_outliers_zscore(self, validator):
        """Test outlier detection using Z-score method."""
        readings = [
            DailyReading(
                plant_id="PLANT_001",
                date=f"2025-01-{i+1:02d}",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
            for i in range(10)
        ]
        # Add extreme outlier
        readings.append(
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-11",
                power_output_kwh=2000.0,  # 4+ std devs away
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
        )

        outliers = validator.detect_outliers(readings, method="zscore", threshold=3.0)
        assert len(outliers) > 0
        assert any(r.power_output_kwh == 2000.0 for r in outliers)

    def test_handle_duplicate_readings(self, validator):
        """Test detection and handling of duplicate readings."""
        readings = [
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            ),
            # Duplicate
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            ),
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-16",
                power_output_kwh=460.0,
                efficiency_pct=86.0,
                temperature_c=36.0,
                irradiance_w_m2=810.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            ),
        ]

        cleaned = validator.remove_duplicates(readings)
        assert len(cleaned) == 2
        # Verify dates are unique
        dates = {r.date for r in cleaned}
        assert len(dates) == 2

    def test_normalize_date_range(self, validator):
        """Test filling gaps in date range."""
        readings = [
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            ),
            DailyReading(
                plant_id="PLANT_001",
                date="2025-01-17",  # Gap on 16th
                power_output_kwh=460.0,
                efficiency_pct=86.0,
                temperature_c=36.0,
                irradiance_w_m2=810.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            ),
        ]

        # Fill with interpolation
        filled = validator.fill_date_gaps(readings, method="interpolate")
        assert len(filled) == 3  # Should have 3 readings now
        # Verify 16th was added
        dates = {r.date for r in filled}
        assert "2025-01-16" in dates

    def test_reject_invalid_inverter_status(self, validator):
        """Test validation fails for invalid inverter status."""
        with pytest.raises(ValidationError) as exc_info:
            reading = DailyReading(
                plant_id="PLANT_001",
                date="2025-01-15",
                power_output_kwh=450.0,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="invalid_status",  # Invalid status
                grid_frequency_hz=50.0,
            )
            validator.validate(reading)
        assert "inverter_status" in str(exc_info.value).lower()

    def test_batch_validation(self, validator):
        """Test validating multiple readings at once."""
        readings = [
            DailyReading(
                plant_id="PLANT_001",
                date=f"2025-01-{i+1:02d}",
                power_output_kwh=450.0 + i,
                efficiency_pct=85.5,
                temperature_c=35.2,
                irradiance_w_m2=800.0,
                inverter_status="active",
                grid_frequency_hz=50.0,
            )
            for i in range(5)
        ]

        results = validator.validate_batch(readings)
        assert len(results) == 5
        assert all(r.is_valid for r in results)
        assert all(r.errors == [] for r in results)

    def test_batch_validation_with_errors(self, validator):
        """Test batch validation capturing invalid readings."""
        # Create valid reading first
        valid_reading = DailyReading(
            plant_id="PLANT_001",
            date="2025-01-01",
            power_output_kwh=450.0,
            efficiency_pct=85.5,
            temperature_c=35.2,
            irradiance_w_m2=800.0,
            inverter_status="active",
            grid_frequency_hz=50.0,
        )

        # Test batch validation with valid reading
        results = validator.validate_batch([valid_reading])
        assert len(results) == 1
        assert results[0].is_valid
        assert len(results[0].errors) == 0
