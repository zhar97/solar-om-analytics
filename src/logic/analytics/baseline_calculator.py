"""Baseline Calculator - Computes statistical baselines for anomaly detection."""
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np

from ..data_models.baseline import Baseline
from ..data_models.reading import DailyReading
from ..utils.constants import BASELINE_MIN_SAMPLES, BASELINE_WINDOW_DAYS
from ..utils.logging import setup_logging

logger = setup_logging(__name__)


class BaselineCalculator:
    """Calculate statistical baselines for anomaly detection."""

    def calculate(
        self,
        readings: List[DailyReading],
        plant_id: str,
        metric: str,
        period_name: Optional[str] = None,
    ) -> Baseline:
        """
        Calculate baseline statistics from readings.

        Args:
            readings: List of DailyReading objects
            plant_id: Plant identifier
            metric: Metric name to extract (power_output_kwh, efficiency_pct, etc.)
            period_name: Optional period name (e.g., Q1_2025)

        Returns:
            Baseline object with statistical parameters

        Raises:
            ValueError: If insufficient samples (<13) or invalid metric
        """
        if len(readings) < BASELINE_MIN_SAMPLES:
            raise ValueError(
                f"Insufficient samples: {len(readings)} < {BASELINE_MIN_SAMPLES}"
            )

        # Extract metric values
        values = self._extract_metric_values(readings, metric)

        if len(values) == 0:
            raise ValueError(f"No valid values found for metric: {metric}")

        # Calculate statistics
        mean = float(np.mean(values))
        std_dev = float(np.std(values))
        q1 = float(np.percentile(values, 25))
        q2 = float(np.percentile(values, 50))
        q3 = float(np.percentile(values, 75))
        iqr = q3 - q1
        min_val = float(np.min(values))
        max_val = float(np.max(values))

        # Get date range
        dates = [datetime.strptime(r.date, "%Y-%m-%d").date() for r in readings]
        date_range = f"{min(dates).isoformat()} to {max(dates).isoformat()}"

        # Create baseline object
        baseline = Baseline(
            plant_id=plant_id,
            period_name=period_name or self._infer_period_name(readings),
            metric_name=metric,
            mean=mean,
            std_dev=std_dev,
            q1=q1,
            q2=q2,
            q3=q3,
            iqr=iqr,
            min_val=min_val,
            max_val=max_val,
            samples_count=len(values),
            date_range=date_range,
            calculation_timestamp=datetime.now().isoformat(),
        )

        logger.info(
            f"Calculated baseline for {plant_id}/{metric}: mean={mean:.2f}, std_dev={std_dev:.2f}"
        )
        return baseline

    def calculate_for_period(
        self,
        readings: List[DailyReading],
        plant_id: str,
        metric: str,
        period_name: str,
    ) -> Baseline:
        """
        Calculate baseline for a specific period.

        Args:
            readings: List of DailyReading objects
            plant_id: Plant identifier
            metric: Metric name
            period_name: Period name (e.g., Q1_2025, WINTER_2024, SUMMER_2025)

        Returns:
            Baseline object
        """
        return self.calculate(readings, plant_id, metric, period_name)

    def update_rolling(
        self, baseline: Baseline, new_readings: List[DailyReading]
    ) -> Baseline:
        """
        Update baseline with new readings using rolling window.

        Args:
            baseline: Existing baseline
            new_readings: New readings to incorporate

        Returns:
            Updated baseline with rolling window
        """
        logger.info(
            f"Updating baseline for {baseline.plant_id} with {len(new_readings)} new readings"
        )
        # Re-calculate with new readings
        # In a production system, we'd maintain a history and apply rolling window
        # For now, just recalculate with all new readings
        return self.calculate(
            new_readings,
            baseline.plant_id,
            baseline.metric_name,
            baseline.period_name,
        )

    def _extract_metric_values(self, readings: List[DailyReading], metric: str) -> List[float]:
        """
        Extract numeric values for a specific metric.

        Args:
            readings: List of readings
            metric: Metric name to extract

        Returns:
            List of numeric values

        Raises:
            ValueError: If metric is invalid
        """
        valid_metrics = {
            "power_output_kwh",
            "efficiency_pct",
            "temperature_c",
            "irradiance_w_m2",
            "grid_frequency_hz",
        }

        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric: {metric}. Valid: {valid_metrics}")

        values = []
        for reading in readings:
            try:
                if metric == "power_output_kwh":
                    values.append(reading.power_output_kwh)
                elif metric == "efficiency_pct":
                    values.append(reading.efficiency_pct)
                elif metric == "temperature_c":
                    values.append(reading.temperature_c)
                elif metric == "irradiance_w_m2":
                    values.append(reading.irradiance_w_m2)
                elif metric == "grid_frequency_hz":
                    values.append(reading.grid_frequency_hz)
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error extracting metric {metric}: {e}")
                continue

        return values

    def _infer_period_name(self, readings: List[DailyReading]) -> str:
        """Infer period name from readings dates."""
        if not readings:
            return "UNKNOWN"

        dates = [datetime.strptime(r.date, "%Y-%m-%d").date() for r in readings]
        min_date = min(dates)
        max_date = max(dates)

        if min_date.month <= 3:
            quarter = "Q1"
        elif min_date.month <= 6:
            quarter = "Q2"
        elif min_date.month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"

        return f"{quarter}_{min_date.year}"
