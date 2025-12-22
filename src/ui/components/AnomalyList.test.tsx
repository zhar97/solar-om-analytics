/**
 * AnomalyList Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnomalyList, { Anomaly } from './AnomalyList';

// Mock fetch
global.fetch = jest.fn();

const mockAnomalies: Anomaly[] = [
  {
    anomaly_id: 'ANOM_001',
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
    anomaly_id: 'ANOM_002',
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
];

describe('AnomalyList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: mockAnomalies,
      }),
    });
  });

  describe('Rendering', () => {
    it('should render component title', async () => {
      render(<AnomalyList />);
      expect(screen.getByText('Anomaly Detection Results')).toBeInTheDocument();
    });

    it('should display loading state initially', () => {
      render(<AnomalyList />);
      // Loading state is shown briefly
      expect(screen.queryByText(/loading/i)).toBeInTheDocument();
    });

    it('should render anomalies table after loading', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    it('should display all anomalies in table', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText('ANOM_001')).toBeInTheDocument();
        expect(screen.getByText('ANOM_002')).toBeInTheDocument();
      });
    });

    it('should display empty state when no anomalies', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          data: [],
        }),
      });

      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText(/no anomalies detected/i)).toBeInTheDocument();
      });
    });

    it('should display error message on API failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText(/HTTP 500/i)).toBeInTheDocument();
      });
    });
  });

  describe('Anomaly Details', () => {
    it('should show anomaly details when clicked', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      const detailsButton = screen.getAllByText('Details')[0];
      fireEvent.click(detailsButton);

      await waitFor(() => {
        expect(screen.getByText(/anomaly details/i)).toBeInTheDocument();
        expect(screen.getByText('2025-01-13')).toBeInTheDocument();
      });
    });

    it('should display severity badge correctly', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const highBadge = screen.getByText('high');
        expect(highBadge).toHaveClass('badge-danger');

        const mediumBadge = screen.getByText('medium');
        expect(mediumBadge).toHaveClass('badge-warning');
      });
    });

    it('should display Z-score when available', async () => {
      render(<AnomalyList />);
      const detailsButton = screen.getAllByText('Details')[0];
      fireEvent.click(detailsButton);

      await waitFor(() => {
        expect(screen.getByText('Z-Score:')).toBeInTheDocument();
      });
    });

    it('should display IQR bounds when available', async () => {
      render(<AnomalyList />);
      const detailsButtons = screen.getAllByText('Details');
      fireEvent.click(detailsButtons[1]); // Click second anomaly with IQR

      await waitFor(() => {
        expect(screen.getByText('IQR Bounds:')).toBeInTheDocument();
      });
    });
  });

  describe('Pagination', () => {
    it('should render pagination controls', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText(/page 1 of/i)).toBeInTheDocument();
      });
    });

    it('should disable previous button on first page', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /previous/i });
        expect(prevButton).toBeDisabled();
      });
    });

    it('should handle page size change', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const pageSizeSelect = screen.getByDisplayValue('10 per page');
        expect(pageSizeSelect).toBeInTheDocument();
      });

      const select = screen.getByDisplayValue('10 per page') as HTMLSelectElement;
      await userEvent.selectOptions(select, '25');

      expect(select.value).toBe('25');
    });
  });

  describe('Sorting', () => {
    it('should render sorting controls', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const sortSelect = screen.getByDisplayValue(/Date.*Newest/i);
        expect(sortSelect).toBeInTheDocument();
      });
    });

    it('should handle sort order change', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const sortSelect = screen.getByDisplayValue(/Date.*Newest/i);
        fireEvent.change(sortSelect, { target: { value: 'date-asc' } });
        expect(sortSelect).toHaveValue('date-asc');
      });
    });

    it('should sort by severity', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        const sortSelect = screen.getByDisplayValue(/Date.*Newest/i);
        fireEvent.change(sortSelect, { target: { value: 'severity-desc' } });
        expect(sortSelect).toHaveValue('severity-desc');
      });
    });
  });

  describe('Filtering', () => {
    it('should fetch with severity filter', async () => {
      render(<AnomalyList severity="high" />);
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('severity=high'));
      });
    });

    it('should fetch with metric filter', async () => {
      render(<AnomalyList metric="power_output_kwh" />);
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('metric=power_output_kwh'));
      });
    });

    it('should fetch for specific plant', async () => {
      render(<AnomalyList plant_id="PLANT_001" />);
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/anomalies/PLANT_001'));
      });
    });
  });

  describe('Chart', () => {
    it('should render anomaly timeline chart', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText('Anomaly Timeline')).toBeInTheDocument();
      });
    });

    it('should handle chart data correctly', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        // Chart should be rendered with data
        expect(screen.getByText('Expected')).toBeInTheDocument();
        expect(screen.getByText('Actual')).toBeInTheDocument();
      });
    });
  });

  describe('Callback Props', () => {
    it('should call onAnomalySelect when anomaly is selected', async () => {
      const mockCallback = jest.fn();
      render(<AnomalyList onAnomalySelect={mockCallback} />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      const detailsButton = screen.getAllByText('Details')[0];
      fireEvent.click(detailsButton);

      await waitFor(() => {
        expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({
          anomaly_id: 'ANOM_001',
        }));
      });
    });
  });

  describe('Table Columns', () => {
    it('should display all required table columns', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText('Date')).toBeInTheDocument();
        expect(screen.getByText('Metric')).toBeInTheDocument();
        expect(screen.getByText('Actual')).toBeInTheDocument();
        expect(screen.getByText('Expected')).toBeInTheDocument();
        expect(screen.getByText('Deviation %')).toBeInTheDocument();
        expect(screen.getByText('Severity')).toBeInTheDocument();
        expect(screen.getByText('Detected By')).toBeInTheDocument();
      });
    });

    it('should format decimal values correctly', async () => {
      render(<AnomalyList />);
      await waitFor(() => {
        expect(screen.getByText('250.00')).toBeInTheDocument(); // actual_value
        expect(screen.getByText('453.32')).toBeInTheDocument(); // expected_value
      });
    });
  });
});
