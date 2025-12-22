"""Data Pipeline - Orchestrates CSV loading, validation, baseline, and anomaly detection."""
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..data_models.plant import Plant
from ..data_models.reading import DailyReading
from ..data_models.baseline import Baseline
from ..data_models.anomaly import Anomaly
from ..ingestion.csv_loader import CsvLoader
from ..analytics.data_validator import DataValidator
from ..analytics.baseline_calculator import BaselineCalculator
from ..analytics.anomaly_detector import AnomalyDetector
from ..utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class PipelineResult:
    """Result from data pipeline execution."""

    success: bool
    plants: Dict[str, Plant]
    readings_by_plant: Dict[str, List[DailyReading]]
    baselines_by_plant: Dict[str, Dict[str, Baseline]]  # plant_id -> {metric -> baseline}
    anomalies_by_plant: Dict[str, List[Anomaly]]  # plant_id -> [anomalies]
    errors: List[str]
    warnings: List[str]


class DataPipeline:
    """Orchestrate end-to-end data analysis pipeline."""

    def __init__(
        self,
        csv_loader: Optional[CsvLoader] = None,
        validator: Optional[DataValidator] = None,
        baseline_calculator: Optional[BaselineCalculator] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ):
        """
        Initialize pipeline with components.

        Args:
            csv_loader: CsvLoader instance (default: new instance)
            validator: DataValidator instance (default: new instance)
            baseline_calculator: BaselineCalculator instance (default: new instance)
            anomaly_detector: AnomalyDetector instance (default: new instance)
        """
        self.csv_loader = csv_loader or CsvLoader()
        self.validator = validator or DataValidator()
        self.baseline_calculator = baseline_calculator or BaselineCalculator()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()

    def execute(
        self,
        plants_csv_path: str,
        readings_csv_path: str,
        metrics: Optional[List[str]] = None,
        validate: bool = True,
        fill_gaps: bool = False,
    ) -> PipelineResult:
        """
        Execute full data pipeline.

        Args:
            plants_csv_path: Path to plants CSV file
            readings_csv_path: Path to readings CSV file
            metrics: Metrics to analyze (default: power_output_kwh)
            validate: Whether to validate readings (default: True)
            fill_gaps: Whether to fill date gaps (default: False)

        Returns:
            PipelineResult with plants, readings, baselines, and anomalies
        """
        metrics = metrics or ["power_output_kwh"]
        result = PipelineResult(
            success=False,
            plants={},
            readings_by_plant={},
            baselines_by_plant={},
            anomalies_by_plant={},
            errors=[],
            warnings=[],
        )

        try:
            # Step 1: Load CSV data
            logger.info("Step 1: Loading CSV data...")
            result.plants = self._load_plants(plants_csv_path, result)
            result.readings_by_plant = self._load_readings(readings_csv_path, result)

            if not result.plants or not result.readings_by_plant:
                result.errors.append("No plants or readings loaded")
                return result

            # Step 2: Process each plant
            logger.info(f"Step 2: Processing {len(result.plants)} plants...")
            for plant_id in result.plants:
                self._process_plant(
                    plant_id,
                    result,
                    metrics=metrics,
                    validate=validate,
                    fill_gaps=fill_gaps,
                )

            result.success = len(result.errors) == 0
            logger.info(
                f"Pipeline complete: success={result.success}, "
                f"plants={len(result.plants)}, "
                f"anomalies={sum(len(a) for a in result.anomalies_by_plant.values())}"
            )

        except Exception as e:
            result.errors.append(f"Pipeline execution error: {str(e)}")
            logger.error(f"Pipeline failed: {e}")

        return result

    def _load_plants(self, plants_csv_path: str, result: PipelineResult) -> Dict[str, Plant]:
        """Load plants from CSV."""
        try:
            plants = self.csv_loader.load_plants(plants_csv_path)
            logger.info(f"Loaded {len(plants)} plants from {plants_csv_path}")
            return plants
        except Exception as e:
            result.errors.append(f"Error loading plants CSV: {str(e)}")
            logger.error(f"Failed to load plants: {e}")
            return {}

    def _load_readings(self, readings_csv_path: str, result: PipelineResult) -> Dict[str, List[DailyReading]]:
        """Load readings from CSV."""
        try:
            readings = self.csv_loader.load_readings(readings_csv_path)
            logger.info(f"Loaded readings from {readings_csv_path}")
            return readings
        except Exception as e:
            result.errors.append(f"Error loading readings CSV: {str(e)}")
            logger.error(f"Failed to load readings: {e}")
            return {}

    def _process_plant(
        self,
        plant_id: str,
        result: PipelineResult,
        metrics: List[str],
        validate: bool,
        fill_gaps: bool,
    ):
        """Process a single plant through the full pipeline."""
        logger.info(f"Processing plant: {plant_id}")

        # Get readings for this plant
        readings = result.readings_by_plant.get(plant_id, [])
        if not readings:
            result.warnings.append(f"No readings found for plant {plant_id}")
            return

        # Step 2a: Validate readings
        if validate:
            readings = self._validate_readings(plant_id, readings, result)
            if not readings:
                result.warnings.append(f"No valid readings for plant {plant_id}")
                return

        # Step 2b: Remove duplicates
        readings = self.validator.remove_duplicates(readings)
        logger.debug(f"After dedup: {len(readings)} readings for {plant_id}")

        # Step 2c: Fill date gaps (optional)
        if fill_gaps and len(readings) > 1:
            readings = self.validator.fill_date_gaps(readings, method="interpolate")
            logger.debug(f"After gap fill: {len(readings)} readings for {plant_id}")

        # Step 2d: Calculate baselines and detect anomalies for each metric
        result.readings_by_plant[plant_id] = readings
        result.baselines_by_plant[plant_id] = {}
        result.anomalies_by_plant[plant_id] = []

        for metric in metrics:
            baselines, anomalies = self._analyze_metric(plant_id, readings, metric, result)
            if baselines:
                result.baselines_by_plant[plant_id].update(baselines)
            if anomalies:
                result.anomalies_by_plant[plant_id].extend(anomalies)

        logger.info(
            f"Plant {plant_id}: {len(result.baselines_by_plant[plant_id])} baselines, "
            f"{len(result.anomalies_by_plant[plant_id])} anomalies"
        )

    def _validate_readings(
        self,
        plant_id: str,
        readings: List[DailyReading],
        result: PipelineResult,
    ) -> List[DailyReading]:
        """Validate readings and filter invalid ones."""
        validation_results = self.validator.validate_batch(readings)
        valid_readings = [
            readings[i] for i, r in enumerate(validation_results) if r.is_valid
        ]

        invalid_count = len(readings) - len(valid_readings)
        if invalid_count > 0:
            result.warnings.append(f"Plant {plant_id}: {invalid_count} invalid readings filtered")
            logger.warning(f"Plant {plant_id}: filtered {invalid_count} invalid readings")

        return valid_readings

    def _analyze_metric(
        self,
        plant_id: str,
        readings: List[DailyReading],
        metric: str,
        result: PipelineResult,
    ) -> Tuple[Dict[str, Baseline], List[Anomaly]]:
        """Analyze a single metric: calculate baseline and detect anomalies."""
        try:
            if len(readings) < 13:
                result.warnings.append(
                    f"Plant {plant_id}/{metric}: insufficient readings ({len(readings)} < 13)"
                )
                logger.warning(f"Insufficient readings for {plant_id}/{metric}: {len(readings)} < 13")
                return {}, []

            # Calculate baseline
            baseline = self.baseline_calculator.calculate(
                readings,
                plant_id=plant_id,
                metric=metric,
            )

            # Detect anomalies
            anomalies = self.anomaly_detector.detect(readings, baseline)

            logger.info(
                f"Plant {plant_id}/{metric}: baseline mean={baseline.mean:.2f}, "
                f"detected {len(anomalies)} anomalies"
            )

            return {metric: baseline}, anomalies

        except Exception as e:
            result.errors.append(f"Error analyzing {plant_id}/{metric}: {str(e)}")
            logger.error(f"Error analyzing {plant_id}/{metric}: {e}")
            return {}, []

    def get_anomaly_summary(self, result: PipelineResult) -> Dict:
        """Generate summary of anomalies by severity."""
        summary = {
            "total_anomalies": 0,
            "by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "by_plant": {},
        }

        for plant_id, anomalies in result.anomalies_by_plant.items():
            summary["total_anomalies"] += len(anomalies)
            summary["by_plant"][plant_id] = {
                "count": len(anomalies),
                "by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            }

            for anomaly in anomalies:
                summary["by_severity"][anomaly.severity] += 1
                summary["by_plant"][plant_id]["by_severity"][anomaly.severity] += 1

        return summary
