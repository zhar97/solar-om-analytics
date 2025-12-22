"""Unit Tests for CSV Loader Module - T021"""
import pytest
from pathlib import Path

from src.logic.ingestion.csv_loader import CsvLoader
from src.logic.data_models.plant import Plant
from src.logic.data_models.reading import DailyReading


class TestCsvLoader:
    """Test suite for CsvLoader class."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def csv_loader(self):
        """Provide a CsvLoader instance."""
        return CsvLoader()

    def test_load_plants_valid_csv(self, csv_loader, fixtures_dir):
        """Test: Load valid plant_details.csv -> List[Plant]"""
        plants_path = fixtures_dir / "sample_plants.csv"
        plants = csv_loader.load_plants(str(plants_path))

        assert len(plants) == 3
        assert "PLANT_001" in plants
        assert isinstance(plants["PLANT_001"], Plant)
        assert plants["PLANT_001"].plant_name == "Solar Farm Alpha"
        assert plants["PLANT_001"].capacity_kw == 500.0

    def test_load_readings_valid_csv(self, csv_loader, fixtures_dir):
        """Test: Load valid daily_plant.csv -> Dict[plant_id, List[DailyReading]]"""
        readings_path = fixtures_dir / "sample_readings.csv"
        readings = csv_loader.load_readings(str(readings_path))

        assert "PLANT_001" in readings
        assert len(readings["PLANT_001"]) == 6  # 6 readings for PLANT_001
        assert isinstance(readings["PLANT_001"][0], DailyReading)
        assert readings["PLANT_001"][0].power_output_kwh == 450.5

    def test_load_plants_file_not_found(self, csv_loader):
        """Test: Handle missing file gracefully."""
        with pytest.raises(FileNotFoundError):
            csv_loader.load_plants("/nonexistent/path/plants.csv")

    def test_load_readings_file_not_found(self, csv_loader):
        """Test: Handle missing file gracefully."""
        with pytest.raises(FileNotFoundError):
            csv_loader.load_readings("/nonexistent/path/readings.csv")

    def test_load_plants_invalid_data_type(self, csv_loader, tmp_path):
        """Test: Reject non-numeric capacity_kw."""
        bad_csv = tmp_path / "bad_plants.csv"
        content = "plant_id,plant_name,capacity_kw,location,installation_date,equipment_type\n"
        content += "PLANT_BAD,Bad Plant,invalid_number,Test Location,2020-01-01,Monocrystalline\n"
        bad_csv.write_text(content)

        # Should raise validation error
        with pytest.raises((ValueError, Exception)):
            csv_loader.load_plants(str(bad_csv))
