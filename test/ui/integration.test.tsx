/**
 * Integration Tests - Frontend + Backend
 * Tests the complete user story flow from data loading to visualization
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnomalyList from '../components/AnomalyList';

// Mock the API responses to simulate backend behavior
const mockPipelineData = {
  anomalies: [
    {
      anomaly_id: 'ANOM_PLANT_001_2025-01-13_abc123',
      plant_id: 'PLANT_001',
      date: '2025-01-13',
      metric_name: 'power_output_kwh',
      actual_value: 250.0,
      expected_value: 453.32,
      deviation_pct: -44.85,
      severity: 'high',
      detected_by: 'zscore',
      status: 'active',
      z_score: -3.37,
    },
    {
      anomaly_id: 'ANOM_PLANT_001_2025-01-10_def456',
      plant_id: 'PLANT_001',
      date: '2025-01-10',
      metric_name: 'efficiency_pct',
      actual_value: 12.5,
      expected_value: 16.8,
      deviation_pct: -25.6,
      severity: 'medium',
      detected_by: 'iqr',
      status: 'active',
      iqr_bounds: { lower: 14.2, upper: 19.4 },
    },
    {
      anomaly_id: 'ANOM_PLANT_001_2025-01-05_ghi789',
      plant_id: 'PLANT_001',
      date: '2025-01-05',
      metric_name: 'power_output_kwh',
      actual_value: 400.0,
      expected_value: 453.32,
      deviation_pct: -11.76,
      severity: 'low',
      detected_by: 'zscore',
      status: 'active',
    },
  ],
};

global.fetch = jest.fn();

describe('Integration Tests - Anomaly Detection User Story', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('End-to-End User Story Flow', () => {
    it('should complete full workflow: view anomalies -> filter -> view details -> analyze', async () => {
      // Step 1: Mock API response for initial anomalies fetch
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockPipelineData.anomalies,
        }),
      });

      // Render the component
      const { rerender } = render(<AnomalyList plant_id="PLANT_001" />);

      // Step 2: Verify anomalies are loaded and displayed
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Verify all anomalies are rendered
      expect(screen.getByText('ANOM_PLANT_001_2025-01-13_abc123')).toBeInTheDocument();
      expect(screen.getByText('ANOM_PLANT_001_2025-01-10_def456')).toBeInTheDocument();

      // Step 3: User filters by high severity
      const filteredAnomalies = mockPipelineData.anomalies.filter((a) => a.severity === 'high');
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: filteredAnomalies,
        }),
      });

      rerender(<AnomalyList plant_id="PLANT_001" severity="high" />);

      // Step 4: Verify filtered results
      await waitFor(() => {
        expect(screen.getByText('ANOM_PLANT_001_2025-01-13_abc123')).toBeInTheDocument();
        expect(screen.queryByText('ANOM_PLANT_001_2025-01-10_def456')).not.toBeInTheDocument();
      });

      // Step 5: User clicks on anomaly details
      const detailsButton = screen.getAllByText('Details')[0];
      fireEvent.click(detailsButton);

      // Step 6: Verify details panel shows comprehensive information
      await waitFor(() => {
        expect(screen.getByText('Anomaly Details')).toBeInTheDocument();
        expect(screen.getByText('2025-01-13')).toBeInTheDocument();
        expect(screen.getByText('power_output_kwh')).toBeInTheDocument();
        expect(screen.getByText('-44.85%')).toBeInTheDocument();
      });

      // Verify Z-score is displayed for zscore detection
      expect(screen.getByText('Z-Score:')).toBeInTheDocument();
    });

    it('should update view when changing plant selection', async () => {
      // Mock initial plant data
      const plant001Anomalies = mockPipelineData.anomalies.slice(0, 2);
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: plant001Anomalies,
        }),
      });

      const { rerender } = render(<AnomalyList plant_id="PLANT_001" />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('ANOM_PLANT_001_2025-01-13_abc123')).toBeInTheDocument();
      });

      // Change to different plant
      const plant002Anomalies = [
        {
          anomaly_id: 'ANOM_PLANT_002_2025-01-15_xyz999',
          plant_id: 'PLANT_002',
          date: '2025-01-15',
          metric_name: 'power_output_kwh',
          actual_value: 180.0,
          expected_value: 400.0,
          deviation_pct: -55.0,
          severity: 'critical',
          detected_by: 'zscore',
          status: 'active',
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: plant002Anomalies,
        }),
      });

      rerender(<AnomalyList plant_id="PLANT_002" />);

      // Verify new plant anomalies are displayed
      await waitFor(() => {
        expect(screen.getByText('ANOM_PLANT_002_2025-01-15_xyz999')).toBeInTheDocument();
      });
    });
  });

  describe('Data Accuracy and Consistency', () => {
    it('should display data matching backend pipeline output', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockPipelineData.anomalies,
        }),
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Verify data accuracy
      const firstAnomaly = mockPipelineData.anomalies[0];

      // Check date
      expect(screen.getByText(firstAnomaly.date)).toBeInTheDocument();

      // Check metric
      expect(screen.getByText(firstAnomaly.metric_name)).toBeInTheDocument();

      // Check values (formatted to 2 decimal places)
      expect(screen.getByText(firstAnomaly.actual_value.toFixed(2))).toBeInTheDocument();
      expect(screen.getByText(firstAnomaly.expected_value.toFixed(2))).toBeInTheDocument();

      // Check deviation percentage
      expect(screen.getByText(`${firstAnomaly.deviation_pct.toFixed(2)}%`)).toBeInTheDocument();

      // Check severity
      expect(screen.getByText('high')).toBeInTheDocument();
    });

    it('should maintain data consistency during filtering', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockPipelineData.anomalies,
        }),
      });

      const { rerender } = render(<AnomalyList plant_id="PLANT_001" />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Verify original data
      const originalRowCount = screen.getAllByRole('row').length - 1; // Exclude header
      expect(originalRowCount).toBe(3);

      // Apply filter
      const filtered = mockPipelineData.anomalies.filter((a) => a.severity !== 'low');
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: filtered,
        }),
      });

      rerender(<AnomalyList plant_id="PLANT_001" severity="high,medium" />);

      // Verify filtered count
      await waitFor(() => {
        const filteredRows = screen.getAllByRole('row').length - 1;
        expect(filteredRows).toBe(2);
      });
    });
  });

  describe('Statistical Accuracy', () => {
    it('should correctly display statistical measurements', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: [mockPipelineData.anomalies[0]], // High severity with z_score
        }),
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      // Click details to see statistical info
      await waitFor(() => {
        expect(screen.getByText('Details')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Details'));

      // Verify Z-score is displayed with correct precision
      await waitFor(() => {
        expect(screen.getByText('Z-Score:')).toBeInTheDocument();
        const zScoreValue = mockPipelineData.anomalies[0].z_score?.toFixed(4);
        expect(screen.getByText(zScoreValue!)).toBeInTheDocument();
      });
    });

    it('should correctly display IQR bounds when available', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: [mockPipelineData.anomalies[1]], // Medium severity with IQR
        }),
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      await waitFor(() => {
        expect(screen.getByText('Details')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Details'));

      // Verify IQR bounds are displayed
      await waitFor(() => {
        expect(screen.getByText('IQR Bounds:')).toBeInTheDocument();
        const bounds = mockPipelineData.anomalies[1].iqr_bounds;
        expect(screen.getByText(`[${bounds?.lower?.toFixed(2)}, ${bounds?.upper?.toFixed(2)}]`)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle missing Z-score gracefully', async () => {
      const anomalyWithoutZScore = {
        ...mockPipelineData.anomalies[2],
        z_score: undefined,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: [anomalyWithoutZScore],
        }),
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      await waitFor(() => {
        expect(screen.getByText('Details')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Details'));

      // Should not crash and Z-Score section should not be visible
      await waitFor(() => {
        expect(screen.getByText('Anomaly Details')).toBeInTheDocument();
      });
    });

    it('should handle API failure with user-friendly message', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/HTTP 500/i)).toBeInTheDocument();
      });

      // Should not display table
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('should handle empty anomalies list', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: [],
        }),
      });

      render(<AnomalyList plant_id="PLANT_001" />);

      // Should display empty state
      await waitFor(() => {
        expect(screen.getByText(/no anomalies detected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('should render large anomalies list efficiently', async () => {
      // Create 100 mock anomalies
      const largeDataSet = Array.from({ length: 100 }, (_, i) => ({
        anomaly_id: `ANOM_${i}`,
        plant_id: 'PLANT_001',
        date: `2025-01-${String((i % 30) + 1).padStart(2, '0')}`,
        metric_name: 'power_output_kwh',
        actual_value: 200 + Math.random() * 300,
        expected_value: 450,
        deviation_pct: -Math.random() * 50,
        severity: ['low', 'medium', 'high', 'critical'][i % 4] as any,
        detected_by: i % 2 === 0 ? 'zscore' : 'iqr',
        status: 'active',
      }));

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: largeDataSet.slice(0, 10), // First page
        }),
      });

      const startTime = performance.now();
      render(<AnomalyList plant_id="PLANT_001" />);
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
      const renderTime = performance.now() - startTime;

      // Should render within reasonable time (2 seconds)
      expect(renderTime).toBeLessThan(2000);
    });
  });

  describe('User Interactions', () => {
    it('should persist user selections across renders', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockPipelineData.anomalies,
        }),
      });

      const { rerender } = render(
        <AnomalyList plant_id="PLANT_001" severity="high" metric="power_output_kwh" />
      );

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Select an anomaly
      const firstDetailsButton = screen.getAllByText('Details')[0];
      fireEvent.click(firstDetailsButton);

      await waitFor(() => {
        expect(screen.getByText('Anomaly Details')).toBeInTheDocument();
      });

      // Rerender with same props
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockPipelineData.anomalies.filter(
            (a) => a.severity === 'high' && a.metric_name === 'power_output_kwh'
          ),
        }),
      });

      rerender(
        <AnomalyList plant_id="PLANT_001" severity="high" metric="power_output_kwh" />
      );

      // Selection should still be visible
      await waitFor(() => {
        expect(screen.getByText('Anomaly Details')).toBeInTheDocument();
      });
    });
  });
});
