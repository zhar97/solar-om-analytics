"""Pattern Detector - Detects recurring patterns in time-series data."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict
import numpy as np
from src.logic.data_models.reading import DailyReading
from src.logic.data_models.pattern import Pattern

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects recurring patterns in solar energy data."""

    def __init__(self, min_occurrences: int = 2, confidence_threshold: float = 0.6):
        """Initialize PatternDetector.
        
        Args:
            min_occurrences: Minimum number of occurrences to consider as pattern
            confidence_threshold: Minimum confidence threshold (0-1) for pattern detection
        """
        self.min_occurrences = min_occurrences
        self.confidence_threshold = confidence_threshold
        self.pattern_counter = 0

    def detect(
        self,
        plant_id: str,
        readings: List[DailyReading],
        metric_name: str
    ) -> List[Pattern]:
        """Detect all types of patterns in readings.
        
        Args:
            plant_id: Plant identifier
            readings: List of daily readings
            metric_name: Metric to analyze (e.g., 'power_output_kwh')
            
        Returns:
            List of detected Pattern objects
        """
        if not readings:
            logger.warning(f"No readings provided for {plant_id}")
            return []
        
        if len(readings) < 30:
            logger.info(f"Insufficient data for pattern detection: {len(readings)} readings")
            return []
        
        patterns = []
        
        # Detect different pattern types
        try:
            seasonal_patterns = self.detect_seasonal(plant_id, readings, metric_name)
            patterns.extend(seasonal_patterns)
        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")
        
        try:
            weekly_patterns = self.detect_weekly_cycle(plant_id, readings, metric_name)
            patterns.extend(weekly_patterns)
        except Exception as e:
            logger.error(f"Error detecting weekly patterns: {e}")
        
        try:
            degradation_patterns = self.detect_degradation(plant_id, readings, metric_name)
            patterns.extend(degradation_patterns)
        except Exception as e:
            logger.error(f"Error detecting degradation patterns: {e}")
        
        logger.info(f"Detected {len(patterns)} patterns for {plant_id}")
        return patterns

    def detect_seasonal(
        self,
        plant_id: str,
        readings: List[DailyReading],
        metric_name: str
    ) -> List[Pattern]:
        """Detect seasonal patterns.
        
        Args:
            plant_id: Plant identifier
            readings: List of daily readings
            metric_name: Metric to analyze (e.g., 'power_output_kwh')
            
        Returns:
            List of seasonal Pattern objects
        """
        patterns = []
        
        if len(readings) < 365:
            return patterns
        
        # Group readings by month
        monthly_values = defaultdict(list)
        
        for reading in readings:
            try:
                date = datetime.strptime(reading.date, '%Y-%m-%d')
                month = date.month
                # Extract metric value from reading
                value = reading.power_output_kwh
                monthly_values[month].append(value)
            except (ValueError, AttributeError):
                continue
        
        if len(monthly_values) < 12:
            return patterns
        
        # Calculate monthly statistics
        monthly_means = {}
        for month, values in monthly_values.items():
            if values:
                monthly_means[month] = np.mean(values)
        
        # Check for seasonal variation
        overall_mean = np.mean([v for v in monthly_means.values()])
        monthly_deviations = [
            abs(mean - overall_mean) / overall_mean * 100
            for mean in monthly_means.values()
        ]
        
        avg_deviation = np.mean(monthly_deviations)
        std_deviation = np.std(monthly_deviations)
        
        # Seasonal pattern if variation is significant (>15%)
        if avg_deviation > 15:
            # Count complete years
            first_date = datetime.strptime(readings[0].date, '%Y-%m-%d')
            last_date = datetime.strptime(readings[-1].date, '%Y-%m-%d')
            years = (last_date - first_date).days / 365.25
            occurrence_count = max(int(years), 2)
            
            # Calculate confidence based on consistency
            confidence = min(100, 70 + (std_deviation * 2))
            
            # Identify which months have highest/lowest values
            sorted_months = sorted(monthly_means.items(), key=lambda x: x[1])
            lowest_month = sorted_months[0][0]
            highest_month = sorted_months[-1][0]
            
            month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            pattern = Pattern(
                pattern_id=self._generate_pattern_id('seasonal'),
                plant_id=plant_id,
                pattern_type='seasonal',
                metric_name=metric_name,
                description=f"Seasonal variation: Higher in {month_names[highest_month]}, "
                           f"lower in {month_names[lowest_month]} (±{avg_deviation:.1f}%)",
                frequency='annual',
                amplitude=monthly_means[highest_month] - monthly_means[lowest_month],
                significance_score=min(100, avg_deviation * 2),
                confidence_pct=confidence,
                first_observed_date=readings[0].date,
                last_observed_date=readings[-1].date,
                occurrence_count=occurrence_count,
                affected_plants=[plant_id],
                is_fleet_wide=False
            )
            
            patterns.append(pattern)
        
        return patterns

    def detect_weekly_cycle(
        self,
        plant_id: str,
        readings: List[DailyReading],
        metric_name: str
    ) -> List[Pattern]:
        """Detect weekly cycle patterns.
        
        Args:
            plant_id: Plant identifier
            readings: List of daily readings
            metric_name: Metric to analyze
            
        Returns:
            List of weekly cycle Pattern objects
        """
        patterns = []
        
        if len(readings) < 60:  # Need at least 8-9 weeks
            return patterns
        
        # Group readings by day of week
        weekday_values = defaultdict(list)
        
        for reading in readings:
            try:
                date = datetime.strptime(reading.date, '%Y-%m-%d')
                weekday = date.weekday()  # 0=Monday, 6=Sunday
                value = reading.power_output_kwh
                weekday_values[weekday].append(value)
            except (ValueError, AttributeError):
                continue
        
        if len(weekday_values) < 7:
            return patterns
        
        # Calculate weekday statistics
        weekday_means = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for weekday in range(7):
            if weekday in weekday_values:
                weekday_means[weekday] = np.mean(weekday_values[weekday])
        
        if not weekday_means:
            return patterns
        
        # Check for significant weekday difference
        overall_mean = np.mean(list(weekday_means.values()))
        weekday_deviations = [
            abs(mean - overall_mean) / overall_mean * 100
            for mean in weekday_means.values()
        ]
        
        avg_deviation = np.mean(weekday_deviations)
        
        # Weekly pattern if variation is significant (>10%)
        if avg_deviation > 10:
            # Count complete weeks
            first_date = datetime.strptime(readings[0].date, '%Y-%m-%d')
            last_date = datetime.strptime(readings[-1].date, '%Y-%m-%d')
            weeks = (last_date - first_date).days / 7
            occurrence_count = max(int(weeks / 4), 4)  # At least 4 complete weeks
            
            # Identify high and low days
            sorted_days = sorted(weekday_means.items(), key=lambda x: x[1])
            low_day = weekday_names[sorted_days[0][0]]
            high_day = weekday_names[sorted_days[-1][0]]
            
            pattern = Pattern(
                pattern_id=self._generate_pattern_id('weekly'),
                plant_id=plant_id,
                pattern_type='weekly_cycle',
                metric_name=metric_name,
                description=f"Weekly cycle: Higher on {high_day}s, lower on {low_day}s "
                           f"(±{avg_deviation:.1f}%)",
                frequency='weekly',
                amplitude=weekday_means[sorted_days[-1][0]] - weekday_means[sorted_days[0][0]],
                significance_score=min(100, avg_deviation * 3),
                confidence_pct=min(100, 60 + avg_deviation * 2),
                first_observed_date=readings[0].date,
                last_observed_date=readings[-1].date,
                occurrence_count=occurrence_count,
                affected_plants=[plant_id],
                is_fleet_wide=False
            )
            
            patterns.append(pattern)
        
        return patterns

    def detect_degradation(
        self,
        plant_id: str,
        readings: List[DailyReading],
        metric_name: str
    ) -> List[Pattern]:
        """Detect degradation patterns (declining performance).
        
        Args:
            plant_id: Plant identifier
            readings: List of daily readings
            metric_name: Metric to analyze
            
        Returns:
            List of degradation Pattern objects
        """
        patterns = []
        
        if len(readings) < 365:  # Need at least 1 year
            return patterns
        
        # Extract values and dates
        values = []
        dates = []
        
        for reading in readings:
            try:
                date = datetime.strptime(reading.date, '%Y-%m-%d')
                dates.append(date)
                value = reading.power_output_kwh
                values.append(value)
            except (ValueError, AttributeError):
                continue
        
        if len(values) < 365:
            return patterns
        
        # Calculate trend using simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Remove NaN values
        valid_idx = ~np.isnan(y)
        x = x[valid_idx]
        y = y[valid_idx]
        
        if len(x) < 365:
            return patterns
        
        # Calculate trend line
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]  # Rate of change per day
        
        # Calculate annual degradation rate
        annual_slope = slope * 365
        
        # Check if degrading (negative slope)
        if annual_slope < 0:
            # Calculate relative degradation percentage
            mean_value = np.mean(y)
            degradation_rate = abs(annual_slope) / mean_value * 100  # percentage per year
            
            # Only flag if degradation is significant (>2% per year)
            if degradation_rate > 2:
                years = (dates[-1] - dates[0]).days / 365.25
                
                pattern = Pattern(
                    pattern_id=self._generate_pattern_id('degradation'),
                    plant_id=plant_id,
                    pattern_type='degradation',
                    metric_name=metric_name,
                    description=f"Performance degradation: Declining at "
                               f"{degradation_rate:.2f}% per year (total: {degradation_rate * years:.1f}%)",
                    frequency='annual',
                    amplitude=None,
                    significance_score=min(100, degradation_rate * 10),
                    confidence_pct=min(100, 70 + (degradation_rate * 2)),
                    first_observed_date=readings[0].date,
                    last_observed_date=readings[-1].date,
                    occurrence_count=int(years),
                    affected_plants=[plant_id],
                    is_fleet_wide=False
                )
                
                patterns.append(pattern)
        
        return patterns

    def _generate_pattern_id(self, pattern_type: str) -> str:
        """Generate unique pattern ID.
        
        Args:
            pattern_type: Type of pattern
            
        Returns:
            Unique pattern identifier
        """
        self.pattern_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"PAT_{pattern_type.upper()}_{timestamp}_{self.pattern_counter}"
