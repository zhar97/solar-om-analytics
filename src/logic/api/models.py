"""API Response Models - Pydantic models for API responses."""
from typing import TypeVar, Generic, List, Optional, Any, Dict
from pydantic import BaseModel, Field

from ..data_models.plant import Plant
from ..data_models.reading import DailyReading
from ..data_models.baseline import Baseline
from ..data_models.anomaly import Anomaly
from ..data_models.pattern import Pattern
from ..data_models.insight import Insight
from ..data_models.health_score import HealthScore

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = Field(..., description="Request success status")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(default=False, description="Success flag")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class GetPlantsResponse(BaseModel):
    """Response for GET /api/v1/plants."""

    success: bool = Field(default=True)
    plants: List[Plant] = Field(..., description="List of plants")
    total_count: int = Field(..., description="Total number of plants")
    returned_count: int = Field(..., description="Number of plants returned")


class PlantDetailResponse(BaseModel):
    """Response for GET /api/v1/plants/{plant_id}."""

    success: bool = Field(default=True)
    plant: Plant = Field(..., description="Plant details")
    health_components: Dict[str, float] = Field(
        ..., description="Breakdown of health score components"
    )
    anomaly_count_annual: int = Field(
        default=0, description="Number of anomalies in last 365 days"
    )
    latest_reading: Optional[DailyReading] = Field(
        default=None, description="Latest sensor reading"
    )


class GetAnomaliesResponse(BaseModel):
    """Response for GET /api/v1/plants/{plant_id}/anomalies."""

    success: bool = Field(default=True)
    anomalies: List[Anomaly] = Field(..., description="List of anomalies")
    total_count: int = Field(..., description="Total number of anomalies")
    returned_count: int = Field(..., description="Number of anomalies returned")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict, description="Applied filters"
    )


class GetInsightsResponse(BaseModel):
    """Response for GET /api/v1/plants/{plant_id}/insights."""

    success: bool = Field(default=True)
    insights: List[Insight] = Field(..., description="List of insights")
    total_count: int = Field(..., description="Total number of insights")
    returned_count: int = Field(..., description="Number of insights returned")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict, description="Applied filters"
    )


class GetPatternsResponse(BaseModel):
    """Response for GET /api/v1/plants/{plant_id}/patterns."""

    success: bool = Field(default=True)
    patterns: List[Pattern] = Field(..., description="List of patterns")
    total_count: int = Field(..., description="Total number of patterns")
    returned_count: int = Field(..., description="Number of patterns returned")


class DiagnosticResponse(BaseModel):
    """Response for GET /api/v1/plants/{plant_id}/diagnostics/{anomaly_id}."""

    success: bool = Field(default=True)
    anomaly: Anomaly = Field(..., description="Anomaly details")
    readings_context: List[DailyReading] = Field(
        ..., description="Readings before and after anomaly"
    )
    equipment_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Equipment events during period"
    )
    possible_causes: List[str] = Field(
        ..., description="Possible causes for the anomaly"
    )
    investigation_notes: str = Field(
        default="", description="Investigation notes field"
    )


class ExportRequest(BaseModel):
    """Request body for POST /api/v1/plants/{plant_id}/export."""

    format: str = Field(..., description="Export format (pdf, csv, json)")
    content: str = Field(
        ..., description="Content level (anomalies, insights, health_summary, full_report)"
    )
    date_from: Optional[str] = Field(
        default=None, description="Start date for export (YYYY-MM-DD)"
    )
    date_to: Optional[str] = Field(
        default=None, description="End date for export (YYYY-MM-DD)"
    )
    include_diagnostics: bool = Field(
        default=False, description="Include diagnostic drill-down data"
    )


class ExportResponse(BaseModel):
    """Response for POST /api/v1/plants/{plant_id}/export."""

    success: bool = Field(default=True)
    download_url: str = Field(..., description="URL to download exported file")
    filename: str = Field(..., description="Generated filename")
    size_bytes: int = Field(..., description="File size in bytes")
    generation_time_seconds: float = Field(
        ..., description="Time taken to generate report"
    )


class IngestRequest(BaseModel):
    """Request body for POST /api/v1/ingest."""

    source: str = Field(default="csv", description="Data source (csv, database)")
    plants_to_analyze: Optional[List[str]] = Field(
        default=None, description="Specific plants to analyze (None = all)"
    )
    force_recalculate: bool = Field(
        default=False, description="Force recalculation of all baselines"
    )


class IngestResponse(BaseModel):
    """Response for POST /api/v1/ingest."""

    success: bool = Field(default=True)
    job_id: str = Field(..., description="Job tracking ID")
    status: str = Field(..., description="Ingestion status (pending, processing, complete)")
    plants_processed: int = Field(..., description="Number of plants processed")
    new_anomalies: int = Field(..., description="Number of new anomalies detected")
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    processing_time_seconds: Optional[float] = Field(
        default=None, description="Time taken to complete"
    )
