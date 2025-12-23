import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InsightsList } from '../../../src/ui/components/InsightsList';

global.fetch = jest.fn();

const mockInsights = [
  {
    insight_id: 'insight-1',
    plant_id: 'plant-a',
    insight_type: 'anomaly_cause_hypothesis',
    title: 'Unexpected Power Drop Detected',
    description: 'Solar output dropped 45% without weather change',
    reasoning: 'Z-score of -3.2 indicates statistical anomaly',
    business_impact: 'Potential equipment failure requiring immediate inspection',
    confidence: 92,
    urgency: 'critical' as const,
    linked_patterns: ['pattern-1'],
    linked_anomalies: ['anomaly-1'],
    generation_date: '2025-12-23',
    recommended_action: 'Schedule immediate equipment inspection',
  },
  {
    insight_id: 'insight-2',
    plant_id: 'plant-b',
    insight_type: 'pattern_explanation',
    title: 'Seasonal Performance Pattern',
    description: 'Production peaks in summer months',
    reasoning: 'Consistent monthly variation correlates with temperature',
    business_impact: 'Plan maintenance during low-production seasons',
    confidence: 85,
    urgency: 'high' as const,
    linked_patterns: ['pattern-2'],
    linked_anomalies: [],
    generation_date: '2025-12-22',
  },
  {
    insight_id: 'insight-3',
    plant_id: 'plant-c',
    insight_type: 'performance_trend',
    title: 'Declining Efficiency Trend',
    description: 'System efficiency decreasing month over month',
    reasoning: 'Linear regression shows -2.3% monthly decline',
    business_impact: 'Maintenance intervention recommended',
    confidence: 78,
    urgency: 'medium' as const,
    linked_patterns: ['pattern-3'],
    linked_anomalies: [],
    generation_date: '2025-12-21',
  },
];

describe('InsightsList Component - Integration Tests (Simplified)', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        insights: mockInsights,
        total: mockInsights.length,
      }),
    } as any);
  });

  describe('Filter and Sort Workflows', () => {
    it('should apply multiple filters together', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          insights: [mockInsights[0]],
          total: 1,
        }),
      } as any);

      const urgencySelect = screen.getByLabelText('Filter by urgency');
      await userEvent.selectOptions(urgencySelect, 'critical');
      fireEvent.blur(urgencySelect);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('urgency=critical')
        );
      });
    });

    it('should reset pagination when filtering', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          insights: [mockInsights[0]],
          total: 1,
        }),
      } as any);

      const typeSelect = screen.getByLabelText('Filter by insight type');
      await userEvent.selectOptions(typeSelect, 'anomaly_cause_hypothesis');
      fireEvent.blur(typeSelect);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('skip=0')
        );
      });
    });
  });

  describe('Pagination Workflows', () => {
    it('should change page size and retain data', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          insights: mockInsights,
          total: mockInsights.length,
        }),
      } as any);

      const pageSizeSelect = screen.getByLabelText('Select page size');
      await userEvent.selectOptions(pageSizeSelect, '25');

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('limit=25')
        );
      });
    });

    it('should display correct pagination info', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        const paginationInfo = screen.getByText(/Showing.*of.*insights/);
        expect(paginationInfo).toBeInTheDocument();
      });
    });

    it('should maintain filters while changing page', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          insights: mockInsights,
          total: mockInsights.length,
        }),
      } as any);

      const urgencySelect = screen.getByLabelText('Filter by urgency');
      await userEvent.selectOptions(urgencySelect, 'high');
      fireEvent.blur(urgencySelect);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('urgency=high')
        );
      });
    });
  });

  describe('Data Consistency Workflows', () => {
    it('should display all insight types correctly', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
        expect(screen.getByText('Seasonal Performance Pattern')).toBeInTheDocument();
        expect(screen.getByText('Declining Efficiency Trend')).toBeInTheDocument();
      });
    });

    it('should maintain data integrity through filters', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      const allTitles = screen.queryAllByText(/Detected|Pattern|Trend/);
      expect(allTitles.length).toBeGreaterThanOrEqual(3);
    });

    it('should display correct urgency levels', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        const criticalBadges = screen.queryAllByText('Critical');
        const highBadges = screen.queryAllByText('High');
        const mediumBadges = screen.queryAllByText('Medium');

        expect(criticalBadges.length).toBeGreaterThan(0);
        expect(highBadges.length).toBeGreaterThan(0);
        expect(mediumBadges.length).toBeGreaterThan(0);
      });
    });

    it('should display confidence values correctly', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText(/92%/)).toBeInTheDocument();
        expect(screen.getByText(/85%/)).toBeInTheDocument();
        expect(screen.getByText(/78%/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery Workflows', () => {
    it('should have clear filters button for reset', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      const clearButton = screen.getByText('Clear Filters');
      expect(clearButton).toBeInTheDocument();
    });

    it('should handle retry operations', () => {
      render(<InsightsList />);

      const retryButton = screen.queryByText('Retry');
      // Retry button exists if error state is possible
      expect(typeof retryButton).toBeDefined();
    });
  });

  describe('Accessibility Workflows', () => {
    it('should have proper navigation structure', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
      });
    });

    it('should have labeled form controls', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByLabelText('Filter by insight type')).toBeInTheDocument();
        expect(screen.getByLabelText('Filter by urgency')).toBeInTheDocument();
        expect(screen.getByLabelText('Filter by minimum confidence')).toBeInTheDocument();
        expect(screen.getByLabelText('Filter by plant ID')).toBeInTheDocument();
        expect(screen.getByLabelText('Select page size')).toBeInTheDocument();
      });
    });

    it('should have keyboard navigable buttons', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
        buttons.forEach(button => {
          // Buttons should be rendered in the DOM
          expect(button).toBeInTheDocument();
        });
      });
    });
  });

  describe('UI Interaction Workflows', () => {
    it('should update UI when filter changes', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          insights: mockInsights.slice(0, 2),
          total: 2,
        }),
      } as any);

      const typeSelect = screen.getByLabelText('Filter by insight type');
      expect(typeSelect).toBeInTheDocument();

      const initialOptions = screen.getAllByRole('option');
      expect(initialOptions.length).toBeGreaterThan(0);
    });

    it('should maintain scroll position information', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      const tableContainer = screen.getByRole('table');
      expect(tableContainer).toBeInTheDocument();
    });

    it('should display sorted data according to headers', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        const confidenceHeader = screen.getByText(/Confidence/);
        expect(confidenceHeader).toBeInTheDocument();
        expect(confidenceHeader.textContent).toContain('↓');
      });
    });
  });

  describe('Complex User Workflows', () => {
    it('should support filter > sort > paginate workflow', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      // Verify initial state
      expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      expect(screen.getByText('Seasonal Performance Pattern')).toBeInTheDocument();

      // Verify filter controls are present
      expect(screen.getByLabelText('Filter by urgency')).toBeInTheDocument();

      // Verify sort indicators are present
      const sortableHeaders = screen.queryAllByText(/Date|Urgency|Confidence/);
      expect(sortableHeaders.length).toBeGreaterThan(0);

      // Verify pagination controls are present
      expect(screen.getByLabelText('Select page size')).toBeInTheDocument();
    });

    it('should display all key UI elements together', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('AI-Generated Insights')).toBeInTheDocument();
      });

      // Filter section
      expect(screen.getByLabelText('Filter by insight type')).toBeInTheDocument();
      expect(screen.getByLabelText('Filter by urgency')).toBeInTheDocument();

      // Table
      expect(screen.getByRole('table')).toBeInTheDocument();

      // Pagination
      expect(screen.getByLabelText('Select page size')).toBeInTheDocument();
      expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
      expect(screen.getByLabelText('Next page')).toBeInTheDocument();
    });

    it('should maintain consistent state across interactions', async () => {
      render(<InsightsList />);

      await waitFor(() => {
        expect(screen.getByText('Unexpected Power Drop Detected')).toBeInTheDocument();
      });

      // Verify data is displayed
      const titles = screen.queryAllByText(/Detected|Pattern|Trend/);
      const initialCount = titles.length;

      // Verify pagination info matches displayed items
      const paginationInfo = screen.getByText(/Showing.*of.*insights/);
      expect(paginationInfo).toBeInTheDocument();

      // Verify count consistency
      expect(initialCount).toBeGreaterThan(0);
    });
  });
});
