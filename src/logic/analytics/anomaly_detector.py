"""Anomaly Detector - Detects anomalies using statistical methods."""
from datetime import datetime
from typing import List
import uuid

from scipy import stats
import numpy as np

from ..data_models.baseline import Baseline
from ..data_models.reading import DailyReading
from ..data_models.anomaly import Anomaly
from ..utils.constants import ZSCORE_THRESHOLD, IQR_MULTIPLIER, ANOMALY_SEVERITY_THRESHOLDS
from ..utils.logging import setup_logging

logger = setup_logging(__name__)


class AnomalyDetector:
    """Detect anomalies in sensor data using statistical methods."""

    def __init__(self, zscore_threshold: float = ZSCORE_THRESHOLD, iqr_multiplier: float = IQR_MULTIPLIER):
        """
        Initialize anomaly detector.

        Args:
            zscore_threshold: Z-score threshold for detection (default 2.0)
            iqr_multiplier: IQR multiplier for bounds (default 1.5)
        """
        self.zscore_threshold = zscore_threshold
        self.iqr_multiplier = iqr_multiplier

    def detect(
        self,
        readings: List[DailyReading],
        baseline: Baseline,
    ) -> List[Anomaly]:
        """
        Detect anomalies in readings against baseline.

        Args:
            readings: List of readings to check
            baseline: Baseline statistics

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Extract metric values from readings
        values = self._extract_metric_from_readings(readings, baseline.metric_name)

        for i, reading in enumerate(readings):
            if i >= len(values):
                continue

            value = values[i]

            # Try Z-score detection
            anomaly = self._detect_zscore(reading, value, baseline)
            if anomaly:
                anomalies.append(anomaly)
                logger.info(f"Detected Z-score anomaly: {anomaly.anomaly_id}")
                continue

            # Try IQR detection
            anomaly = self._detect_iqr(reading, value, baseline)
            if anomaly:
                anomalies.append(anomaly)
                logger.info(f"Detected IQR anomaly: {anomaly.anomaly_id}")

        logger.info(f"Detected {len(anomalies)} anomalies in {len(readings)} readings")
        return anomalies

    def detect_zscore(
        self,
        readings: List[DailyReading],
        baseline: Baseline,
        threshold: float = None,
    ) -> List[Anomaly]:
        """
        Detect anomalies using Z-score method.

        Args:
            readings: List of readings
            baseline: Baseline statistics
            threshold: Z-score threshold (default from config)

        Returns:
            List of Z-score anomalies
        """
        threshold = threshold or self.zscore_threshold
        anomalies = []
        values = self._extract_metric_from_readings(readings, baseline.metric_name)

        for i, reading in enumerate(readings):
            if i >= len(values):
                continue

            value = values[i]
            z_score = (value - baseline.mean) / baseline.std_dev if baseline.std_dev > 0 else 0

            if abs(z_score) > threshold:
                anomaly = self._create_anomaly(
                    reading, value, baseline, "zscore", z_score=z_score
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_iqr(
        self,
        readings: List[DailyReading],
        baseline: Baseline,
        multiplier: float = None,
    ) -> List[Anomaly]:
        """
        Detect anomalies using IQR method.

        Args:
            readings: List of readings
            baseline: Baseline statistics
            multiplier: IQR multiplier (default from config)

        Returns:
            List of IQR anomalies
        """
        multiplier = multiplier or self.iqr_multiplier
        anomalies = []
        values = self._extract_metric_from_readings(readings, baseline.metric_name)

        # Calculate IQR bounds
        lower_bound = baseline.q1 - (multiplier * baseline.iqr)
        upper_bound = baseline.q3 + (multiplier * baseline.iqr)

        for i, reading in enumerate(readings):
            if i >= len(values):
                continue

            value = values[i]

            if value < lower_bound or value > upper_bound:
                anomaly = self._create_anomaly(
                    reading,
                    value,
                    baseline,
                    "iqr",
                    iqr_bounds={"lower": lower_bound, "upper": upper_bound},
                )
                anomalies.append(anomaly)

        return anomalies

    def classify_severity(self, deviation_pct: float) -> str:
        """
        Classify anomaly severity based on deviation percentage.

        Args:
            deviation_pct: Deviation percentage from expected value

        Returns:
            Severity level (low, medium, high, critical)
        """
        abs_deviation = abs(deviation_pct)

        if abs_deviation >= ANOMALY_SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif abs_deviation >= ANOMALY_SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif abs_deviation >= ANOMALY_SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        elif abs_deviation >= ANOMALY_SEVERITY_THRESHOLDS["low"]:
            return "low"
        else:
            return "low"

    def _detect_zscore(
        self, reading: DailyReading, value: float, baseline: Baseline
    ) -> Anomaly:
        """Detect single anomaly using Z-score."""
        if baseline.std_dev == 0:
            return None

        z_score = (value - baseline.mean) / baseline.std_dev

        if abs(z_score) > self.zscore_threshold:
            return self._create_anomaly(reading, value, baseline, "zscore", z_score=z_score)

        return None

    def _detect_iqr(
        self, reading: DailyReading, value: float, baseline: Baseline
    ) -> Anomaly:
        """Detect single anomaly using IQR method."""
        lower_bound = baseline.q1 - (self.iqr_multiplier * baseline.iqr)
        upper_bound = baseline.q3 + (self.iqr_multiplier * baseline.iqr)

        if value < lower_bound or value > upper_bound:
            return self._create_anomaly(
                reading,
                value,
                baseline,
                "iqr",
                iqr_bounds={"lower": lower_bound, "upper": upper_bound},
            )

        return None

    def _create_anomaly(
        self,
        reading: DailyReading,
        value: float,
        baseline: Baseline,
        detection_method: str,
        z_score: float = None,
        iqr_bounds: dict = None,
    ) -> Anomaly:
        """Create an Anomaly object."""
        deviation_pct = ((value - baseline.mean) / baseline.mean * 100) if baseline.mean != 0 else 0
        severity = self.classify_severity(deviation_pct)

        return Anomaly(
            anomaly_id=f"ANOM_{reading.plant_id}_{reading.date}_{uuid.uuid4().hex[:8]}",
            plant_id=reading.plant_id,
            date=reading.date,
            metric_name=baseline.metric_name,
            actual_value=value,
            expected_value=baseline.mean,
            deviation_pct=deviation_pct,
            severity=severity,
            detected_by=detection_method,
            z_score=z_score,
            iqr_bounds=iqr_bounds,
            status="open",
            detection_timestamp=datetime.now().isoformat(),
        )

    def _extract_metric_from_readings(self, readings: List[DailyReading], metric: str) -> List[float]:
        """Extract metric values from readings."""
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
            except AttributeError:
                logger.warning(f"Could not extract metric {metric} from reading")
                values.append(0.0)

        return values
