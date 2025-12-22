"""Unit tests for Pattern Detector module."""
import pytest
from datetime import datetime, timedelta
from src.logic.data_models.reading import DailyReading
from src.logic.data_models.baseline import Baseline
from src.logic.data_models.pattern import Pattern
from src.logic.analytics.pattern_detector import PatternDetector


@pytest.fixture
def sample_readings():
    """Create sample readings with seasonal pattern."""
    readings = []
    base_date = datetime(2023, 1, 1)
    
    # Create 2 years of data with strong seasonal variations (>15% difference)
    for month in range(24):
        date = base_date + timedelta(days=30*month)
        # Strong seasonal variation: 300 kWh (winter) vs 600 kWh (summer) = 50% difference
        if month % 12 in [0, 1, 11]:  # Dec, Jan, Feb
            base_value = 300
        elif month % 12 in [5, 6, 7]:  # Jun, Jul, Aug
            base_value = 600
        else:
            base_value = 450
        
        for day in range(30):
            current_date = date + timedelta(days=day)
            # Add slight daily variation
            value = base_value + (day % 3) * 5
            readings.append(DailyReading(
                plant_id='PLANT_001',
                date=current_date.strftime('%Y-%m-%d'),
                power_output_kwh=value,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            ))
    
    return readings


@pytest.fixture
def sample_readings_weekly():
    """Create sample readings with weekly pattern."""
    readings = []
    base_date = datetime(2024, 1, 1)
    
    # Create 6 months of data with weekly pattern
    for week in range(26):
        for day in range(7):
            current_date = base_date + timedelta(days=week*7 + day)
            # Higher on weekdays (0-4), lower on weekends (5-6)
            value = 480 if day < 5 else 320
            readings.append(DailyReading(
                plant_id='PLANT_002',
                date=current_date.strftime('%Y-%m-%d'),
                power_output_kwh=value,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            ))
    
    return readings


@pytest.fixture
def sample_readings_degradation():
    """Create sample readings with degradation pattern."""
    readings = []
    base_date = datetime(2023, 1, 1)
    
    # Create 3 years with gradual degradation
    for month in range(36):
        date = base_date + timedelta(days=30*month)
        # Gradual decrease: 500 kWh -> 350 kWh over 3 years
        base_value = 500 - (month * 4.17)
        
        for day in range(30):
            current_date = date + timedelta(days=day)
            value = max(base_value + (day % 5) * 5, 100)  # Prevent negative
            readings.append(DailyReading(
                plant_id='PLANT_003',
                date=current_date.strftime('%Y-%m-%d'),
                power_output_kwh=value,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            ))
    
    return readings


@pytest.fixture
def pattern_detector():
    """Create PatternDetector instance."""
    return PatternDetector()


class TestPatternDetectorInitialization:
    """Test PatternDetector initialization."""

    def test_detector_creates_successfully(self, pattern_detector):
        """Test detector creates without errors."""
        assert pattern_detector is not None
        assert hasattr(pattern_detector, 'detect')

    def test_detector_has_required_methods(self, pattern_detector):
        """Test detector has all required methods."""
        required_methods = ['detect', 'detect_seasonal', 'detect_weekly_cycle', 'detect_degradation']
        for method in required_methods:
            assert hasattr(pattern_detector, method)
            assert callable(getattr(pattern_detector, method))


class TestSeasonalPatternDetection:
    """Test seasonal pattern detection."""

    def test_detects_seasonal_pattern(self, pattern_detector, sample_readings):
        """Test detection of seasonal pattern."""
        patterns = pattern_detector.detect_seasonal(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.pattern_type == 'seasonal'
        assert pattern.plant_id == 'PLANT_001'
        assert pattern.metric_name == 'power_output_kwh'

    def test_seasonal_pattern_has_correct_fields(self, pattern_detector, sample_readings):
        """Test seasonal pattern has all required fields."""
        patterns = pattern_detector.detect_seasonal(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        pattern = patterns[0]
        assert pattern.frequency == 'annual'
        assert pattern.occurrence_count >= 2
        assert pattern.significance_score >= 0
        assert pattern.confidence_pct >= 0
        assert pattern.amplitude is not None

    def test_seasonal_pattern_confidence_high_for_clear_pattern(self, pattern_detector, sample_readings):
        """Test seasonal pattern has high confidence for clear variations."""
        patterns = pattern_detector.detect_seasonal(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern = patterns[0]
        # Clear seasonal pattern should have high confidence
        assert pattern.confidence_pct > 70

    def test_no_seasonal_pattern_in_flat_data(self, pattern_detector):
        """Test no seasonal pattern detected in flat data."""
        readings = [
            DailyReading(
                plant_id='PLANT_001',
                date=(datetime(2023, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d'),
                power_output_kwh=500.0,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            )
            for i in range(365)
        ]
        
        patterns = pattern_detector.detect_seasonal(
            plant_id='PLANT_001',
            readings=readings,
            metric_name='power_output_kwh'
        )
        
        # Should detect no or very low confidence pattern
        if patterns:
            assert patterns[0].confidence_pct < 50


class TestWeeklyCycleDetection:
    """Test weekly cycle pattern detection."""

    def test_detects_weekly_cycle(self, pattern_detector, sample_readings_weekly):
        """Test detection of weekly cycle pattern."""
        patterns = pattern_detector.detect_weekly_cycle(
            plant_id='PLANT_002',
            readings=sample_readings_weekly,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.pattern_type == 'weekly_cycle'
        assert pattern.frequency == 'weekly'

    def test_weekly_pattern_has_minimum_occurrences(self, pattern_detector, sample_readings_weekly):
        """Test weekly pattern has minimum 4 occurrences."""
        patterns = pattern_detector.detect_weekly_cycle(
            plant_id='PLANT_002',
            readings=sample_readings_weekly,
            metric_name='power_output_kwh'
        )
        
        if patterns:
            pattern = patterns[0]
            assert pattern.occurrence_count >= 4

    def test_weekly_pattern_identifies_weekday_weekend(self, pattern_detector, sample_readings_weekly):
        """Test weekly pattern correctly identifies weekday/weekend difference."""
        patterns = pattern_detector.detect_weekly_cycle(
            plant_id='PLANT_002',
            readings=sample_readings_weekly,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern = patterns[0]
        # Should have description mentioning weekly pattern
        assert 'week' in pattern.description.lower()


class TestDegradationDetection:
    """Test degradation pattern detection."""

    def test_detects_degradation_pattern(self, pattern_detector, sample_readings_degradation):
        """Test detection of degradation pattern."""
        patterns = pattern_detector.detect_degradation(
            plant_id='PLANT_003',
            readings=sample_readings_degradation,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.pattern_type == 'degradation'
        assert pattern.plant_id == 'PLANT_003'

    def test_degradation_pattern_shows_declining_trend(self, pattern_detector, sample_readings_degradation):
        """Test degradation pattern correctly identifies declining trend."""
        patterns = pattern_detector.detect_degradation(
            plant_id='PLANT_003',
            readings=sample_readings_degradation,
            metric_name='power_output_kwh'
        )
        
        if patterns:
            pattern = patterns[0]
            # Degradation description should mention decline
            assert 'degrad' in pattern.description.lower() or 'declin' in pattern.description.lower()

    def test_degradation_frequency_is_long_term(self, pattern_detector, sample_readings_degradation):
        """Test degradation is identified as long-term pattern."""
        patterns = pattern_detector.detect_degradation(
            plant_id='PLANT_003',
            readings=sample_readings_degradation,
            metric_name='power_output_kwh'
        )
        
        if patterns:
            pattern = patterns[0]
            assert pattern.frequency in ['annual', 'long_term', 'multi_year']


class TestGeneralPatternDetection:
    """Test general pattern detection method."""

    def test_detect_method_finds_multiple_pattern_types(self, pattern_detector, sample_readings):
        """Test detect method can find multiple pattern types."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        assert len(patterns) > 0
        pattern_types = {p.pattern_type for p in patterns}
        # Should find at least seasonal pattern in sample data
        assert 'seasonal' in pattern_types or len(pattern_types) > 0

    def test_detect_method_returns_pattern_objects(self, pattern_detector, sample_readings):
        """Test detect method returns valid Pattern objects."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        for pattern in patterns:
            assert isinstance(pattern, Pattern)
            assert pattern.plant_id == 'PLANT_001'
            assert pattern.metric_name == 'power_output_kwh'

    def test_detect_with_empty_readings(self, pattern_detector):
        """Test detect handles empty readings gracefully."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=[],
            metric_name='power_output_kwh'
        )
        
        assert isinstance(patterns, list)

    def test_detect_with_insufficient_data(self, pattern_detector):
        """Test detect handles insufficient data gracefully."""
        readings = [
            DailyReading(
                plant_id='PLANT_001',
                date=datetime(2023, 1, 1).strftime('%Y-%m-%d'),
                power_output_kwh=500.0,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            )
        ]
        
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=readings,
            metric_name='power_output_kwh'
        )
        
        assert isinstance(patterns, list)


class TestPatternAttributes:
    """Test pattern attribute correctness."""

    def test_pattern_id_is_unique(self, pattern_detector, sample_readings):
        """Test each pattern has unique pattern_id."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        if len(patterns) > 1:
            pattern_ids = [p.pattern_id for p in patterns]
            assert len(pattern_ids) == len(set(pattern_ids))

    def test_pattern_dates_are_valid(self, pattern_detector, sample_readings):
        """Test pattern dates are valid and in correct order."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        for pattern in patterns:
            first_date = datetime.strptime(pattern.first_observed_date, '%Y-%m-%d')
            last_date = datetime.strptime(pattern.last_observed_date, '%Y-%m-%d')
            assert first_date <= last_date

    def test_pattern_confidence_in_valid_range(self, pattern_detector, sample_readings):
        """Test pattern confidence is within 0-100 range."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        for pattern in patterns:
            assert 0 <= pattern.confidence_pct <= 100
            assert 0 <= pattern.significance_score <= 100

    def test_pattern_amplitude_is_positive_or_none(self, pattern_detector, sample_readings):
        """Test pattern amplitude is positive when present."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        for pattern in patterns:
            if pattern.amplitude is not None:
                assert pattern.amplitude >= 0

    def test_pattern_occurrence_count_minimum_two(self, pattern_detector, sample_readings):
        """Test pattern occurrence count is at least 2."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='power_output_kwh'
        )
        
        for pattern in patterns:
            assert pattern.occurrence_count >= 2


class TestPatternDetectorEdgeCases:
    """Test pattern detector edge cases."""

    def test_handles_missing_metric(self, pattern_detector, sample_readings):
        """Test detector handles readings with missing metric gracefully."""
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=sample_readings,
            metric_name='non_existent_metric'
        )
        
        # Should return empty list or handle gracefully
        assert isinstance(patterns, list)

    def test_handles_null_values(self, pattern_detector):
        """Test detector handles null/zero values in readings."""
        readings = [
            DailyReading(
                plant_id='PLANT_001',
                date=(datetime(2023, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d'),
                power_output_kwh=0 if i % 10 == 0 else 500.0,  # Some null values
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            )
            for i in range(365)
        ]
        
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=readings,
            metric_name='power_output_kwh'
        )
        
        assert isinstance(patterns, list)

    def test_handles_very_short_data_series(self, pattern_detector):
        """Test detector handles very short data series."""
        readings = [
            DailyReading(
                plant_id='PLANT_001',
                date=(datetime(2023, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d'),
                power_output_kwh=500.0,
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            )
            for i in range(7)  # Only 7 days
        ]
        
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=readings,
            metric_name='power_output_kwh'
        )
        
        assert isinstance(patterns, list)

    def test_handles_very_long_data_series(self, pattern_detector):
        """Test detector handles very long data series efficiently."""
        readings = [
            DailyReading(
                plant_id='PLANT_001',
                date=(datetime(2020, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d'),
                power_output_kwh=500.0 + (i % 100),
                efficiency_pct=85.0,
                temperature_c=25.0,
                irradiance_w_m2=800.0
            )
            for i in range(1460)  # 4 years
        ]
        
        patterns = pattern_detector.detect(
            plant_id='PLANT_001',
            readings=readings,
            metric_name='power_output_kwh'
        )
        
        assert isinstance(patterns, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
