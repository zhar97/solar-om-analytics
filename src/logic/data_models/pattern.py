"""Pattern Data Model - Represents detected recurring pattern in data."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Pattern(BaseModel):
    """Pydantic model for detected patterns."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    plant_id: str = Field(..., description="Plant identifier")
    pattern_type: str = Field(
        ..., description="Pattern type (seasonal, degradation, weekly_cycle, etc.)"
    )
    metric_name: str = Field(..., description="Metric name (e.g., power_output_kwh)")
    description: str = Field(..., description="Human-readable pattern description")
    frequency: str = Field(..., description="Pattern frequency (daily, weekly, monthly, annual)")
    amplitude: Optional[float] = Field(
        default=None, description="Pattern amplitude (magnitude of variation)"
    )
    significance_score: float = Field(
        ..., ge=0, le=100, description="Statistical significance score (0-100)"
    )
    confidence_pct: float = Field(
        ..., ge=0, le=100, description="Confidence percentage (0-100)"
    )
    first_observed_date: str = Field(..., description="First observation date (YYYY-MM-DD)")
    last_observed_date: str = Field(..., description="Last observation date (YYYY-MM-DD)")
    occurrence_count: int = Field(..., ge=2, description="Number of occurrences (min 2)")
    affected_plants: List[str] = Field(
        default_factory=list, description="List of plant IDs affected by this pattern"
    )
    is_fleet_wide: bool = Field(
        default=False, description="Is pattern observed across multiple plants"
    )

    @field_validator("first_observed_date", "last_observed_date", mode="after")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "pattern_id": "PAT_001_SEASONAL",
                "plant_id": "PLANT_001",
                "pattern_type": "seasonal",
                "metric_name": "power_output_kwh",
                "description": "Winter Seasonal Decline: Production drops 25-30% Nov-Feb",
                "frequency": "annual",
                "amplitude": 125.0,
                "significance_score": 92.5,
                "confidence_pct": 95.0,
                "first_observed_date": "2023-11-01",
                "last_observed_date": "2025-02-28",
                "occurrence_count": 3,
                "affected_plants": ["PLANT_001"],
                "is_fleet_wide": False,
            }
        }
