/**
 * AnomalyList Component
 * Displays a paginated list of anomalies detected for a solar plant
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar } from 'recharts';

export interface Anomaly {
  anomaly_id: string;
  plant_id: string;
  date: string;
  metric_name: string;
  actual_value: number;
  expected_value: number;
  deviation_pct: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  detected_by: 'zscore' | 'iqr';
  status: string;
  z_score?: number;
  iqr_bounds?: { lower: number; upper: number };
}

export interface AnomalyListProps {
  plant_id?: string;
  severity?: string;
  metric?: string;
  onAnomalySelect?: (anomaly: Anomaly) => void;
}

const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'low':
      return '#4CAF50';
    case 'medium':
      return '#FF9800';
    case 'high':
      return '#FF5722';
    case 'critical':
      return '#9C27B0';
    default:
      return '#9E9E9E';
  }
};

const getSeverityBadgeClass = (severity: string): string => {
  switch (severity) {
    case 'low':
      return 'badge-success';
    case 'medium':
      return 'badge-warning';
    case 'high':
      return 'badge-danger';
    case 'critical':
      return 'badge-critical';
    default:
      return 'badge-secondary';
  }
};

export const AnomalyList: React.FC<AnomalyListProps> = ({
  plant_id,
  severity: severityFilter,
  metric: metricFilter,
  onAnomalySelect,
}) => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'severity'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fetch anomalies from API
  useEffect(() => {
    const fetchAnomalies = async () => {
      setLoading(true);
      setError(null);
      try {
        let url = '/api/anomalies';
        if (plant_id) {
          url += `/${plant_id}`;
        }

        const params = new URLSearchParams();
        params.append('skip', String(page * pageSize));
        params.append('limit', String(pageSize));
        params.append('sort', sortBy);
        params.append('order', sortOrder);

        if (severityFilter) {
          params.append('severity', severityFilter);
        }
        if (metricFilter) {
          params.append('metric', metricFilter);
        }

        const response = await fetch(`${url}?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        if (!data.success) {
          throw new Error(data.error || 'Failed to fetch anomalies');
        }

        setAnomalies(data.data || []);
        setTotalCount(data.data?.length || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
        setAnomalies([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAnomalies();
  }, [plant_id, page, pageSize, sortBy, sortOrder, severityFilter, metricFilter]);

  const handleAnomalyClick = (anomaly: Anomaly) => {
    setSelectedAnomaly(anomaly);
    if (onAnomalySelect) {
      onAnomalySelect(anomaly);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);
  const hasNextPage = page < totalPages - 1;
  const hasPrevPage = page > 0;

  // Prepare data for visualization
  const chartData = anomalies
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((anom) => ({
      date: anom.date,
      actual: anom.actual_value,
      expected: anom.expected_value,
      anomaly_id: anom.anomaly_id,
      severity: anom.severity,
    }));

  return (
    <div className="anomaly-list-container">
      <div className="anomaly-header">
        <h2>Anomaly Detection Results</h2>
        <div className="controls">
          <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
          </select>
          <select value={`${sortBy}-${sortOrder}`} onChange={(e) => {
            const [sort, order] = e.target.value.split('-');
            setSortBy(sort as 'date' | 'severity');
            setSortOrder(order as 'asc' | 'desc');
          }}>
            <option value="date-desc">Date (Newest First)</option>
            <option value="date-asc">Date (Oldest First)</option>
            <option value="severity-desc">Severity (Critical First)</option>
            <option value="severity-asc">Severity (Low First)</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading && <div className="loading">Loading anomalies...</div>}

      {!loading && anomalies.length === 0 && !error && (
        <div className="empty-state">No anomalies detected for the selected criteria.</div>
      )}

      {!loading && anomalies.length > 0 && (
        <>
          {/* Chart View */}
          <div className="anomaly-chart">
            <h3>Anomaly Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
                <YAxis label={{ value: 'Power Output (kWh)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="chart-tooltip">
                          <p>{data.date}</p>
                          <p>Expected: {data.expected.toFixed(2)} kWh</p>
                          <p>Actual: {data.actual.toFixed(2)} kWh</p>
                          <p className={`severity-${data.severity}`}>Severity: {data.severity}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="expected" stroke="#4CAF50" name="Expected" />
                <Line type="monotone" dataKey="actual" stroke="#FF5722" name="Actual" isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Table View */}
          <div className="anomaly-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Metric</th>
                  <th>Actual</th>
                  <th>Expected</th>
                  <th>Deviation %</th>
                  <th>Severity</th>
                  <th>Detected By</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((anomaly) => (
                  <tr
                    key={anomaly.anomaly_id}
                    className={`anomaly-row ${selectedAnomaly?.anomaly_id === anomaly.anomaly_id ? 'selected' : ''}`}
                    onClick={() => handleAnomalyClick(anomaly)}
                  >
                    <td>{anomaly.date}</td>
                    <td>{anomaly.metric_name}</td>
                    <td>{anomaly.actual_value.toFixed(2)}</td>
                    <td>{anomaly.expected_value.toFixed(2)}</td>
                    <td className={`deviation-${anomaly.deviation_pct < 0 ? 'negative' : 'positive'}`}>
                      {anomaly.deviation_pct.toFixed(2)}%
                    </td>
                    <td>
                      <span className={`badge ${getSeverityBadgeClass(anomaly.severity)}`}>
                        {anomaly.severity}
                      </span>
                    </td>
                    <td>{anomaly.detected_by.toUpperCase()}</td>
                    <td>
                      <button
                        className="btn-small btn-detail"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAnomalyClick(anomaly);
                        }}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button disabled={!hasPrevPage} onClick={() => setPage(Math.max(0, page - 1))}>
              Previous
            </button>
            <span className="page-info">
              Page {page + 1} of {totalPages} ({totalCount} total)
            </span>
            <button disabled={!hasNextPage} onClick={() => setPage(page + 1)}>
              Next
            </button>
          </div>

          {/* Details Panel */}
          {selectedAnomaly && (
            <div className="anomaly-details">
              <h3>Anomaly Details</h3>
              <div className="details-grid">
                <div className="detail-item">
                  <label>ID:</label>
                  <span>{selectedAnomaly.anomaly_id}</span>
                </div>
                <div className="detail-item">
                  <label>Plant ID:</label>
                  <span>{selectedAnomaly.plant_id}</span>
                </div>
                <div className="detail-item">
                  <label>Date:</label>
                  <span>{selectedAnomaly.date}</span>
                </div>
                <div className="detail-item">
                  <label>Metric:</label>
                  <span>{selectedAnomaly.metric_name}</span>
                </div>
                <div className="detail-item">
                  <label>Actual Value:</label>
                  <span>{selectedAnomaly.actual_value.toFixed(4)}</span>
                </div>
                <div className="detail-item">
                  <label>Expected Value:</label>
                  <span>{selectedAnomaly.expected_value.toFixed(4)}</span>
                </div>
                <div className="detail-item">
                  <label>Deviation:</label>
                  <span>{selectedAnomaly.deviation_pct.toFixed(2)}%</span>
                </div>
                <div className="detail-item">
                  <label>Severity:</label>
                  <span className={`badge ${getSeverityBadgeClass(selectedAnomaly.severity)}`}>
                    {selectedAnomaly.severity}
                  </span>
                </div>
                <div className="detail-item">
                  <label>Detected By:</label>
                  <span>{selectedAnomaly.detected_by.toUpperCase()}</span>
                </div>
                {selectedAnomaly.z_score !== undefined && (
                  <div className="detail-item">
                    <label>Z-Score:</label>
                    <span>{selectedAnomaly.z_score.toFixed(4)}</span>
                  </div>
                )}
                {selectedAnomaly.iqr_bounds && (
                  <div className="detail-item">
                    <label>IQR Bounds:</label>
                    <span>
                      [{selectedAnomaly.iqr_bounds.lower?.toFixed(2)}, {selectedAnomaly.iqr_bounds.upper?.toFixed(2)}]
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AnomalyList;
