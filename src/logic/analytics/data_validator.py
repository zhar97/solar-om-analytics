"""Data Validator - Validates and cleans sensor data."""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from ..data_models.reading import DailyReading
from ..utils.logging import setup_logging

logger = setup_logging(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


@dataclass
class ValidationResult:
    """Result of batch validation."""

    is_valid: bool
    errors: List[str]


class DataValidator:
    """Validate and clean sensor reading data."""

    VALID_INVERTER_STATUSES = {"active", "inactive", "fault", "standby", "maintenance"}
    VALID_GRID_FREQUENCIES = (49.5, 50.5)  # Hz range tolerance
    OUTLIER_ZSCORE_THRESHOLD = 3.0

    def __init__(self):
        """Initialize validator."""
        self.validation_errors = []

    def validate(self, reading: DailyReading) -> bool:
        """
        Validate a single reading.

        Args:
            reading: Reading to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        # Check plant_id
        if not reading.plant_id or reading.plant_id.strip() == "":
            errors.append("plant_id cannot be empty")

        # Check date format and value
        try:
            reading_date = datetime.strptime(reading.date, "%Y-%m-%d")
            if reading_date > datetime.now():
                errors.append(f"date cannot be in the future: {reading.date}")
        except ValueError:
            errors.append(f"invalid date format: {reading.date}, expected YYYY-MM-DD")

        # Check power output
        if reading.power_output_kwh < 0:
            errors.append(f"power_output_kwh cannot be negative: {reading.power_output_kwh}")

        # Check efficiency
        if reading.efficiency_pct < 0 or reading.efficiency_pct > 100:
            errors.append(f"efficiency_pct must be 0-100: {reading.efficiency_pct}")

        # Check temperature (realistic bounds for solar)
        if reading.temperature_c < -50 or reading.temperature_c > 80:
            errors.append(f"temperature_c out of realistic range: {reading.temperature_c}")

        # Check irradiance
        if reading.irradiance_w_m2 < 0 or reading.irradiance_w_m2 > 1500:
            errors.append(f"irradiance_w_m2 out of range (0-1500): {reading.irradiance_w_m2}")

        # Check inverter status
        if reading.inverter_status.lower() not in self.VALID_INVERTER_STATUSES:
            errors.append(
                f"inverter_status must be one of {self.VALID_INVERTER_STATUSES}: {reading.inverter_status}"
            )

        # Check grid frequency
        if not (self.VALID_GRID_FREQUENCIES[0] <= reading.grid_frequency_hz <= self.VALID_GRID_FREQUENCIES[1]):
            errors.append(
                f"grid_frequency_hz out of range (49.5-50.5 Hz): {reading.grid_frequency_hz}"
            )

        if errors:
            logger.warning(f"Validation failed for reading {reading.plant_id}/{reading.date}: {errors}")
            raise ValidationError("; ".join(errors))

        logger.debug(f"Validation passed for reading {reading.plant_id}/{reading.date}")
        return True

    def detect_outliers(
        self,
        readings: List[DailyReading],
        method: str = "zscore",
        threshold: float = OUTLIER_ZSCORE_THRESHOLD,
    ) -> List[DailyReading]:
        """
        Detect outlier readings.

        Args:
            readings: List of readings to check
            method: Detection method ("zscore" or "iqr")
            threshold: Detection threshold

        Returns:
            List of outlier readings
        """
        if len(readings) < 3:
            logger.warning("Need at least 3 readings for outlier detection")
            return []

        values = np.array([r.power_output_kwh for r in readings])

        if method == "zscore":
            return self._detect_outliers_zscore(readings, values, threshold)
        elif method == "iqr":
            return self._detect_outliers_iqr(readings, values)
        else:
            logger.warning(f"Unknown outlier detection method: {method}")
            return []

    def _detect_outliers_zscore(
        self,
        readings: List[DailyReading],
        values: np.ndarray,
        threshold: float,
    ) -> List[DailyReading]:
        """Detect outliers using Z-score method."""
        mean = np.mean(values)
        std_dev = np.std(values)

        if std_dev == 0:
            logger.warning("Standard deviation is 0, cannot detect outliers")
            return []

        z_scores = np.abs((values - mean) / std_dev)
        outlier_indices = np.where(z_scores > threshold)[0]

        outliers = [readings[i] for i in outlier_indices]
        logger.info(f"Detected {len(outliers)} outliers using Z-score method (threshold={threshold})")
        return outliers

    def _detect_outliers_iqr(
        self,
        readings: List[DailyReading],
        values: np.ndarray,
    ) -> List[DailyReading]:
        """Detect outliers using IQR method."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_indices = np.where((values < lower_bound) | (values > upper_bound))[0]

        outliers = [readings[i] for i in outlier_indices]
        logger.info(f"Detected {len(outliers)} outliers using IQR method")
        return outliers

    def remove_duplicates(self, readings: List[DailyReading]) -> List[DailyReading]:
        """
        Remove duplicate readings (same plant_id and date).

        Args:
            readings: List of readings

        Returns:
            List with duplicates removed
        """
        seen = set()
        unique = []

        for reading in readings:
            key = (reading.plant_id, reading.date)
            if key not in seen:
                seen.add(key)
                unique.append(reading)
            else:
                logger.warning(f"Duplicate reading removed: {reading.plant_id}/{reading.date}")

        logger.info(f"Removed {len(readings) - len(unique)} duplicates, {len(unique)} readings remain")
        return unique

    def fill_date_gaps(
        self,
        readings: List[DailyReading],
        method: str = "interpolate",
    ) -> List[DailyReading]:
        """
        Fill gaps in date range.

        Args:
            readings: List of readings (should be sorted by date)
            method: Fill method ("interpolate" or "forward_fill")

        Returns:
            List with gaps filled
        """
        if len(readings) < 2:
            return readings

        # Sort by date
        sorted_readings = sorted(readings, key=lambda r: r.date)

        # Find date range
        start_date = datetime.strptime(sorted_readings[0].date, "%Y-%m-%d")
        end_date = datetime.strptime(sorted_readings[-1].date, "%Y-%m-%d")

        # Create reading lookup
        readings_by_date = {r.date: r for r in sorted_readings}

        # Fill gaps
        filled = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            if date_str in readings_by_date:
                filled.append(readings_by_date[date_str])
            else:
                # Interpolate or forward fill
                if method == "interpolate":
                    filled_reading = self._interpolate_reading(
                        sorted_readings, current_date
                    )
                    if filled_reading:
                        filled.append(filled_reading)
                        logger.debug(f"Interpolated reading for {date_str}")
                elif method == "forward_fill":
                    if filled:
                        last_reading = filled[-1]
                        filled_reading = DailyReading(
                            plant_id=last_reading.plant_id,
                            date=date_str,
                            power_output_kwh=last_reading.power_output_kwh,
                            efficiency_pct=last_reading.efficiency_pct,
                            temperature_c=last_reading.temperature_c,
                            irradiance_w_m2=last_reading.irradiance_w_m2,
                            inverter_status=last_reading.inverter_status,
                            grid_frequency_hz=last_reading.grid_frequency_hz,
                        )
                        filled.append(filled_reading)
                        logger.debug(f"Forward-filled reading for {date_str}")

            current_date += timedelta(days=1)

        logger.info(f"Filled {len(filled) - len(sorted_readings)} gaps, total readings: {len(filled)}")
        return filled

    def _interpolate_reading(
        self,
        readings: List[DailyReading],
        target_date: datetime,
    ) -> Optional[DailyReading]:
        """Interpolate a reading for target date using adjacent readings."""
        before = None
        after = None

        for reading in readings:
            reading_date = datetime.strptime(reading.date, "%Y-%m-%d")
            if reading_date < target_date:
                before = reading
            elif reading_date > target_date:
                after = reading
                break

        if before and after:
            # Linear interpolation
            before_date = datetime.strptime(before.date, "%Y-%m-%d")
            after_date = datetime.strptime(after.date, "%Y-%m-%d")

            total_days = (after_date - before_date).days
            days_from_before = (target_date - before_date).days

            if total_days > 0:
                ratio = days_from_before / total_days

                interpolated = DailyReading(
                    plant_id=before.plant_id,
                    date=target_date.strftime("%Y-%m-%d"),
                    power_output_kwh=before.power_output_kwh + ratio
                    * (after.power_output_kwh - before.power_output_kwh),
                    efficiency_pct=before.efficiency_pct
                    + ratio * (after.efficiency_pct - before.efficiency_pct),
                    temperature_c=before.temperature_c
                    + ratio * (after.temperature_c - before.temperature_c),
                    irradiance_w_m2=before.irradiance_w_m2
                    + ratio * (after.irradiance_w_m2 - before.irradiance_w_m2),
                    inverter_status=before.inverter_status,
                    grid_frequency_hz=before.grid_frequency_hz,
                )
                return interpolated

        return None

    def validate_batch(self, readings: List[DailyReading]) -> List[ValidationResult]:
        """
        Validate multiple readings at once.

        Args:
            readings: List of readings to validate

        Returns:
            List of validation results (one per reading)
        """
        results = []

        for reading in readings:
            try:
                self.validate(reading)
                results.append(ValidationResult(is_valid=True, errors=[]))
            except ValidationError as e:
                results.append(ValidationResult(is_valid=False, errors=[str(e)]))

        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"Batch validation: {valid_count}/{len(readings)} readings valid")
        return results
