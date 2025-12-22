/**
 * Integration tests for PatternList component
 * Tests component integration with API, layout, and multiple features working together
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatternList } from './PatternList';

global.fetch = jest.fn();

const mockPatterns = [
  {
    pattern_id: 'pat-seasonal-001',
    plant_id: 'plant-001',
    pattern_type: 'seasonal' as const,
    metric_name: 'power_output_kwh',
    description: 'Summer peak production',
    frequency: 'monthly',
    amplitude: 45.5,
    significance_score: 8.7,
    confidence_pct: 92.5,
    first_observed_date: '2023-01-15',
    last_observed_date: '2024-12-20',
    occurrence_count: 24,
    affected_plants: ['plant-001', 'plant-002'],
    is_fleet_wide: false,
  },
  {
    pattern_id: 'pat-weekly-001',
    plant_id: 'plant-001',
    pattern_type: 'weekly_cycle' as const,
    metric_name: 'power_output_kwh',
    description: 'Weekend drop',
    frequency: 'weekly',
    amplitude: 15.3,
    significance_score: 6.2,
    confidence_pct: 85.0,
    first_observed_date: '2023-06-10',
    last_observed_date: '2024-12-15',
    occurrence_count: 78,
    affected_plants: ['plant-001'],
    is_fleet_wide: false,
  },
  {
    pattern_id: 'pat-degradation-001',
    plant_id: 'plant-002',
    pattern_type: 'degradation' as const,
    metric_name: 'efficiency_pct',
    description: 'System degradation',
    frequency: 'annual',
    amplitude: 3.2,
    significance_score: 7.1,
    confidence_pct: 78.5,
    first_observed_date: '2023-01-01',
    last_observed_date: '2024-12-31',
    occurrence_count: 12,
    affected_plants: ['plant-002', 'plant-003', 'plant-004'],
    is_fleet_wide: true,
  },
];

describe('PatternList Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ patterns: mockPatterns, total: 3 }),
    });
  });

  describe('Complete User Workflow', () => {
    test('user can filter, sort, and view pattern details in sequence', async () => {
      render(<PatternList />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
      });

      // 1. View initial patterns
      expect(screen.getByText('Seasonal')).toBeInTheDocument();
      expect(screen.getByText('Weekly Cycle')).toBeInTheDocument();

      // 2. Filter by pattern type
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('pattern_type=seasonal'))).toBe(true);
      });

      // 3. Sort by confidence
      const sortButton = screen.getByLabelText('Sort by confidence');
      fireEvent.click(sortButton);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('sort_by=confidence_pct'))).toBe(true);
      });

      // 4. Change page size
      const pageSize = screen.getByLabelText('Select number of items per page');
      await userEvent.selectOptions(pageSize, '25');

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('limit=25'))).toBe(true);
      });

      // 5. Select a pattern to view details
      const seasonalBadge = screen.getByText('Seasonal');
      const row = seasonalBadge.closest('tr');
      fireEvent.click(row!);

      await waitFor(() => {
        expect(screen.getByText('Pattern Details')).toBeInTheDocument();
        expect(screen.getByText('pat-seasonal-001')).toBeInTheDocument();
      });
    });
  });

  describe('Filter and Sort Combination', () => {
    test('filtering and sorting work together', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Apply filter
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      // Apply sort
      const sortButton = screen.getByLabelText('Sort by confidence');
      fireEvent.click(sortButton);

      await waitFor(() => {
        const lastCall = (global.fetch as jest.Mock).mock.calls[
          (global.fetch as jest.Mock).mock.calls.length - 1
        ][0];
        expect(lastCall).toContain('pattern_type=seasonal');
        expect(lastCall).toContain('sort_by=confidence_pct');
      });
    });

    test('filtering, sorting, and pagination work together', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Set filter
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      // Set sort
      const sortButton = screen.getByLabelText('Sort by confidence');
      fireEvent.click(sortButton);

      // Change page
      const nextButton = screen.getByLabelText('Next page');
      fireEvent.click(nextButton);

      await waitFor(() => {
        const lastCall = (global.fetch as jest.Mock).mock.calls[
          (global.fetch as jest.Mock).mock.calls.length - 1
        ][0];
        expect(lastCall).toContain('pattern_type=seasonal');
        expect(lastCall).toContain('sort_by=confidence_pct');
        expect(lastCall).toContain('skip=10');
      });
    });
  });

  describe('Pagination with Filters', () => {
    test('pagination resets when filters change', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Go to page 2
      const nextButton = screen.getByLabelText('Next page');
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Page 2/)).toBeInTheDocument();
      });

      // Apply filter (should reset to page 1)
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        const lastCall = (global.fetch as jest.Mock).mock.calls[
          (global.fetch as jest.Mock).mock.calls.length - 1
        ][0];
        expect(lastCall).toContain('skip=0');
      });
    });
  });

  describe('Error Handling and Recovery', () => {
    test('can recover from API error with retry', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Server Error',
      });

      const { rerender } = render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText(/Error loading patterns/)).toBeInTheDocument();
      });

      // Mock success for retry
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: mockPatterns, total: 3 }),
      });

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });
    });

    test('handles switching between empty and populated states', async () => {
      const { rerender } = render(<PatternList />);

      // Start with data
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Mock empty response
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: [], total: 0 }),
      });

      const clearButton = screen.getByText('Clear Filters');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.queryByText('Seasonal')).not.toBeInTheDocument();
      });
    });
  });

  describe('Details Panel Persistence', () => {
    test('details panel updates when selecting different patterns', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Select first pattern
      let seasonalBadge = screen.getByText('Seasonal');
      let row = seasonalBadge.closest('tr');
      fireEvent.click(row!);

      await waitFor(() => {
        expect(screen.getByText('pat-seasonal-001')).toBeInTheDocument();
      });

      // Select second pattern
      const weeklyBadge = screen.getByText('Weekly Cycle');
      row = weeklyBadge.closest('tr');
      fireEvent.click(row!);

      await waitFor(() => {
        expect(screen.getByText('pat-weekly-001')).toBeInTheDocument();
      });
    });

    test('details panel closes and stays closed', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Open details
      const seasonalBadge = screen.getByText('Seasonal');
      const row = seasonalBadge.closest('tr');
      fireEvent.click(row!);

      await waitFor(() => {
        expect(screen.getByText('Pattern Details')).toBeInTheDocument();
      });

      // Close details
      const closeButton = screen.getByLabelText('Close details panel');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Pattern Details')).not.toBeInTheDocument();
      });

      // Verify it stays closed after sorting
      const sortButton = screen.getByLabelText('Sort by confidence');
      fireEvent.click(sortButton);

      // Details should still be closed
      expect(screen.queryByText('Pattern Details')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    test('keyboard navigation through patterns', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Tab to first pattern row
      const seasonalBadge = screen.getByText('Seasonal');
      const row = seasonalBadge.closest('tr');

      // Press Enter to select
      if (row) {
        fireEvent.keyPress(row, { key: 'Enter', code: 'Enter', charCode: 13 });
      }

      await waitFor(() => {
        expect(screen.getByText('Pattern Details')).toBeInTheDocument();
      });
    });

    test('keyboard interaction with filters', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Min Confidence (%)')).toBeInTheDocument();
      });

      const confidenceInput = screen.getByPlaceholderText('Min Confidence (%)');
      confidenceInput.focus();
      expect(document.activeElement).toBe(confidenceInput);
    });
  });

  describe('Data Consistency', () => {
    test('API is called with correct parameters on each interaction', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const initialCallCount = (global.fetch as jest.Mock).mock.calls.length;

      // Make a change
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(initialCallCount);
      });

      const lastCall = (global.fetch as jest.Mock).mock.calls[
        (global.fetch as jest.Mock).mock.calls.length - 1
      ][0];

      // Verify all expected parameters are present
      expect(lastCall).toContain('skip=');
      expect(lastCall).toContain('limit=');
      expect(lastCall).toContain('sort_by=');
      expect(lastCall).toContain('sort_order=');
      expect(lastCall).toContain('pattern_type=seasonal');
    });

    test('displayed data matches API response', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      // Check all patterns from mock data are displayed
      mockPatterns.forEach((pattern) => {
        expect(screen.getByText(pattern.confidence_pct.toFixed(1) + '%')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Layout Behavior', () => {
    test('layout is visible and functional on all viewports', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
      });

      // Verify key elements are present
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Clear Filters')).toBeInTheDocument();
      expect(screen.getByLabelText('Next page')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('handles large dataset gracefully', async () => {
      const largeDataset = Array.from({ length: 100 }, (_, i) => ({
        ...mockPatterns[i % 3],
        pattern_id: `pat-${i}`,
      }));

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: largeDataset.slice(0, 10), total: 100 }),
      });

      render(<PatternList />);

      await waitFor(() => {
        // Should still render efficiently
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    test('pagination prevents rendering too many items', async () => {
      const largeDataset = Array.from({ length: 25 }, (_, i) => ({
        ...mockPatterns[i % 3],
        pattern_id: `pat-${i}`,
      }));

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: largeDataset, total: 250 }),
      });

      render(<PatternList />);

      await waitFor(() => {
        expect(screen.getByText(/of 250 patterns/)).toBeInTheDocument();
      });

      // Only the paginated amount should be rendered
      const rows = screen.getAllByRole('row');
      // Header row + up to 10 data rows (default page size)
      expect(rows.length).toBeLessThanOrEqual(11);
    });
  });
});
