"""Anomaly Data Model - Represents detected anomaly in sensor data."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Anomaly(BaseModel):
    """Pydantic model for detected anomalies."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    plant_id: str = Field(..., description="Plant identifier")
    date: str = Field(..., description="Anomaly date (YYYY-MM-DD)")
    metric_name: str = Field(..., description="Metric name (e.g., power_output_kwh)")
    actual_value: float = Field(..., description="Actual measured value")
    expected_value: float = Field(..., description="Expected value from baseline")
    deviation_pct: float = Field(..., description="Deviation percentage from expected")
    severity: str = Field(
        ..., description="Severity level (low, medium, high, critical)"
    )
    detected_by: str = Field(
        ..., description="Detection method (zscore, iqr, manual)"
    )
    z_score: Optional[float] = Field(
        default=None, description="Z-score value if detected by zscore"
    )
    iqr_bounds: Optional[dict] = Field(
        default=None, description="IQR bounds if detected by IQR (lower, upper)"
    )
    status: str = Field(
        default="open", description="Status (open, investigating, resolved, false_positive)"
    )
    detection_timestamp: str = Field(
        ..., description="Detection timestamp (ISO 8601 format)"
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

    @field_validator("severity", mode="after")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is one of allowed values."""
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"Severity must be one of {allowed}")
        return v

    @field_validator("detected_by", mode="after")
    @classmethod
    def validate_detection_method(cls, v: str) -> str:
        """Validate detection method is one of allowed values."""
        allowed = {"zscore", "iqr", "manual"}
        if v not in allowed:
            raise ValueError(f"detected_by must be one of {allowed}")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "anomaly_id": "ANOM_001_20251222",
                "plant_id": "PLANT_001",
                "date": "2025-12-22",
                "metric_name": "power_output_kwh",
                "actual_value": 250.0,
                "expected_value": 450.0,
                "deviation_pct": -44.4,
                "severity": "high",
                "detected_by": "zscore",
                "z_score": -4.44,
                "iqr_bounds": {"lower": 420.0, "upper": 480.0},
                "status": "open",
                "detection_timestamp": "2025-12-22T10:30:00",
            }
        }
