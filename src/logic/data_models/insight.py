"""Insight Data Model - Represents human-readable finding or recommendation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Insight(BaseModel):
    """Pydantic model for insights and findings."""

    insight_id: str = Field(..., description="Unique insight identifier")
    plant_id: str = Field(..., description="Plant identifier")
    insight_type: str = Field(
        ..., description="Insight type (pattern_explanation, anomaly_cause_hypothesis, performance_trend, maintenance_recommendation)"
    )
    title: str = Field(..., description="Short insight title")
    description: str = Field(..., description="Detailed insight description")
    reasoning: str = Field(..., description="Explanation of how insight was derived")
    business_impact: str = Field(
        ..., description="Impact on plant operations (e.g., revenue loss, maintenance needed)"
    )
    confidence: float = Field(
        ..., ge=0, le=100, description="Confidence level (0-100)"
    )
    recommended_action: Optional[str] = Field(
        default=None, description="Recommended action to take"
    )
    urgency: str = Field(
        default="low", description="Urgency level (low, medium, high, critical)"
    )
    linked_patterns: List[str] = Field(
        default_factory=list, description="List of linked pattern IDs"
    )
    linked_anomalies: List[str] = Field(
        default_factory=list, description="List of linked anomaly IDs"
    )
    generation_date: str = Field(..., description="Generation date (YYYY-MM-DD)")
    applicable_date_range: str = Field(
        default="", description="Applicable date range (YYYY-MM-DD to YYYY-MM-DD)"
    )

    @field_validator("insight_type", mode="after")
    @classmethod
    def validate_insight_type(cls, v: str) -> str:
        """Validate insight type is one of allowed values."""
        allowed = {
            "pattern_explanation",
            "anomaly_cause_hypothesis",
            "performance_trend",
            "maintenance_recommendation",
        }
        if v not in allowed:
            raise ValueError(f"insight_type must be one of {allowed}")
        return v

    @field_validator("urgency", mode="after")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        """Validate urgency is one of allowed values."""
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"urgency must be one of {allowed}")
        return v

    @field_validator("generation_date", mode="after")
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
                "insight_id": "INSIGHT_001_20251222",
                "plant_id": "PLANT_001",
                "insight_type": "pattern_explanation",
                "title": "Expected Winter Seasonal Decline",
                "description": "Production drops 25-30% in winter months due to lower irradiance and seasonal weather patterns. This is normal and expected.",
                "reasoning": "Historical data shows consistent 25-30% reduction Nov-Feb for 3 years. Statistical significance 92.5%.",
                "business_impact": "Expected revenue reduction of approximately 25% during winter season. No action required.",
                "confidence": 95.0,
                "recommended_action": "Monitor actual vs expected closely. Prepare Q1 budget forecasts accordingly.",
                "urgency": "low",
                "linked_patterns": ["PAT_001_SEASONAL"],
                "linked_anomalies": [],
                "generation_date": "2025-12-22",
                "applicable_date_range": "2025-11-01 to 2026-02-28",
            }
        }
