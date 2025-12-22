"""Baseline Data Model - Represents statistical baseline for anomaly detection."""
from pydantic import BaseModel, Field, field_validator


class Baseline(BaseModel):
    """Pydantic model for baseline statistics."""

    plant_id: str = Field(..., description="Plant identifier")
    period_name: str = Field(..., description="Period name (e.g., Q1_2025)")
    metric_name: str = Field(..., description="Metric name (e.g., power_output_kwh)")
    mean: float = Field(..., description="Mean value")
    std_dev: float = Field(..., ge=0, description="Standard deviation")
    q1: float = Field(..., description="25th percentile (Q1)")
    q2: float = Field(..., description="50th percentile (Q2/Median)")
    q3: float = Field(..., description="75th percentile (Q3)")
    iqr: float = Field(..., ge=0, description="Interquartile range (Q3 - Q1)")
    min_val: float = Field(..., description="Minimum value")
    max_val: float = Field(..., description="Maximum value")
    samples_count: int = Field(..., ge=13, description="Number of samples (min 13)")
    date_range: str = Field(..., description="Date range of baseline (YYYY-MM-DD to YYYY-MM-DD)")
    calculation_timestamp: str = Field(
        ..., description="Calculation timestamp (ISO 8601 format)"
    )

    @field_validator("min_val", "max_val", "q1", "q2", "q3", mode="after")
    @classmethod
    def validate_quartile_order(cls, v: float) -> float:
        """Validate quartile order: min <= q1 <= q2 <= q3 <= max."""
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "plant_id": "PLANT_001",
                "period_name": "Q1_2025",
                "metric_name": "power_output_kwh",
                "mean": 450.0,
                "std_dev": 45.0,
                "q1": 420.0,
                "q2": 450.0,
                "q3": 480.0,
                "iqr": 60.0,
                "min_val": 250.0,
                "max_val": 550.0,
                "samples_count": 90,
                "date_range": "2025-01-01 to 2025-03-31",
                "calculation_timestamp": "2025-04-01T00:00:00",
            }
        }
