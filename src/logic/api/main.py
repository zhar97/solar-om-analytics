"""FastAPI application for solar plant anomaly detection."""
from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
from typing import Optional

from src.logic.analytics.data_pipeline import DataPipeline
from src.logic.api.models import GetAnomaliesResponse, AnomalyResponse

# Initialize FastAPI app
app = FastAPI(
    title="Solar Plant Analytics API",
    description="ML-powered anomaly detection for solar plants",
    version="0.1.0",
)

# Global pipeline instance (in production, this would use dependency injection)
_pipeline: Optional[DataPipeline] = None
_pipeline_result = None


def get_pipeline():
    """Get or initialize the pipeline."""
    global _pipeline, _pipeline_result
    
    if _pipeline is None:
        # Initialize pipeline with test data
        _pipeline = DataPipeline()
        test_data_path = Path(__file__).parent.parent.parent.parent / "test" / "logic" / "fixtures"
        plants_file = str(test_data_path / "sample_plants.csv")
        readings_file = str(test_data_path / "sample_readings.csv")
        
        try:
            _pipeline_result = _pipeline.execute(plants_file, readings_file)
        except Exception as e:
            # If test data not available, create empty pipeline
            _pipeline = DataPipeline()
    
    return _pipeline, _pipeline_result


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Solar Plant Analytics API"}


@app.get("/api/anomalies")
async def get_all_anomalies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> GetAnomaliesResponse:
    """Get anomalies for all plants."""
    try:
        pipeline, result = get_pipeline()
        
        if result is None:
            return GetAnomaliesResponse(
                success=False,
                data=[],
                error="No data available",
                error_code="NO_DATA",
            )
        
        # Flatten anomalies from all plants
        all_anomalies = []
        for plant_anomalies in result.anomalies_by_plant.values():
            all_anomalies.extend(plant_anomalies)
        
        # Apply pagination
        paginated = all_anomalies[skip : skip + limit]
        
        # Convert to response format
        anomaly_responses = [
            AnomalyResponse(
                anomaly_id=anomaly.anomaly_id,
                plant_id=anomaly.plant_id,
                date=anomaly.date if isinstance(anomaly.date, str) else anomaly.date.isoformat(),
                metric_name=anomaly.metric_name,
                actual_value=anomaly.actual_value,
                expected_value=anomaly.expected_value,
                deviation_pct=anomaly.deviation_pct,
                severity=anomaly.severity,
                detected_by=anomaly.detected_by,
                status="active",
                z_score=anomaly.z_score,
                iqr_bounds=anomaly.iqr_bounds,
            )
            for anomaly in paginated
        ]
        
        return GetAnomaliesResponse(success=True, data=anomaly_responses)
    
    except Exception as e:
        return GetAnomaliesResponse(
            success=False,
            data=[],
            error=str(e),
            error_code="INTERNAL_ERROR",
        )


@app.get("/api/anomalies/{plant_id}")
async def get_anomalies_by_plant(
    plant_id: str,
    metric: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort: Optional[str] = Query("date"),
    order: Optional[str] = Query("desc"),
) -> GetAnomaliesResponse:
    """Get anomalies for a specific plant with optional filtering."""
    try:
        pipeline, result = get_pipeline()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Plant not found")
        
        # Check if plant exists
        if plant_id not in result.anomalies_by_plant:
            raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")
        
        # Get anomalies for the plant
        anomalies = result.anomalies_by_plant[plant_id]
        
        # Filter by metric if specified
        if metric:
            anomalies = [a for a in anomalies if a.metric_name == metric]
        
        # Filter by severity if specified
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        # Sort
        if sort == "date":
            reverse = order == "desc"
            anomalies = sorted(anomalies, key=lambda a: a.date, reverse=reverse)
        elif sort == "severity":
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            reverse = order == "desc"
            anomalies = sorted(
                anomalies,
                key=lambda a: severity_order.get(a.severity, 0),
                reverse=reverse,
            )
        
        # Apply pagination
        paginated = anomalies[skip : skip + limit]
        
        # Convert to response format
        anomaly_responses = [
            AnomalyResponse(
                anomaly_id=anomaly.anomaly_id,
                plant_id=anomaly.plant_id,
                date=anomaly.date if isinstance(anomaly.date, str) else anomaly.date.isoformat(),
                metric_name=anomaly.metric_name,
                actual_value=anomaly.actual_value,
                expected_value=anomaly.expected_value,
                deviation_pct=anomaly.deviation_pct,
                severity=anomaly.severity,
                detected_by=anomaly.detected_by,
                status="active",
                z_score=anomaly.z_score,
                iqr_bounds=anomaly.iqr_bounds,
            )
            for anomaly in paginated
        ]
        
        return GetAnomaliesResponse(success=True, data=anomaly_responses)
    
    except HTTPException:
        raise
    except Exception as e:
        return GetAnomaliesResponse(
            success=False,
            data=[],
            error=str(e),
            error_code="INTERNAL_ERROR",
        )


@app.get("/api/plants")
async def get_plants():
    """Get all plants."""
    try:
        pipeline, result = get_pipeline()
        
        if result is None:
            return {
                "success": False,
                "data": [],
                "error": "No data available",
                "error_code": "NO_DATA",
            }
        
        plants_data = [
            {
                "plant_id": plant.plant_id,
                "name": plant.name,
                "location": plant.location,
                "capacity_kwp": plant.capacity_kwp,
                "anomaly_count": len(result.anomalies_by_plant.get(plant.plant_id, [])),
            }
            for plant in result.plants
        ]
        
        return {
            "success": True,
            "data": plants_data,
        }
    
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
        }
