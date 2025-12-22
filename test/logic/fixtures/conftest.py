"""Pytest Configuration and Shared Fixtures for Backend Tests"""
import sys
from pathlib import Path

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
def sample_plant():
    """Fixture: Sample plant for testing."""
    from src.logic.data_models.plant import Plant

    return Plant(
        plant_id="PLANT_001",
        plant_name="Solar Farm Alpha",
        capacity_kw=500.0,
        location="Chennai, India",
        installation_date="2020-01-15",
        equipment_type="Monocrystalline",
        current_health_score=85.0,
        last_analysis_date="2025-12-22",
        anomaly_count_7d=2,
        anomaly_count_30d=8,
    )


@pytest.fixture
def sample_readings():
    """Fixture: Sample daily readings for testing."""
    from datetime import date, timedelta

    from src.logic.data_models.reading import DailyReading

    readings = []
    start_date = date(2025, 1, 1)
    for i in range(365):
        current_date = start_date + timedelta(days=i)
        # Normal distribution around expected values
        readings.append(
            DailyReading(
                plant_id="PLANT_001",
                date=current_date.isoformat(),
                power_output_kwh=450.0 + (i % 100),
                efficiency_pct=18.5 + ((i % 50) / 100),
                temperature_c=35.0 + (i % 20),
                irradiance_w_m2=800.0 + (i % 200),
                inverter_status="OK",
                grid_frequency_hz=50.0,
            )
        )
    return readings


@pytest.fixture
def sample_baseline():
    """Fixture: Sample baseline statistics for testing."""
    from src.logic.data_models.baseline import Baseline

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
def data_factory():
    """Fixture: Factory for creating test data."""

    class DataFactory:
        @staticmethod
        def create_plant(plant_id="PLANT_001", **kwargs):
            from src.logic.data_models.plant import Plant

            defaults = {
                "plant_name": "Test Plant",
                "capacity_kw": 500.0,
                "location": "Test Location",
                "installation_date": "2020-01-01",
                "equipment_type": "Monocrystalline",
                "current_health_score": 85.0,
                "last_analysis_date": "2025-12-22",
                "anomaly_count_7d": 0,
                "anomaly_count_30d": 0,
            }
            defaults.update(kwargs)
            return Plant(plant_id=plant_id, **defaults)

        @staticmethod
        def create_reading(plant_id="PLANT_001", date="2025-01-01", **kwargs):
            from src.logic.data_models.reading import DailyReading

            defaults = {
                "power_output_kwh": 450.0,
                "efficiency_pct": 18.5,
                "temperature_c": 35.0,
                "irradiance_w_m2": 800.0,
                "inverter_status": "OK",
                "grid_frequency_hz": 50.0,
            }
            defaults.update(kwargs)
            return DailyReading(plant_id=plant_id, date=date, **defaults)

    return DataFactory()
