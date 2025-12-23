/**
 * InsightsList Component
 * 
 * Displays AI-generated insights about solar energy plant performance,
 * combining anomalies and patterns to provide actionable recommendations.
 * Includes filtering, sorting, pagination, and detailed insights panel.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './insights-list.css';

interface Insight {
  insight_id: string;
  plant_id: string;
  insight_type: string;
  title: string;
  description: string;
  reasoning: string;
  business_impact: string;
  confidence: number;
  recommended_action?: string;
  urgency: 'critical' | 'high' | 'medium' | 'low';
  linked_patterns: string[];
  linked_anomalies: string[];
  generation_date: string;
  applicable_date_range?: string;
}

interface FilterOptions {
  plant_id?: string;
  insight_type?: string;
  urgency?: string;
  min_confidence?: number;
}

interface SortOptions {
  sort_by: 'confidence' | 'urgency' | 'generation_date';
  sort_order: 'asc' | 'desc';
}

interface PaginationOptions {
  skip: number;
  limit: number;
}

interface InsightsListProps {
  onInsightSelected?: (insight: Insight) => void;
  onFilterChanged?: (filters: FilterOptions) => void;
  onSortChanged?: (sort: SortOptions) => void;
  onPageChanged?: (pagination: PaginationOptions) => void;
}

export const InsightsList: React.FC<InsightsListProps> = ({
  onInsightSelected,
  onFilterChanged,
  onSortChanged,
  onPageChanged,
}) => {
  // State management
  const [insights, setInsights] = useState<Insight[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);

  // Filter state
  const [filters, setFilters] = useState<FilterOptions>({});
  const [insightTypeFilter, setInsightTypeFilter] = useState('');
  const [urgencyFilter, setUrgencyFilter] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState(0);
  const [plantIdFilter, setPlantIdFilter] = useState('');

  // Sort state
  const [sortBy, setSortBy] = useState<SortOptions['sort_by']>('confidence');
  const [sortOrder, setSortOrder] = useState<SortOptions['sort_order']>('desc');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  /**
   * Fetch insights from API with current filters, sort, and pagination
   */
  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      const skip = (currentPage - 1) * pageSize;
      params.append('skip', skip.toString());
      params.append('limit', pageSize.toString());
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);

      if (filters.plant_id) params.append('plant_id', filters.plant_id);
      if (filters.insight_type) params.append('insight_type', filters.insight_type);
      if (filters.urgency) params.append('urgency', filters.urgency);
      if (filters.min_confidence) params.append('min_confidence', filters.min_confidence.toString());

      const response = await fetch(`/api/insights?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch insights: ${response.statusText}`);
      }

      const data = await response.json();
      setInsights(data.insights || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setInsights([]);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, sortBy, sortOrder, filters]);

  /**
   * Fetch insights on mount and when dependencies change
   */
  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  /**
   * Handle filter changes
   */
  const handleFilterChange = useCallback(() => {
    const newFilters: FilterOptions = {};
    if (insightTypeFilter) newFilters.insight_type = insightTypeFilter;
    if (urgencyFilter) newFilters.urgency = urgencyFilter;
    if (confidenceFilter > 0) newFilters.min_confidence = confidenceFilter;
    if (plantIdFilter) newFilters.plant_id = plantIdFilter;

    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page

    if (onFilterChanged) {
      onFilterChanged(newFilters);
    }
  }, [insightTypeFilter, urgencyFilter, confidenceFilter, plantIdFilter, onFilterChanged]);

  /**
   * Handle sort changes
   */
  const handleSortChange = useCallback((newSortBy: SortOptions['sort_by']) => {
    if (newSortBy === sortBy) {
      // Toggle sort order if same column clicked
      const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
      setSortOrder(newOrder);
      if (onSortChanged) {
        onSortChanged({ sort_by: sortBy, sort_order: newOrder });
      }
    } else {
      // New sort column, default to descending
      setSortBy(newSortBy);
      setSortOrder('desc');
      if (onSortChanged) {
        onSortChanged({ sort_by: newSortBy, sort_order: 'desc' });
      }
    }
    setCurrentPage(1); // Reset pagination
  }, [sortBy, sortOrder, onSortChanged]);

  /**
   * Handle pagination changes
   */
  const handlePageChange = useCallback((newPage: number) => {
    setCurrentPage(newPage);
    if (onPageChanged) {
      onPageChanged({ skip: (newPage - 1) * pageSize, limit: pageSize });
    }
  }, [pageSize, onPageChanged]);

  /**
   * Handle page size change
   */
  const handlePageSizeChange = useCallback((newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1); // Reset to first page
    if (onPageChanged) {
      onPageChanged({ skip: 0, limit: newSize });
    }
  }, [onPageChanged]);

  /**
   * Handle insight selection
   */
  const handleInsightSelect = useCallback((insight: Insight) => {
    setSelectedInsight(insight);
    if (onInsightSelected) {
      onInsightSelected(insight);
    }
  }, [onInsightSelected]);

  /**
   * Format date string
   */
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Get urgency badge styling
   */
  const getUrgencyClass = (urgency: string): string => {
    return `urgency-${urgency.toLowerCase()}`;
  };

  /**
   * Get insight type label
   */
  const getInsightTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'anomaly_cause_hypothesis': 'Anomaly Cause',
      'pattern_explanation': 'Pattern Explanation',
      'performance_trend': 'Performance Trend',
      'maintenance_recommendation': 'Maintenance',
      'operational_insight': 'Operational',
    };
    return labels[type] || type;
  };

  /**
   * Calculate total pages
   */
  const totalPages = Math.ceil(totalCount / pageSize);

  /**
   * Render loading state
   */
  if (loading && insights.length === 0) {
    return (
      <div className="insights-list-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading insights...</p>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="insights-list-container">
        <div className="error-state">
          <p className="error-message">Error loading insights: {error}</p>
          <button onClick={() => fetchInsights()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  /**
   * Render main component
   */
  return (
    <div className="insights-list-container">
      {/* Filters Section */}
      <div className="filter-section">
        <h2>AI-Generated Insights</h2>
        <div className="filter-group">
          <select
            value={insightTypeFilter}
            onChange={(e) => setInsightTypeFilter(e.target.value)}
            onBlur={handleFilterChange}
            aria-label="Filter by insight type"
            className="filter-select"
          >
            <option value="">All Types</option>
            <option value="anomaly_cause_hypothesis">Anomaly Cause</option>
            <option value="pattern_explanation">Pattern Explanation</option>
            <option value="performance_trend">Performance Trend</option>
            <option value="maintenance_recommendation">Maintenance</option>
            <option value="operational_insight">Operational</option>
          </select>

          <select
            value={urgencyFilter}
            onChange={(e) => setUrgencyFilter(e.target.value)}
            onBlur={handleFilterChange}
            aria-label="Filter by urgency"
            className="filter-select"
          >
            <option value="">All Urgency Levels</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <input
            type="number"
            min="0"
            max="100"
            placeholder="Min Confidence (%)"
            value={confidenceFilter}
            onChange={(e) => setConfidenceFilter(parseInt(e.target.value) || 0)}
            onBlur={handleFilterChange}
            aria-label="Filter by minimum confidence"
            className="filter-input"
          />

          <input
            type="text"
            placeholder="Plant ID"
            value={plantIdFilter}
            onChange={(e) => setPlantIdFilter(e.target.value)}
            onBlur={handleFilterChange}
            aria-label="Filter by plant ID"
            className="filter-input"
          />

          <button
            onClick={() => {
              setInsightTypeFilter('');
              setUrgencyFilter('');
              setConfidenceFilter(0);
              setPlantIdFilter('');
              setFilters({});
              setCurrentPage(1);
            }}
            className="clear-filters-button"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Empty state */}
      {insights.length === 0 && (
        <div className="empty-state">
          <p>No insights found matching your criteria.</p>
        </div>
      )}

      {/* Insights Table */}
      {insights.length > 0 && (
        <>
          <div className="table-container">
            <table className="insights-table">
              <thead>
                <tr>
                  <th onClick={() => handleSortChange('generation_date')} className="sortable-header">
                    Date {sortBy === 'generation_date' && <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                  </th>
                  <th>Type</th>
                  <th>Title</th>
                  <th onClick={() => handleSortChange('urgency')} className="sortable-header">
                    Urgency {sortBy === 'urgency' && <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                  </th>
                  <th onClick={() => handleSortChange('confidence')} className="sortable-header">
                    Confidence {sortBy === 'confidence' && <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                  </th>
                  <th>Plant</th>
                  <th>Links</th>
                </tr>
              </thead>
              <tbody>
                {insights.map((insight) => (
                  <tr
                    key={insight.insight_id}
                    onClick={() => handleInsightSelect(insight)}
                    className={selectedInsight?.insight_id === insight.insight_id ? 'selected' : ''}
                    role="button"
                    tabIndex={0}
                  >
                    <td className="date-cell">{formatDate(insight.generation_date)}</td>
                    <td className="type-cell">{getInsightTypeLabel(insight.insight_type)}</td>
                    <td className="title-cell">{insight.title}</td>
                    <td className={`urgency-cell ${getUrgencyClass(insight.urgency)}`}>
                      <span className="urgency-badge">{insight.urgency.charAt(0).toUpperCase() + insight.urgency.slice(1)}</span>
                    </td>
                    <td className="confidence-cell">
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{ width: `${insight.confidence}%` }}
                        />
                        <span className="confidence-text">{insight.confidence}%</span>
                      </div>
                    </td>
                    <td className="plant-cell">{insight.plant_id}</td>
                    <td className="links-cell">
                      {(insight.linked_patterns?.length || 0) > 0 && (
                        <span className="link-badge" title="Linked patterns">{insight.linked_patterns?.length}</span>
                      )}
                      {(insight.linked_anomalies?.length || 0) > 0 && (
                        <span className="link-badge anomaly" title="Linked anomalies">{insight.linked_anomalies?.length}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Details Panel */}
          {selectedInsight && (
            <div className="details-panel">
              <div className="panel-header">
                <h3>{selectedInsight.title}</h3>
                <button
                  onClick={() => setSelectedInsight(null)}
                  className="close-panel-button"
                  aria-label="Close details panel"
                >
                  ✕
                </button>
              </div>

              <div className="panel-content">
                <div className="detail-section">
                  <h4>Description</h4>
                  <p>{selectedInsight.description}</p>
                </div>

                <div className="detail-section">
                  <h4>Reasoning</h4>
                  <p>{selectedInsight.reasoning}</p>
                </div>

                <div className="detail-section">
                  <h4>Business Impact</h4>
                  <p>{selectedInsight.business_impact}</p>
                </div>

                {selectedInsight.recommended_action && (
                  <div className="detail-section action-section">
                    <h4>Recommended Action</h4>
                    <p>{selectedInsight.recommended_action}</p>
                  </div>
                )}

                <div className="detail-row">
                  <div className="detail-item">
                    <label>Confidence:</label>
                    <span>{selectedInsight.confidence}%</span>
                  </div>
                  <div className="detail-item">
                    <label>Urgency:</label>
                    <span className={getUrgencyClass(selectedInsight.urgency)}>
                      {selectedInsight.urgency.charAt(0).toUpperCase() + selectedInsight.urgency.slice(1)}
                    </span>
                  </div>
                </div>

                <div className="detail-row">
                  <div className="detail-item">
                    <label>Type:</label>
                    <span>{getInsightTypeLabel(selectedInsight.insight_type)}</span>
                  </div>
                  <div className="detail-item">
                    <label>Plant:</label>
                    <span>{selectedInsight.plant_id}</span>
                  </div>
                </div>

                <div className="detail-row">
                  <div className="detail-item">
                    <label>Generated:</label>
                    <span>{formatDate(selectedInsight.generation_date)}</span>
                  </div>
                </div>

                {(selectedInsight.linked_patterns?.length || 0) > 0 && (
                  <div className="detail-section links-section">
                    <h4>Linked Patterns ({selectedInsight.linked_patterns?.length})</h4>
                    <ul className="links-list">
                      {selectedInsight.linked_patterns?.map((patternId) => (
                        <li key={patternId}>{patternId}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {(selectedInsight.linked_anomalies?.length || 0) > 0 && (
                  <div className="detail-section links-section">
                    <h4>Linked Anomalies ({selectedInsight.linked_anomalies?.length})</h4>
                    <ul className="links-list">
                      {selectedInsight.linked_anomalies?.map((anomalyId) => (
                        <li key={anomalyId}>{anomalyId}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Pagination Controls */}
          <div className="pagination-section">
            <div className="pagination-info">
              <span>
                Showing {(currentPage - 1) * pageSize + 1} to{' '}
                {Math.min(currentPage * pageSize, totalCount)} of {totalCount} insights
              </span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(parseInt(e.target.value))}
                aria-label="Select page size"
                className="page-size-select"
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
              </select>
            </div>

            <div className="pagination-controls">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                aria-label="Previous page"
                className="pagination-button"
              >
                ← Previous
              </button>

              <div className="page-info">
                Page {currentPage} of {totalPages}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
                aria-label="Next page"
                className="pagination-button"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default InsightsList;
