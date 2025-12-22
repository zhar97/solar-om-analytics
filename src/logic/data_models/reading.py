"""DailyReading Data Model - Represents daily sensor readings from a plant."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DailyReading(BaseModel):
    """Pydantic model for daily sensor readings."""

    plant_id: str = Field(..., description="Plant identifier")
    date: str = Field(..., description="Reading date (YYYY-MM-DD)")
    power_output_kwh: float = Field(
        ..., ge=0, description="Daily power output in kilowatt-hours"
    )
    efficiency_pct: float = Field(
        ..., ge=0, le=100, description="Panel efficiency percentage (0-100)"
    )
    temperature_c: float = Field(..., description="Ambient temperature in Celsius")
    irradiance_w_m2: float = Field(
        ..., ge=0, description="Solar irradiance in W/m²"
    )
    inverter_status: str = Field(
        default="OK", description="Inverter status (OK, Warning, Error)"
    )
    grid_frequency_hz: float = Field(
        default=50.0, ge=45, le=55, description="Grid frequency in Hz"
    )

    @field_validator("date", mode="after")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("date", mode="after")
    @classmethod
    def validate_not_future_date(cls, v: str) -> str:
        """Ensure date is not in the future."""
        reading_date = datetime.strptime(v, "%Y-%m-%d").date()
        if reading_date > datetime.now().date():
            raise ValueError("Reading date cannot be in the future")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "plant_id": "PLANT_001",
                "date": "2025-12-22",
                "power_output_kwh": 450.5,
                "efficiency_pct": 18.5,
                "temperature_c": 35.2,
                "irradiance_w_m2": 850.0,
                "inverter_status": "OK",
                "grid_frequency_hz": 50.0,
            }
        }
