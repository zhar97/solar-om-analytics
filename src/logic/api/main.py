"""FastAPI application for solar plant anomaly detection."""
from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
from typing import Optional

from src.logic.analytics.data_pipeline import DataPipeline
from src.logic.analytics.pattern_detector import PatternDetector
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


@app.get("/api/patterns")
async def get_all_patterns(
    plant_id: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    min_confidence: int = Query(0, ge=0, le=100),
    sort_by: str = Query("confidence_pct"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Get patterns detected across all plants or filtered by criteria."""
    try:
        pipeline, result = get_pipeline()
        
        if result is None:
            return {
                "success": False,
                "patterns": [],
                "error": "No data available",
                "error_code": "NO_DATA",
            }
        
        # Detect patterns for all plants
        pattern_detector = PatternDetector()
        all_patterns = []
        
        for plant in result.plants:
            plant_readings = result.readings_by_plant.get(plant.plant_id, [])
            if plant_readings:
                patterns = pattern_detector.detect(
                    plant_id=plant.plant_id,
                    readings=plant_readings,
                    metric_name="power_output_kwh"
                )
                all_patterns.extend(patterns)
        
        # Apply filters
        if plant_id:
            all_patterns = [p for p in all_patterns if p.plant_id == plant_id]
        
        if pattern_type:
            all_patterns = [p for p in all_patterns if p.pattern_type == pattern_type]
        
        if min_confidence > 0:
            all_patterns = [p for p in all_patterns if p.confidence_pct >= min_confidence]
        
        # Sort
        if sort_by == "confidence_pct":
            reverse = sort_order == "desc"
            all_patterns = sorted(
                all_patterns,
                key=lambda p: p.confidence_pct,
                reverse=reverse
            )
        elif sort_by == "first_observed_date":
            reverse = sort_order == "desc"
            all_patterns = sorted(
                all_patterns,
                key=lambda p: p.first_observed_date,
                reverse=reverse
            )
        elif sort_by == "significance_score":
            reverse = sort_order == "desc"
            all_patterns = sorted(
                all_patterns,
                key=lambda p: p.significance_score,
                reverse=reverse
            )
        
        # Apply pagination
        paginated = all_patterns[skip : skip + limit]
        
        # Convert to response format
        pattern_responses = [
            {
                "pattern_id": pattern.pattern_id,
                "plant_id": pattern.plant_id,
                "pattern_type": pattern.pattern_type,
                "metric_name": pattern.metric_name,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "amplitude": pattern.amplitude,
                "significance_score": pattern.significance_score,
                "confidence_pct": pattern.confidence_pct,
                "first_observed_date": pattern.first_observed_date,
                "last_observed_date": pattern.last_observed_date,
                "occurrence_count": pattern.occurrence_count,
                "affected_plants": pattern.affected_plants,
                "is_fleet_wide": pattern.is_fleet_wide,
            }
            for pattern in paginated
        ]
        
        return {
            "success": True,
            "patterns": pattern_responses,
            "total": len(all_patterns),
            "skip": skip,
            "limit": limit,
        }
    
    except Exception as e:
        return {
            "success": False,
            "patterns": [],
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
        }


@app.get("/api/patterns/{plant_id}")
async def get_patterns_by_plant(
    plant_id: str,
    pattern_type: Optional[str] = Query(None),
    min_confidence: int = Query(0, ge=0, le=100),
    sort_by: str = Query("confidence_pct"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Get patterns for a specific plant."""
    try:
        pipeline, result = get_pipeline()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Plant not found")
        
        # Check if plant exists
        if plant_id not in result.readings_by_plant:
            raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")
        
        # Detect patterns for the plant
        plant_readings = result.readings_by_plant[plant_id]
        pattern_detector = PatternDetector()
        patterns = pattern_detector.detect(
            plant_id=plant_id,
            readings=plant_readings,
            metric_name="power_output_kwh"
        )
        
        # Apply filters
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        if min_confidence > 0:
            patterns = [p for p in patterns if p.confidence_pct >= min_confidence]
        
        # Sort
        if sort_by == "confidence_pct":
            reverse = sort_order == "desc"
            patterns = sorted(patterns, key=lambda p: p.confidence_pct, reverse=reverse)
        elif sort_by == "first_observed_date":
            reverse = sort_order == "desc"
            patterns = sorted(
                patterns,
                key=lambda p: p.first_observed_date,
                reverse=reverse
            )
        elif sort_by == "significance_score":
            reverse = sort_order == "desc"
            patterns = sorted(
                patterns,
                key=lambda p: p.significance_score,
                reverse=reverse
            )
        
        # Apply pagination
        paginated = patterns[skip : skip + limit]
        
        # Convert to response format
        pattern_responses = [
            {
                "pattern_id": pattern.pattern_id,
                "plant_id": pattern.plant_id,
                "pattern_type": pattern.pattern_type,
                "metric_name": pattern.metric_name,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "amplitude": pattern.amplitude,
                "significance_score": pattern.significance_score,
                "confidence_pct": pattern.confidence_pct,
                "first_observed_date": pattern.first_observed_date,
                "last_observed_date": pattern.last_observed_date,
                "occurrence_count": pattern.occurrence_count,
                "affected_plants": pattern.affected_plants,
                "is_fleet_wide": pattern.is_fleet_wide,
            }
            for pattern in paginated
        ]
        
        return {
            "success": True,
            "patterns": pattern_responses,
            "total": len(patterns),
            "skip": skip,
            "limit": limit,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "patterns": [],
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
        }
