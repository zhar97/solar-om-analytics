/**
 * Unit tests for PatternList React component
 * Tests component rendering, filtering, sorting, pagination, and API integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatternList } from './PatternList';

// Mock fetch
global.fetch = jest.fn();

// Sample test data
const mockPatterns = [
  {
    pattern_id: 'pat-001',
    plant_id: 'plant-001',
    pattern_type: 'seasonal' as const,
    metric_name: 'power_output_kwh',
    description: 'Strong seasonal variation with peak in summer',
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
    pattern_id: 'pat-002',
    plant_id: 'plant-001',
    pattern_type: 'weekly_cycle' as const,
    metric_name: 'power_output_kwh',
    description: 'Weekly cycle with lower output on weekends',
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
    pattern_id: 'pat-003',
    plant_id: 'plant-002',
    pattern_type: 'degradation' as const,
    metric_name: 'efficiency_pct',
    description: 'Gradual efficiency decline over time',
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

describe('PatternList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ patterns: mockPatterns, total: 3 }),
    });
  });

  describe('Initialization and Rendering', () => {
    test('renders loading state initially', () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );
      render(<PatternList />);
      expect(screen.getByText('Loading patterns...')).toBeInTheDocument();
    });

    test('renders component without crash', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
      });
    });

    test('displays title on mount', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
      });
    });

    test('shows error state on API failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Server Error',
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Error loading patterns/)).toBeInTheDocument();
      });
    });

    test('shows empty state when no patterns', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: [], total: 0 }),
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/No patterns detected/)).toBeInTheDocument();
      });
    });

    test('displays retry button on error', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Error',
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });
    });
  });

  describe('Data Display', () => {
    test('displays pattern table', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    test('displays pattern type column', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Pattern Type')).toBeInTheDocument();
      });
    });

    test('displays confidence column', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Confidence/)).toBeInTheDocument();
      });
    });

    test('displays all pattern types with badges', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
        expect(screen.getByText('Weekly Cycle')).toBeInTheDocument();
        expect(screen.getByText('Degradation')).toBeInTheDocument();
      });
    });

    test('formats dates correctly', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Jan 15, 2023')).toBeInTheDocument();
      });
    });

    test('displays confidence percentage with % symbol', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('92.5%')).toBeInTheDocument();
      });
    });

    test('displays occurrence count', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('24x')).toBeInTheDocument();
      });
    });

    test('displays fleet-wide badge for fleet patterns', async () => {
      render(<PatternList />);
      await waitFor(() => {
        const badges = screen.getAllByText('Fleet-wide');
        expect(badges.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Filtering', () => {
    test('filter by pattern type dropdown exists', async () => {
      render(<PatternList />);
      await waitFor(() => {
        const selects = screen.getAllByRole('combobox');
        expect(selects[0]).toBeInTheDocument();
      });
    });

    test('filter by confidence input exists', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Min Confidence (%)')).toBeInTheDocument();
      });
    });

    test('clear filters button exists', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Clear Filters')).toBeInTheDocument();
      });
    });

    test('filtering by pattern type updates API call', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('pattern_type=seasonal'))).toBe(true);
      });
    });

    test('filtering by confidence updates API call', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Min Confidence (%)')).toBeInTheDocument();
      });

      const confidenceInput = screen.getByPlaceholderText('Min Confidence (%)');
      await userEvent.type(confidenceInput, '80');
      fireEvent.blur(confidenceInput);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('min_confidence=80'))).toBe(true);
      });
    });

    test('clear filters resets all filters', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Min Confidence (%)')).toBeInTheDocument();
      });

      // Set filters
      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');

      // Clear filters
      const clearButton = screen.getByText('Clear Filters');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect((typeSelect as HTMLSelectElement).value).toBe('');
      });
    });

    test('multiple filters work together', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
      });

      const typeSelect = screen.getAllByRole('combobox')[0];
      const confidenceInput = screen.getByPlaceholderText('Min Confidence (%)');

      await userEvent.selectOptions(typeSelect, 'seasonal');
      await userEvent.clear(confidenceInput);
      await userEvent.type(confidenceInput, '85');

      fireEvent.blur(typeSelect);
      fireEvent.blur(confidenceInput);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        const lastCall = calls[calls.length - 1][0];
        expect(lastCall).toContain('pattern_type=seasonal');
        expect(lastCall).toContain('min_confidence=85');
      });
    });
  });

  describe('Sorting', () => {
    test('sort by confidence button exists', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Sort by confidence/i)).toBeInTheDocument();
      });
    });

    test('clicking sort button toggles order', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Sort by confidence/i)).toBeInTheDocument();
      });

      const sortButton = screen.getByLabelText('Sort by confidence');

      // First click - set to desc (default)
      fireEvent.click(sortButton);
      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('sort_order=desc'))).toBe(true);
      });

      // Second click - toggle to asc
      fireEvent.click(sortButton);
      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        const lastCall = calls[calls.length - 1][0];
        expect(lastCall).toContain('sort_by=confidence_pct');
      });
    });

    test('sort indicators visible', async () => {
      render(<PatternList />);
      await waitFor(() => {
        const button = screen.getByLabelText('Sort by confidence');
        fireEvent.click(button);
        expect(button.textContent).toMatch(/↓|↑/);
      });
    });

    test('sorting by different columns works', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Sort by date')).toBeInTheDocument();
      });

      const dateButton = screen.getByLabelText('Sort by date');
      fireEvent.click(dateButton);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(
          calls.some((call) => call[0].includes('sort_by=first_observed_date'))
        ).toBe(true);
      });
    });
  });

  describe('Pagination', () => {
    test('pagination controls visible', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
      });
    });

    test('next button works', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
      });

      const nextButton = screen.getByLabelText('Next page');
      fireEvent.click(nextButton);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('skip=10'))).toBe(true);
      });
    });

    test('previous button disabled on first page', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Previous page')).toBeDisabled();
      });
    });

    test('page size selector exists', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Select number of items per page')).toBeInTheDocument();
      });
    });

    test('changing page size updates API call', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Select number of items per page')).toBeInTheDocument();
      });

      const pageSize = screen.getByLabelText('Select number of items per page');
      await userEvent.selectOptions(pageSize, '25');

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        expect(calls.some((call) => call[0].includes('limit=25'))).toBe(true);
      });
    });

    test('page indicator displays correctly', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Page 1 of/)).toBeInTheDocument();
      });
    });

    test('total count displayed', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/of 3 patterns/)).toBeInTheDocument();
      });
    });
  });

  describe('Details Panel', () => {
    test('clicking pattern shows details panel', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText('Pattern Details')).toBeInTheDocument();
      });
    });

    test('details panel shows pattern ID', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText('pat-001')).toBeInTheDocument();
      });
    });

    test('details panel shows all fields', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText('Pattern ID')).toBeInTheDocument();
        expect(screen.getByText('Metric')).toBeInTheDocument();
        expect(screen.getByText('Confidence')).toBeInTheDocument();
        expect(screen.getByText('Frequency')).toBeInTheDocument();
      });
    });

    test('close button closes details panel', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText('Pattern Details')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText('Close details panel');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Pattern Details')).not.toBeInTheDocument();
      });
    });

    test('details panel shows affected plants', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText('Affected Plants')).toBeInTheDocument();
      });
    });

    test('details panel shows fleet-wide indicator', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Degradation')).toBeInTheDocument();
      });

      const degradationRow = screen.getByText('Degradation').closest('tr');
      fireEvent.click(degradationRow!);

      await waitFor(() => {
        expect(screen.getByText('Fleet-wide Pattern')).toBeInTheDocument();
      });
    });
  });

  describe('Callbacks', () => {
    test('onPatternSelected callback called', async () => {
      const onPatternSelected = jest.fn();
      render(<PatternList onPatternSelected={onPatternSelected} />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(onPatternSelected).toHaveBeenCalledWith(expect.objectContaining({
          pattern_id: 'pat-001',
        }));
      });
    });

    test('onFilterChanged callback called', async () => {
      const onFilterChanged = jest.fn();
      render(<PatternList onFilterChanged={onFilterChanged} />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Min Confidence (%)')).toBeInTheDocument();
      });

      const typeSelect = screen.getAllByRole('combobox')[0];
      await userEvent.selectOptions(typeSelect, 'seasonal');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        expect(onFilterChanged).toHaveBeenCalledWith(
          expect.objectContaining({ pattern_type: 'seasonal' })
        );
      });
    });

    test('onSortChanged callback called', async () => {
      const onSortChanged = jest.fn();
      render(<PatternList onSortChanged={onSortChanged} />);
      await waitFor(() => {
        expect(screen.getByLabelText('Sort by confidence')).toBeInTheDocument();
      });

      const sortButton = screen.getByLabelText('Sort by confidence');
      fireEvent.click(sortButton);

      await waitFor(() => {
        expect(onSortChanged).toHaveBeenCalled();
      });
    });

    test('onPageChanged callback called', async () => {
      const onPageChanged = jest.fn();
      render(<PatternList onPageChanged={onPageChanged} />);
      await waitFor(() => {
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
      });

      const nextButton = screen.getByLabelText('Next page');
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(onPageChanged).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    test('table has proper ARIA roles', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    test('buttons have descriptive labels', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
      });
    });

    test('filter inputs have labels', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByLabelText('Filter by pattern type')).toBeInTheDocument();
        expect(screen.getByLabelText('Filter by minimum confidence')).toBeInTheDocument();
      });
    });

    test('rows are keyboard accessible', async () => {
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('Seasonal')).toBeInTheDocument();
      });

      const firstRow = screen.getByText('Seasonal').closest('tr');
      expect(firstRow).toHaveAttribute('tabindex', '0');
    });
  });

  describe('Edge Cases', () => {
    test('handles empty pattern list', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: [], total: 0 }),
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/No patterns detected/)).toBeInTheDocument();
      });
    });

    test('handles very long descriptions', async () => {
      const longPatterns = [
        {
          ...mockPatterns[0],
          description:
            'A'.repeat(200) +
            ' This is a very long description that should still be displayed properly without breaking the layout',
        },
      ];
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: longPatterns, total: 1 }),
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Pattern Details/)).not.toBeInTheDocument();
      });
    });

    test('handles missing fields gracefully', async () => {
      const incompletPattern = {
        ...mockPatterns[0],
        affected_plants: [],
      };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ patterns: [incompletPattern], total: 1 }),
      });
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText('92.5%')).toBeInTheDocument();
      });
    });

    test('handles API timeout', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 100))
      );
      render(<PatternList />);
      await waitFor(() => {
        expect(screen.getByText(/Error loading patterns/)).toBeInTheDocument();
      });
    });
  });
});
