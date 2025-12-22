"""CSV Data Loader - Loads plant and reading data from CSV files."""
import csv
from pathlib import Path
from typing import Dict, List, Tuple

from ..data_models.plant import Plant
from ..data_models.reading import DailyReading
from ..utils.logging import setup_logging

logger = setup_logging(__name__)


class CsvLoader:
    """Load plant and reading data from CSV files."""

    def load_plants(self, filepath: str) -> Dict[str, Plant]:
        """
        Load plant details from CSV.

        Args:
            filepath: Path to plant_details.csv

        Returns:
            Dict mapping plant_id to Plant objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV format is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Plant CSV file not found: {filepath}")

        plants = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        plant = Plant(
                            plant_id=row["plant_id"],
                            plant_name=row["plant_name"],
                            capacity_kw=float(row["capacity_kw"]),
                            location=row["location"],
                            installation_date=row["installation_date"],
                            equipment_type=row["equipment_type"],
                        )
                        plants[plant.plant_id] = plant
                        logger.info(f"Loaded plant: {plant.plant_id}")
                    except (ValueError, KeyError) as e:
                        logger.error(f"Error parsing plant row: {row}, error: {e}")
                        raise ValueError(f"Invalid plant data in CSV: {e}")

        except Exception as e:
            logger.error(f"Error loading plants CSV: {e}")
            raise

        logger.info(f"Successfully loaded {len(plants)} plants from {filepath}")
        return plants

    def load_readings(self, filepath: str) -> Dict[str, List[DailyReading]]:
        """
        Load daily readings from CSV.

        Args:
            filepath: Path to daily_plant.csv

        Returns:
            Dict mapping plant_id to list of DailyReading objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV format is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Readings CSV file not found: {filepath}")

        readings_dict = {}
        total_readings = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        reading = DailyReading(
                            plant_id=row["plant_id"],
                            date=row["date"],
                            power_output_kwh=float(row["power_output_kwh"]),
                            efficiency_pct=float(row["efficiency_pct"]),
                            temperature_c=float(row["temperature_c"]),
                            irradiance_w_m2=float(row["irradiance_w_m2"]),
                            inverter_status=row.get("inverter_status", "OK"),
                            grid_frequency_hz=float(row.get("grid_frequency_hz", 50.0)),
                        )

                        if reading.plant_id not in readings_dict:
                            readings_dict[reading.plant_id] = []
                        readings_dict[reading.plant_id].append(reading)
                        total_readings += 1

                    except (ValueError, KeyError) as e:
                        logger.error(f"Error parsing reading row: {row}, error: {e}")
                        raise ValueError(f"Invalid reading data in CSV: {e}")

        except Exception as e:
            logger.error(f"Error loading readings CSV: {e}")
            raise

        logger.info(
            f"Successfully loaded {total_readings} readings from {len(readings_dict)} plants"
        )
        return readings_dict

    def load_all(
        self, plants_path: str, readings_path: str
    ) -> Tuple[Dict[str, Plant], Dict[str, List[DailyReading]]]:
        """
        Load both plants and readings.

        Args:
            plants_path: Path to plant_details.csv
            readings_path: Path to daily_plant.csv

        Returns:
            Tuple of (plants_dict, readings_dict)
        """
        logger.info("Starting to load all data...")
        plants = self.load_plants(plants_path)
        readings = self.load_readings(readings_path)
        logger.info("Completed loading all data")
        return plants, readings
