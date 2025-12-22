"""Constants and Configuration for Solar Analytics Platform."""

# Anomaly Detection Thresholds
ZSCORE_THRESHOLD = 2.0  # Standard deviations for z-score detection
IQR_MULTIPLIER = 1.5  # Multiplier for IQR bounds

# Baseline Calculation
BASELINE_MIN_SAMPLES = 13  # Minimum samples required for baseline (>= 2 weeks)
BASELINE_WINDOW_DAYS = 730  # Rolling window size (2 years)

# Anomaly Severity Thresholds (deviation percentage boundaries)
ANOMALY_SEVERITY_THRESHOLDS = {
    "low": 5,  # 5-10%
    "medium": 10,  # 10-20%
    "high": 20,  # 20-50%
    "critical": 50,  # > 50%
}

# Health Score Weights (must sum to 1.0)
HEALTH_SCORE_WEIGHTS = {
    "frequency": 0.5,  # Weight for anomaly frequency
    "severity": 0.3,  # Weight for anomaly severity
    "trend": 0.2,  # Weight for trend
}

# Health Score Status Thresholds
HEALTH_STATUS_THRESHOLDS = {
    "excellent": 85,  # 85-100
    "good": 70,  # 70-85
    "fair": 55,  # 55-70
    "poor": 40,  # 40-55
    "critical": 0,  # 0-40
}

# Date Range Windows (in days)
ANOMALY_WINDOW_7D = 7
ANOMALY_WINDOW_30D = 30
ANOMALY_WINDOW_365D = 365

# API Settings
API_MAX_RESULTS_PER_PAGE = 100
API_DEFAULT_LIMIT = 20
API_REQUEST_TIMEOUT_SECONDS = 30

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/solar_analytics.log"
LOG_RETENTION_DAYS = 30

# Performance Targets (seconds)
CSV_LOADING_TARGET = 10  # Load CSV < 10s for 100 plants
ANOMALY_DETECTION_TARGET = 5  # Detect anomalies < 5s per plant
BASELINE_CALCULATION_TARGET = 2  # Calculate baseline < 2s per plant
API_RESPONSE_TARGET = 0.1  # API response < 100ms (0.1s)

# Pattern Detection Settings
PATTERN_MIN_OCCURRENCES = 2  # Minimum occurrences to be considered a pattern
PATTERN_SIGNIFICANCE_MIN = 70.0  # Minimum significance score
PATTERN_CONFIDENCE_MIN = 80.0  # Minimum confidence percentage

# Seasonal Pattern Detection
SEASONAL_PATTERN_WINDOW = 365  # Days to analyze for seasonal patterns
SEASONAL_PATTERN_MIN_YEARS = 2  # Minimum years of data required

# Insight Generation
INSIGHT_MIN_CONFIDENCE = 60.0  # Minimum confidence to generate insight
MAX_INSIGHTS_PER_PLANT = 50  # Maximum recent insights to store

# Export Settings
EXPORT_TIMEOUT_SECONDS = 30  # Timeout for export generation
EXPORT_MAX_ROWS = 10000  # Maximum rows in exported report

# CSV Data Validation
CSV_ENCODING = "utf-8"
CSV_DELIMITER = ","
CSV_DATE_FORMAT = "%Y-%m-%d"

# Valid Status Values
INVERTER_STATUS_VALUES = {"OK", "Warning", "Error"}
ANOMALY_STATUS_VALUES = {"open", "investigating", "resolved", "false_positive"}
INSIGHT_TYPE_VALUES = {
    "pattern_explanation",
    "anomaly_cause_hypothesis",
    "performance_trend",
    "maintenance_recommendation",
}
URGENCY_VALUES = {"low", "medium", "high", "critical"}
SEVERITY_VALUES = {"low", "medium", "high", "critical"}
HEALTH_STATUS_VALUES = {"excellent", "good", "fair", "poor", "critical"}
DETECTION_METHOD_VALUES = {"zscore", "iqr", "manual"}

# Feature Flags (for Phase 2 features)
ENABLE_WEATHER_DATA = False  # Enable weather integration (Phase 2)
ENABLE_GRID_DATA = False  # Enable grid frequency integration (Phase 2)
ENABLE_ML_MODELS = False  # Enable ML model-based detection (Phase 2)
ENABLE_REAL_TIME_STREAMING = False  # Enable real-time data streaming (Phase 2)
ENABLE_DATABASE_PERSISTENCE = False  # Enable database persistence (Phase 2)
