/**
 * PatternList Component
 * 
 * Displays detected patterns in solar energy data with filtering,
 * sorting, pagination, and detailed information panel.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './pattern-list.css';

interface Pattern {
  pattern_id: string;
  plant_id: string;
  pattern_type: 'seasonal' | 'weekly_cycle' | 'degradation';
  metric_name: string;
  description: string;
  frequency: string;
  amplitude: number;
  significance_score: number;
  confidence_pct: number;
  first_observed_date: string;
  last_observed_date: string;
  occurrence_count: number;
  affected_plants: string[];
  is_fleet_wide: boolean;
}

interface FilterOptions {
  plant_id?: string;
  pattern_type?: string;
  min_confidence?: number;
}

interface SortOptions {
  sort_by: 'confidence_pct' | 'first_observed_date' | 'significance_score';
  sort_order: 'asc' | 'desc';
}

interface PaginationOptions {
  skip: number;
  limit: number;
}

interface PatternListProps {
  onPatternSelected?: (pattern: Pattern) => void;
  onFilterChanged?: (filters: FilterOptions) => void;
  onSortChanged?: (sort: SortOptions) => void;
  onPageChanged?: (pagination: PaginationOptions) => void;
}

export const PatternList: React.FC<PatternListProps> = ({
  onPatternSelected,
  onFilterChanged,
  onSortChanged,
  onPageChanged,
}) => {
  // State management
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);

  // Filter state
  const [filters, setFilters] = useState<FilterOptions>({});
  const [patternTypeFilter, setPatternTypeFilter] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState(0);
  const [plantIdFilter, setPlantIdFilter] = useState('');

  // Sort state
  const [sortBy, setSortBy] = useState<SortOptions['sort_by']>('confidence_pct');
  const [sortOrder, setSortOrder] = useState<SortOptions['sort_order']>('desc');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  /**
   * Fetch patterns from API with current filters, sort, and pagination
   */
  const fetchPatterns = useCallback(async () => {
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
      if (filters.pattern_type) params.append('pattern_type', filters.pattern_type);
      if (filters.min_confidence) params.append('min_confidence', filters.min_confidence.toString());

      const response = await fetch(`/api/patterns?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch patterns: ${response.statusText}`);
      }

      const data = await response.json();
      setPatterns(data.patterns || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setPatterns([]);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, sortBy, sortOrder, filters]);

  /**
   * Fetch patterns on mount and when dependencies change
   */
  useEffect(() => {
    fetchPatterns();
  }, [fetchPatterns]);

  /**
   * Handle filter changes
   */
  const handleFilterChange = useCallback(() => {
    const newFilters: FilterOptions = {};
    if (patternTypeFilter) newFilters.pattern_type = patternTypeFilter;
    if (confidenceFilter > 0) newFilters.min_confidence = confidenceFilter;
    if (plantIdFilter) newFilters.plant_id = plantIdFilter;

    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page

    if (onFilterChanged) {
      onFilterChanged(newFilters);
    }
  }, [patternTypeFilter, confidenceFilter, plantIdFilter, onFilterChanged]);

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
   * Handle pattern selection
   */
  const handlePatternSelect = useCallback((pattern: Pattern) => {
    setSelectedPattern(pattern);
    if (onPatternSelected) {
      onPatternSelected(pattern);
    }
  }, [onPatternSelected]);

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
   * Get pattern type label
   */
  const getPatternTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      seasonal: 'Seasonal',
      weekly_cycle: 'Weekly Cycle',
      degradation: 'Degradation',
    };
    return labels[type] || type;
  };

  /**
   * Get pattern type CSS class
   */
  const getPatternTypeClass = (type: string): string => {
    return `pattern-type-${type}`;
  };

  /**
   * Calculate total pages
   */
  const totalPages = Math.ceil(totalCount / pageSize);

  /**
   * Render loading state
   */
  if (loading && patterns.length === 0) {
    return (
      <div className="pattern-list-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading patterns...</p>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="pattern-list-container">
        <div className="error-state">
          <p className="error-message">Error loading patterns: {error}</p>
          <button onClick={() => fetchPatterns()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  /**
   * Render empty state
   */
  if (patterns.length === 0) {
    return (
      <div className="pattern-list-container">
        <div className="filter-section">
          <h2>Detected Patterns</h2>
          <div className="filter-group">
            <select
              value={patternTypeFilter}
              onChange={(e) => setPatternTypeFilter(e.target.value)}
              onBlur={handleFilterChange}
              aria-label="Filter by pattern type"
            >
              <option value="">All Types</option>
              <option value="seasonal">Seasonal</option>
              <option value="weekly_cycle">Weekly Cycle</option>
              <option value="degradation">Degradation</option>
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
            />
            <button
              onClick={() => {
                setPatternTypeFilter('');
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
        <div className="empty-state">
          <p>No patterns detected. Try adjusting your filters.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pattern-list-container">
      {/* Header and Filters */}
      <div className="filter-section">
        <h2>Detected Patterns</h2>
        <div className="filter-group">
          <select
            value={patternTypeFilter}
            onChange={(e) => setPatternTypeFilter(e.target.value)}
            onBlur={handleFilterChange}
            aria-label="Filter by pattern type"
            className="filter-select"
          >
            <option value="">All Types</option>
            <option value="seasonal">Seasonal</option>
            <option value="weekly_cycle">Weekly Cycle</option>
            <option value="degradation">Degradation</option>
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

          <button
            onClick={() => {
              setPatternTypeFilter('');
              setConfidenceFilter(0);
              setPlantIdFilter('');
              setFilters({});
              setCurrentPage(1);
            }}
            className="clear-filters-button"
            aria-label="Clear all filters"
          >
            Clear Filters
          </button>
        </div>
        <div className="filter-results">
          Showing {(currentPage - 1) * pageSize + 1} to{' '}
          {Math.min(currentPage * pageSize, totalCount)} of {totalCount} patterns
        </div>
      </div>

      {/* Main Content */}
      <div className="pattern-list-main">
        {/* Table */}
        <div className="table-wrapper">
          <table className="pattern-table" role="grid">
            <thead>
              <tr role="row">
                <th role="columnheader">
                  <button
                    onClick={() => handleSortChange('confidence_pct')}
                    className={sortBy === 'confidence_pct' ? 'active' : ''}
                    aria-label="Sort by confidence"
                  >
                    Confidence {sortBy === 'confidence_pct' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </button>
                </th>
                <th role="columnheader">Pattern Type</th>
                <th role="columnheader">Description</th>
                <th role="columnheader">
                  <button
                    onClick={() => handleSortChange('first_observed_date')}
                    className={sortBy === 'first_observed_date' ? 'active' : ''}
                    aria-label="Sort by date"
                  >
                    Detected {sortBy === 'first_observed_date' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </button>
                </th>
                <th role="columnheader">
                  <button
                    onClick={() => handleSortChange('significance_score')}
                    className={sortBy === 'significance_score' ? 'active' : ''}
                    aria-label="Sort by significance"
                  >
                    Significance {sortBy === 'significance_score' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </button>
                </th>
                <th role="columnheader">Occurrences</th>
              </tr>
            </thead>
            <tbody>
              {patterns.map((pattern) => (
                <tr
                  key={pattern.pattern_id}
                  onClick={() => handlePatternSelect(pattern)}
                  className={selectedPattern?.pattern_id === pattern.pattern_id ? 'selected' : ''}
                  role="row"
                  tabIndex={0}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handlePatternSelect(pattern);
                    }
                  }}
                >
                  <td role="gridcell">
                    <div className="confidence-cell">
                      <span className="confidence-value">{pattern.confidence_pct.toFixed(1)}%</span>
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{ width: `${pattern.confidence_pct}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td role="gridcell">
                    <span className={`pattern-badge ${getPatternTypeClass(pattern.pattern_type)}`}>
                      {getPatternTypeLabel(pattern.pattern_type)}
                    </span>
                  </td>
                  <td role="gridcell" className="description-cell">
                    <div className="description-text">{pattern.description}</div>
                  </td>
                  <td role="gridcell">
                    {formatDate(pattern.first_observed_date)}
                    {pattern.is_fleet_wide && <span className="fleet-wide-badge">Fleet-wide</span>}
                  </td>
                  <td role="gridcell">
                    <span className="significance-score">{pattern.significance_score.toFixed(2)}</span>
                  </td>
                  <td role="gridcell" className="occurrence-cell">
                    {pattern.occurrence_count}x
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Details Panel */}
        {selectedPattern && (
          <div className="details-panel">
            <div className="details-header">
              <h3>Pattern Details</h3>
              <button
                onClick={() => setSelectedPattern(null)}
                className="close-button"
                aria-label="Close details panel"
              >
                ✕
              </button>
            </div>
            <div className="details-content">
              <div className="detail-group">
                <label>Pattern ID</label>
                <code className="detail-value">{selectedPattern.pattern_id}</code>
              </div>

              <div className="detail-group">
                <label>Type</label>
                <span className={`pattern-badge ${getPatternTypeClass(selectedPattern.pattern_type)}`}>
                  {getPatternTypeLabel(selectedPattern.pattern_type)}
                </span>
              </div>

              <div className="detail-group">
                <label>Metric</label>
                <span className="detail-value">{selectedPattern.metric_name}</span>
              </div>

              <div className="detail-group">
                <label>Description</label>
                <p className="detail-description">{selectedPattern.description}</p>
              </div>

              <div className="detail-group">
                <label>Confidence</label>
                <div className="confidence-detail">
                  <span className="confidence-value">{selectedPattern.confidence_pct.toFixed(1)}%</span>
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{ width: `${selectedPattern.confidence_pct}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="detail-group">
                <label>Significance Score</label>
                <span className="detail-value">{selectedPattern.significance_score.toFixed(2)}</span>
              </div>

              <div className="detail-group">
                <label>Frequency</label>
                <span className="detail-value">{selectedPattern.frequency}</span>
              </div>

              <div className="detail-group">
                <label>Amplitude</label>
                <span className="detail-value">{selectedPattern.amplitude.toFixed(2)}</span>
              </div>

              <div className="detail-group">
                <label>Detected</label>
                <span className="detail-value">{formatDate(selectedPattern.first_observed_date)}</span>
              </div>

              <div className="detail-group">
                <label>Last Observed</label>
                <span className="detail-value">{formatDate(selectedPattern.last_observed_date)}</span>
              </div>

              <div className="detail-group">
                <label>Occurrences</label>
                <span className="detail-value">{selectedPattern.occurrence_count}</span>
              </div>

              <div className="detail-group">
                <label>Plant ID</label>
                <code className="detail-value">{selectedPattern.plant_id}</code>
              </div>

              {selectedPattern.is_fleet_wide && (
                <div className="detail-group fleet-wide">
                  <span className="fleet-wide-badge">Fleet-wide Pattern</span>
                </div>
              )}

              {selectedPattern.affected_plants && selectedPattern.affected_plants.length > 0 && (
                <div className="detail-group">
                  <label>Affected Plants</label>
                  <ul className="affected-plants">
                    {selectedPattern.affected_plants.map((plantId) => (
                      <li key={plantId}>{plantId}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="pagination-section">
        <div className="pagination-controls">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="pagination-button"
            aria-label="Previous page"
          >
            Previous
          </button>

          <span className="page-indicator">
            Page {currentPage} of {totalPages || 1}
          </span>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="pagination-button"
            aria-label="Next page"
          >
            Next
          </button>
        </div>

        <div className="page-size-selector">
          <label htmlFor="page-size">Items per page:</label>
          <select
            id="page-size"
            value={pageSize}
            onChange={(e) => handlePageSizeChange(parseInt(e.target.value))}
            aria-label="Select number of items per page"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default PatternList;
