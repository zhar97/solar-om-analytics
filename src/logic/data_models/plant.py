"""Plant Data Model - Represents a solar power plant."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Plant(BaseModel):
    """Pydantic model for a solar power plant."""

    plant_id: str = Field(..., description="Unique plant identifier")
    plant_name: str = Field(..., description="Human-readable plant name")
    capacity_kw: float = Field(..., gt=0, description="Plant capacity in kilowatts")
    location: str = Field(..., description="Geographic location of plant")
    installation_date: str = Field(..., description="Installation date (YYYY-MM-DD)")
    equipment_type: str = Field(..., description="Solar panel type (e.g., Monocrystalline)")
    current_health_score: float = Field(
        default=0.0, ge=0, le=100, description="Current health score (0-100)"
    )
    last_analysis_date: str = Field(
        default="", description="Last analysis date (YYYY-MM-DD)"
    )
    anomaly_count_7d: int = Field(
        default=0, ge=0, description="Number of anomalies in last 7 days"
    )
    anomaly_count_30d: int = Field(
        default=0, ge=0, description="Number of anomalies in last 30 days"
    )

    @field_validator("installation_date", "last_analysis_date", mode="after")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        if v and len(v) > 0:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plant_id": "PLANT_001",
                "plant_name": "Solar Farm Alpha",
                "capacity_kw": 500.0,
                "location": "Chennai, India",
                "installation_date": "2020-01-15",
                "equipment_type": "Monocrystalline",
                "current_health_score": 85.5,
                "last_analysis_date": "2025-12-22",
                "anomaly_count_7d": 2,
                "anomaly_count_30d": 8,
            }
        }
    )
