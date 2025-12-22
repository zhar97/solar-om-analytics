"""HealthScore Data Model - Represents plant health composite metric."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class HealthScore(BaseModel):
    """Pydantic model for plant health scores."""

    plant_id: str = Field(..., description="Plant identifier")
    anomaly_frequency_score: float = Field(
        ..., ge=0, le=100, description="Frequency of anomalies (0-100)"
    )
    anomaly_severity_score: float = Field(
        ..., ge=0, le=100, description="Severity of anomalies (0-100)"
    )
    trend_score: float = Field(
        ..., ge=0, le=100, description="Health trend score (0-100)"
    )
    overall_score: float = Field(
        ..., ge=0, le=100, description="Overall health score (0-100)"
    )
    score_trend_7d: float = Field(
        ..., description="Score change in last 7 days (positive=improving, negative=declining)"
    )
    score_trend_30d: float = Field(
        ..., description="Score change in last 30 days (positive=improving, negative=declining)"
    )
    health_status: str = Field(
        ..., description="Health status (excellent, good, fair, poor, critical)"
    )
    calculation_date: str = Field(..., description="Calculation date (YYYY-MM-DD)")
    period_analyzed: str = Field(
        ..., description="Period analyzed (e.g., 'Last 30 days', 'Last 7 days')"
    )

    @field_validator("health_status", mode="after")
    @classmethod
    def validate_health_status(cls, v: str) -> str:
        """Validate health status is one of allowed values."""
        allowed = {"excellent", "good", "fair", "poor", "critical"}
        if v not in allowed:
            raise ValueError(f"health_status must be one of {allowed}")
        return v

    @field_validator("calculation_date", mode="after")
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
                "plant_id": "PLANT_001",
                "anomaly_frequency_score": 85.0,
                "anomaly_severity_score": 88.0,
                "trend_score": 82.0,
                "overall_score": 85.0,
                "score_trend_7d": 2.5,
                "score_trend_30d": -1.2,
                "health_status": "good",
                "calculation_date": "2025-12-22",
                "period_analyzed": "Last 30 days",
            }
        }
