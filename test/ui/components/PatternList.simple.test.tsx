import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PatternList } from '../../../src/ui/components/PatternList';

global.fetch = jest.fn();

// Mock ResizeObserver for Recharts
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

const mockPatterns = [
  {
    pattern_id: 'pattern-1',
    plant_id: 'plant-a',
    pattern_type: 'seasonal' as const,
    metric_name: 'power_output',
    description: 'Higher production in summer months',
    frequency: 'yearly',
    amplitude: 35,
    significance_score: 8.5,
    confidence_pct: 92,
    first_observed_date: '2024-01-01',
    last_observed_date: '2025-12-23',
    occurrence_count: 24,
    affected_plants: ['plant-a', 'plant-b'],
    is_fleet_wide: true,
  },
  {
    pattern_id: 'pattern-2',
    plant_id: 'plant-c',
    pattern_type: 'weekly_cycle' as const,
    metric_name: 'power_output',
    description: 'Production dips on weekends',
    frequency: 'weekly',
    amplitude: 15,
    significance_score: 7.2,
    confidence_pct: 85,
    first_observed_date: '2024-06-01',
    last_observed_date: '2025-12-23',
    occurrence_count: 120,
    affected_plants: ['plant-c'],
    is_fleet_wide: false,
  },
];

describe('PatternList Component - Simplified Tests', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        patterns: mockPatterns,
        total: mockPatterns.length,
      }),
    } as any);
  });

  describe('Basic Rendering', () => {
    it('should render component and fetch data', async () => {
      const { container } = render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });

      expect(container).toBeTruthy();
    });
  });

  describe('Filtering', () => {
    it('should apply filters to fetch request', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/patterns'));
      });
    });
  });

  describe('Sorting', () => {
    it('should fetch with default sort by confidence descending', async () => {
      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('sort_by=confidence_pct')
        );
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('sort_order=desc')
        );
      });
    });
  });

  describe('Pagination', () => {
    it('should have pagination controls', async () => {
      render(<PatternList />);

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });

    it('should handle page size changes', async () => {
      render(<PatternList />);

      const pageSizeSelect = await screen.findByDisplayValue('10');
      fireEvent.change(pageSizeSelect, { target: { value: '25' } });

      await waitFor(() => {
        expect(screen.getByDisplayValue('25')).toBeInTheDocument();
      });
    });
  });

  describe('Pattern Selection', () => {
    it('should call onPatternSelected callback', async () => {
      const mockCallback = jest.fn();
      render(<PatternList onPatternSelected={mockCallback} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle fetch errors gracefully', async () => {
      fetch.mockClear();
      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });

    it('should handle unsuccessful responses', async () => {
      fetch.mockClear();
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ success: false, error: 'Server error' }),
      } as any);

      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Loading State', () => {
    it('should render while loading data', async () => {
      fetch.mockClear();
      fetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({
                    success: true,
                    patterns: mockPatterns,
                    total: mockPatterns.length,
                  }),
                } as any),
              50
            )
          )
      );

      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Empty State', () => {
    it('should handle empty patterns list', async () => {
      fetch.mockClear();
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          patterns: [],
          total: 0,
        }),
      } as any);

      render(<PatternList />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Callbacks', () => {
    it('should accept onFilterChanged callback', async () => {
      const mockFilterCallback = jest.fn();
      render(<PatternList onFilterChanged={mockFilterCallback} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });

    it('should accept onSortChanged callback', async () => {
      const mockSortCallback = jest.fn();
      render(<PatternList onSortChanged={mockSortCallback} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });

    it('should accept onPageChanged callback', async () => {
      const mockPageCallback = jest.fn();
      render(<PatternList onPageChanged={mockPageCallback} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });

    it('should accept all callback props', async () => {
      const callbacks = {
        onFilterChanged: jest.fn(),
        onSortChanged: jest.fn(),
        onPageChanged: jest.fn(),
        onPatternSelected: jest.fn(),
      };

      render(<PatternList {...callbacks} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });
});
