"""
InsightsEngine - generates actionable insights from anomalies and patterns.

This module combines detected anomalies and patterns to create actionable insights
that drive decision-making and enable proactive maintenance and optimization.

Classes:
    Recommendation: Data model for recommendations
    InsightsEngine: Main engine for insight generation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import uuid
from src.logic.data_models.reading import DailyReading
from src.logic.data_models.anomaly import Anomaly
from src.logic.data_models.pattern import Pattern
from src.logic.data_models.insight import Insight


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Recommendation:
    """
    A specific recommendation for addressing an insight.
    
    Attributes:
        recommendation_id: Unique identifier
        title: Short title of the recommendation
        description: Detailed description
        priority: Priority level (1-5, 5 is highest)
        effort_level: Effort to implement (LOW, MEDIUM, HIGH)
        expected_impact: Description of expected impact
        action_items: List of concrete action steps
    """
    recommendation_id: str
    title: str
    description: str
    priority: int
    effort_level: str
    expected_impact: str
    action_items: List[str]

    def __init__(
        self,
        title: str,
        description: str,
        priority: int,
        effort_level: str,
        expected_impact: str,
        action_items: List[str],
    ):
        self.recommendation_id = f"rec-{uuid.uuid4().hex[:8]}"
        self.title = title
        self.description = description
        self.priority = priority
        self.effort_level = effort_level
        self.expected_impact = expected_impact
        self.action_items = action_items


# ============================================================================
# INSIGHTS ENGINE
# ============================================================================

class InsightsEngine:
    """
    Generates actionable insights from anomalies and patterns.
    
    The engine combines detected anomalies and patterns to identify:
    - Performance issues requiring immediate attention
    - Maintenance needs
    - Optimization opportunities
    - Operational patterns
    
    Attributes:
        daily_readings: List of daily readings for context
        anomalies: Detected anomalies
        patterns: Detected patterns
    """

    def __init__(
        self,
        daily_readings: List[DailyReading],
        anomalies: List[Anomaly],
        patterns: List[Pattern],
    ):
        """
        Initialize the InsightsEngine.
        
        Args:
            daily_readings: Historical daily readings
            anomalies: Detected anomalies
            patterns: Detected patterns
        """
        self.daily_readings = daily_readings
        self.anomalies = anomalies
        self.patterns = patterns

    def generate_insights(self) -> List[Insight]:
        """
        Generate insights from anomalies and patterns.
        
        Returns:
            List of generated insights
        """
        insights = []

        # Generate insights from anomalies
        insights.extend(self._generate_anomaly_insights())

        # Generate insights from patterns
        insights.extend(self._generate_pattern_insights())

        # Generate combined insights
        insights.extend(self._generate_combined_insights())

        return insights

    def _generate_anomaly_insights(self) -> List[Insight]:
        """Generate insights from detected anomalies."""
        insights = []

        for anomaly in self.anomalies:
            # Map severity to urgency
            urgency = self._map_severity_to_urgency(anomaly.severity)

            # Create base insight
            title = f"Anomaly Detected: {anomaly.metric_name}"
            description = (
                f"Unexpected {anomaly.metric_name} value detected. "
                f"Actual: {anomaly.actual_value:.2f}, "
                f"Expected: {anomaly.expected_value:.2f}, "
                f"Deviation: {anomaly.deviation_pct:.1f}%"
            )
            reasoning = (
                f"Detected by {anomaly.detected_by} method with "
                f"{anomaly.severity} severity"
            )
            business_impact = f"Potential performance issue affecting {anomaly.metric_name}"
            confidence = self._calculate_confidence_from_anomaly(anomaly)

            insight = Insight(
                insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                plant_id=anomaly.plant_id,
                insight_type="anomaly_cause_hypothesis",
                title=title,
                description=description,
                reasoning=reasoning,
                business_impact=business_impact,
                confidence=confidence,
                urgency=urgency,
                linked_anomalies=[anomaly.anomaly_id],
                generation_date=datetime.now().strftime("%Y-%m-%d"),
            )

            insights.append(insight)

        return insights

    def _generate_pattern_insights(self) -> List[Insight]:
        """Generate insights from detected patterns."""
        insights = []

        for pattern in self.patterns:
            # Determine insight type based on pattern type
            if pattern.pattern_type == "degradation":
                insight_type = "performance_trend"
                title = f"Performance Degradation: {pattern.metric_name}"
            elif pattern.pattern_type == "seasonal":
                insight_type = "pattern_explanation"
                title = f"Seasonal Pattern: {pattern.metric_name}"
            else:  # weekly_cycle
                insight_type = "pattern_explanation"
                title = f"Operational Pattern: {pattern.metric_name}"

            # Map significance score to urgency
            urgency = self._map_score_to_urgency(pattern.significance_score)

            description = pattern.description
            if pattern.is_fleet_wide:
                description += " (Fleet-wide pattern)"
            description += f". Confidence: {pattern.confidence_pct:.1f}%"

            reasoning = (
                f"Pattern detected with {pattern.occurrence_count} occurrences. "
                f"Significance score: {pattern.significance_score:.1f}%, "
                f"Confidence: {pattern.confidence_pct:.1f}%"
            )

            if pattern.pattern_type == "degradation":
                business_impact = (
                    f"Equipment showing {pattern.amplitude:.1f}% degradation. "
                    f"Maintenance may be required."
                )
            else:
                business_impact = f"Expected {pattern.pattern_type} in {pattern.metric_name}"

            insight = Insight(
                insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                plant_id=pattern.plant_id,
                insight_type=insight_type,
                title=title,
                description=description,
                reasoning=reasoning,
                business_impact=business_impact,
                confidence=pattern.confidence_pct,
                urgency=urgency,
                linked_patterns=[pattern.pattern_id],
                generation_date=datetime.now().strftime("%Y-%m-%d"),
            )

            insights.append(insight)

        return insights

    def _generate_combined_insights(self) -> List[Insight]:
        """Generate insights that combine anomalies and patterns."""
        insights = []

        # Find anomalies that correlate with patterns
        for anomaly in self.anomalies:
            # Find patterns for the same metric
            related_patterns = [
                p for p in self.patterns
                if p.metric_name == anomaly.metric_name
            ]

            if not related_patterns:
                continue

            # Create combined insight
            pattern_descriptions = ", ".join([p.description for p in related_patterns])
            title = f"Anomaly in Context of Pattern: {anomaly.metric_name}"
            description = (
                f"Anomaly detected within a known pattern context. "
                f"Pattern: {pattern_descriptions}"
            )

            # Combine confidence scores
            anomaly_confidence = self._calculate_confidence_from_anomaly(anomaly)
            combined_confidence = (anomaly_confidence + (sum(
                p.confidence_pct for p in related_patterns
            ) / len(related_patterns))) / 2

            urgency = self._map_score_to_urgency(combined_confidence)

            insight = Insight(
                insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                plant_id=anomaly.plant_id,
                insight_type="performance_trend",
                title=title,
                description=description,
                reasoning=(
                    f"Correlation found between anomaly and {len(related_patterns)} "
                    f"pattern(s)"
                ),
                business_impact=f"Anomaly correlates with known pattern",
                confidence=min(100.0, combined_confidence),
                urgency=urgency,
                linked_anomalies=[anomaly.anomaly_id],
                linked_patterns=[p.pattern_id for p in related_patterns],
                generation_date=datetime.now().strftime("%Y-%m-%d"),
            )

            insights.append(insight)

        return insights

    def _calculate_confidence_from_anomaly(self, anomaly: Anomaly) -> float:
        """Calculate confidence score from anomaly data."""
        # Use z-score if available
        if anomaly.z_score is not None:
            # Z-score > 3 is very confident
            confidence = min(100.0, abs(anomaly.z_score) * 15)
        else:
            # Fall back to deviation percentage
            confidence = min(100.0, abs(anomaly.deviation_pct))
        
        return confidence

    def _map_severity_to_urgency(self, severity: str) -> str:
        """Map anomaly severity to insight urgency."""
        severity_to_urgency = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical",
        }
        return severity_to_urgency.get(severity.lower(), "medium")

    def _map_score_to_urgency(self, score: float) -> str:
        """Map significance/confidence score to urgency."""
        if score >= 85:
            return "critical"
        elif score >= 65:
            return "high"
        elif score >= 45:
            return "medium"
        else:
            return "low"

