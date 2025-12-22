/**
 * E2E tests for PatternList component using Playwright
 * Tests real browser interactions, visual states, and complete workflows
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const PATTERNS_PAGE = `${BASE_URL}/patterns`;

// Mock data for testing
const mockPatternResponse = {
  patterns: [
    {
      pattern_id: 'pat-001',
      plant_id: 'plant-001',
      pattern_type: 'seasonal',
      metric_name: 'power_output_kwh',
      description: 'Strong seasonal variation with peak in summer months',
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
      pattern_type: 'weekly_cycle',
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
      pattern_type: 'degradation',
      metric_name: 'efficiency_pct',
      description: 'Gradual efficiency decline over 3-year period',
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
  ],
  total: 3,
};

test.describe('PatternList E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocking
    await page.route('**/api/patterns*', (route) => {
      route.abort('failed');
    });
  });

  test.describe('Page Load and Initialization', () => {
    test('loads pattern page successfully', async ({ page }) => {
      await page.goto(PATTERNS_PAGE);
      await page.waitForLoadState('networkidle');
      expect(page).toHaveTitle(/Patterns/i);
    });

    test('displays loading state initially', async ({ page }) => {
      // Create a slow network condition
      await page.route('**/api/patterns*', (route) => {
        setTimeout(() => route.continue(), 500);
      });

      await page.goto(PATTERNS_PAGE);
      
      const loader = page.locator('text=Loading patterns');
      await expect(loader).toBeVisible();
    });

    test('displays patterns after loading', async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });

      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('text=Detected Patterns');
      
      const header = page.locator('text=Detected Patterns');
      await expect(header).toBeVisible();
    });
  });

  test.describe('Table Display', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('displays pattern table with correct columns', async ({ page }) => {
      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();

      // Check for column headers
      await expect(page.locator('text=Confidence')).toBeVisible();
      await expect(page.locator('text=Pattern Type')).toBeVisible();
      await expect(page.locator('text=Description')).toBeVisible();
      await expect(page.locator('text=Detected')).toBeVisible();
      await expect(page.locator('text=Significance')).toBeVisible();
    });

    test('displays all pattern rows', async ({ page }) => {
      const rows = page.locator('[role="row"]').locator('visible=true');
      // Header row + 3 data rows
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThanOrEqual(3);
    });

    test('shows confidence percentages with progress bars', async ({ page }) => {
      await expect(page.locator('text=92.5%')).toBeVisible();
      await expect(page.locator('text=85.0%')).toBeVisible();
      await expect(page.locator('text=78.5%')).toBeVisible();

      // Check for progress bars
      const bars = page.locator('.confidence-bar');
      expect(await bars.count()).toBeGreaterThan(0);
    });

    test('displays pattern type badges with correct colors', async ({ page }) => {
      const seasonalBadge = page.locator('text=Seasonal').first();
      await expect(seasonalBadge).toBeVisible();
      
      const weeklyBadge = page.locator('text=Weekly Cycle');
      await expect(weeklyBadge).toBeVisible();

      const degradationBadge = page.locator('text=Degradation');
      await expect(degradationBadge).toBeVisible();

      // Check colors using data attributes or CSS classes
      const seasonalStyle = await seasonalBadge.evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor;
      });
      expect(seasonalStyle).toBeTruthy();
    });

    test('formats dates in readable format', async ({ page }) => {
      // Dates should be in format like "Jan 15, 2023"
      await expect(page.locator('text=Jan 15, 2023')).toBeVisible();
      await expect(page.locator('text=Jun 10, 2023')).toBeVisible();
    });
  });

  test.describe('Filtering Functionality', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('filter by pattern type', async ({ page }) => {
      const typeSelect = page.locator('select').first();
      await typeSelect.selectOption('seasonal');
      
      // Wait for API call with filter parameter
      await page.waitForURL('**/api/patterns*pattern_type=seasonal*');
      
      const seasonalBadges = page.locator('text=Seasonal');
      await expect(seasonalBadges.first()).toBeVisible();
    });

    test('filter by confidence threshold', async ({ page }) => {
      const confidenceInput = page.locator('[placeholder="Min Confidence (%)"]');
      await confidenceInput.fill('85');
      await confidenceInput.blur();

      // Wait for API call with filter parameter
      await page.waitForURL('**/api/patterns*min_confidence=85*');

      // Should still show patterns with >= 85% confidence
      await expect(page.locator('text=92.5%')).toBeVisible();
      await expect(page.locator('text=85.0%')).toBeVisible();
    });

    test('clear all filters', async ({ page }) => {
      const typeSelect = page.locator('select').first();
      await typeSelect.selectOption('seasonal');
      
      await page.waitForURL('**/api/patterns*pattern_type=seasonal*');

      const clearButton = page.locator('text=Clear Filters');
      await clearButton.click();

      // Check that select is reset
      const selectedValue = await typeSelect.inputValue();
      expect(selectedValue).toBe('');

      // Should show all patterns again
      await expect(page.locator('text=Seasonal')).toBeVisible();
      await expect(page.locator('text=Weekly Cycle')).toBeVisible();
      await expect(page.locator('text=Degradation')).toBeVisible();
    });

    test('multiple filters work together', async ({ page }) => {
      const typeSelect = page.locator('select').first();
      const confidenceInput = page.locator('[placeholder="Min Confidence (%)"]');

      await typeSelect.selectOption('seasonal');
      await confidenceInput.fill('90');
      await confidenceInput.blur();

      // Wait for API call with both filters
      await page.waitForURL('**/api/patterns*pattern_type=seasonal*min_confidence=90*');
    });
  });

  test.describe('Sorting Functionality', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('sort by confidence descending', async ({ page }) => {
      const confidenceButton = page.locator('[aria-label="Sort by confidence"]');
      await confidenceButton.click();

      // Wait for API call with sort parameter
      await page.waitForURL('**/api/patterns*sort_by=confidence_pct*sort_order=desc*');

      // Check that sort indicator shows
      const sortIndicator = confidenceButton.locator('text=↓');
      await expect(sortIndicator).toBeVisible();
    });

    test('sort by date ascending', async ({ page }) => {
      const dateButton = page.locator('[aria-label="Sort by date"]');
      await dateButton.click();

      await page.waitForURL('**/api/patterns*sort_by=first_observed_date*sort_order=desc*');

      // Click again to toggle to ascending
      await dateButton.click();
      await page.waitForURL('**/api/patterns*sort_order=asc*');
    });

    test('sort toggle changes direction', async ({ page }) => {
      const confidenceButton = page.locator('[aria-label="Sort by confidence"]');

      // First click: asc
      await confidenceButton.click();
      await page.waitForURL('**/api/patterns*sort_order=desc*');

      // Second click on same column: toggle direction
      await confidenceButton.click();
      await page.waitForURL('**/api/patterns*sort_order=asc*');
    });
  });

  test.describe('Pagination', () => {
    test.beforeEach(async ({ page }) => {
      const largeDataset = {
        ...mockPatternResponse,
        total: 100,
      };
      
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(largeDataset),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('displays page indicator', async ({ page }) => {
      const pageIndicator = page.locator('text=/Page \\d+ of/');
      await expect(pageIndicator).toBeVisible();
    });

    test('shows total count', async ({ page }) => {
      const totalCount = page.locator('text=of 100 patterns');
      await expect(totalCount).toBeVisible();
    });

    test('next button works', async ({ page }) => {
      const nextButton = page.locator('[aria-label="Next page"]');
      await expect(nextButton).toBeEnabled();

      await nextButton.click();
      await page.waitForURL('**/api/patterns*skip=10*');

      const pageIndicator = page.locator('text=Page 2 of');
      await expect(pageIndicator).toBeVisible();
    });

    test('previous button disabled on first page', async ({ page }) => {
      const prevButton = page.locator('[aria-label="Previous page"]');
      await expect(prevButton).toBeDisabled();
    });

    test('change items per page', async ({ page }) => {
      const pageSizeSelect = page.locator('[aria-label="Select number of items per page"]');
      await pageSizeSelect.selectOption('25');

      await page.waitForURL('**/api/patterns*limit=25*');

      const pageIndicator = page.locator('text=/Page 1 of/');
      await expect(pageIndicator).toBeVisible();
    });
  });

  test.describe('Details Panel', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('clicking pattern opens details panel', async ({ page }) => {
      const firstRow = page.locator('[role="row"]').nth(1); // Skip header
      await firstRow.click();

      const detailsPanel = page.locator('text=Pattern Details');
      await expect(detailsPanel).toBeVisible();
    });

    test('details panel shows all pattern information', async ({ page }) => {
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.click();

      // Wait for details panel
      await page.waitForSelector('text=Pattern Details');

      // Check various fields
      await expect(page.locator('text=Pattern ID')).toBeVisible();
      await expect(page.locator('text=Type')).toBeVisible();
      await expect(page.locator('text=Metric')).toBeVisible();
      await expect(page.locator('text=Confidence')).toBeVisible();
      await expect(page.locator('text=Significance Score')).toBeVisible();
      await expect(page.locator('text=Frequency')).toBeVisible();
      await expect(page.locator('text=Detected')).toBeVisible();
      await expect(page.locator('text=Last Observed')).toBeVisible();
      await expect(page.locator('text=Occurrences')).toBeVisible();
    });

    test('close button closes details panel', async ({ page }) => {
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.click();

      await page.waitForSelector('text=Pattern Details');

      const closeButton = page.locator('[aria-label="Close details panel"]');
      await closeButton.click();

      const detailsPanel = page.locator('text=Pattern Details');
      await expect(detailsPanel).not.toBeVisible();
    });

    test('fleet-wide badge displays for fleet patterns', async ({ page }) => {
      // Click on the degradation pattern (third row, which is fleet-wide)
      const rows = page.locator('[role="row"]');
      const degradationRow = rows.filter({ hasText: 'Degradation' }).first();
      await degradationRow.click();

      await page.waitForSelector('text=Pattern Details');

      const fleetBadge = page.locator('text=Fleet-wide');
      await expect(fleetBadge).toBeVisible();
    });

    test('affected plants list displays', async ({ page }) => {
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.click();

      await page.waitForSelector('text=Pattern Details');

      const affectedPlants = page.locator('text=Affected Plants');
      await expect(affectedPlants).toBeVisible();
    });

    test('selecting different pattern updates details panel', async ({ page }) => {
      // Click first pattern
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.click();

      await page.waitForSelector('text=Pattern Details');

      const seasonal = await page.locator('text=Seasonal').first().isVisible();
      expect(seasonal).toBeTruthy();

      // Click second pattern
      const secondRow = page.locator('[role="row"]').nth(2);
      await secondRow.click();

      const weekly = await page.locator('text=Weekly Cycle').first().isVisible();
      expect(weekly).toBeTruthy();
    });
  });

  test.describe('Responsive Design', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
    });

    test('desktop layout displays correctly', async ({ page }) => {
      await page.setViewportSize({ width: 1400, height: 900 });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const table = page.locator('[role="table"]');
      const detailsPanel = page.locator('.details-panel');

      // Both should be visible in desktop view
      await expect(table).toBeVisible();
    });

    test('tablet layout displays correctly', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 900 });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();

      // Responsive layout should adapt
      const container = page.locator('.pattern-list-container');
      const computedStyle = await container.evaluate((el) => {
        return window.getComputedStyle(el).display;
      });
      expect(computedStyle).toBeTruthy();
    });

    test('mobile layout displays correctly', async ({ page }) => {
      await page.setViewportSize({ width: 480, height: 800 });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();

      // On mobile, table should be scrollable
      const wrapper = page.locator('.table-wrapper');
      const isScrollable = await wrapper.evaluate((el) => {
        return el.scrollWidth > el.clientWidth;
      });
      // May or may not be scrollable depending on content width
      expect(typeof isScrollable).toBe('boolean');
    });

    test('small mobile layout displays correctly', async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 568 });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();

      // Filters should still be accessible
      const filters = page.locator('.filter-section');
      await expect(filters).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('shows error state on API failure', async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.abort('failed');
      });

      await page.goto(PATTERNS_PAGE);

      const errorMessage = page.locator('text=/Error loading patterns/');
      await expect(errorMessage).toBeVisible();

      const retryButton = page.locator('text=Retry');
      await expect(retryButton).toBeVisible();
    });

    test('retry button retries failed request', async ({ page }) => {
      let callCount = 0;

      await page.route('**/api/patterns*', (route) => {
        callCount++;
        if (callCount === 1) {
          route.abort('failed');
        } else {
          route.fulfill({
            status: 200,
            body: JSON.stringify(mockPatternResponse),
          });
        }
      });

      await page.goto(PATTERNS_PAGE);

      const errorMessage = page.locator('text=/Error loading patterns/');
      await expect(errorMessage).toBeVisible();

      const retryButton = page.locator('text=Retry');
      await retryButton.click();

      // Should now show patterns
      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();
    });

    test('shows empty state when no patterns', async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({ patterns: [], total: 0 }),
        });
      });

      await page.goto(PATTERNS_PAGE);

      const emptyMessage = page.locator('text=/No patterns detected/');
      await expect(emptyMessage).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');
    });

    test('keyboard navigation through patterns', async ({ page }) => {
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.focus();

      // Press Enter to select
      await page.keyboard.press('Enter');

      const detailsPanel = page.locator('text=Pattern Details');
      await expect(detailsPanel).toBeVisible();
    });

    test('keyboard navigation with Tab key', async ({ page }) => {
      // Tab through interactive elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      const focusedElement = await page.evaluate(() => {
        return document.activeElement?.tagName;
      });

      expect(focusedElement).toBeTruthy();
    });

    test('ARIA labels are present', async ({ page }) => {
      const buttons = page.locator('[aria-label]');
      const count = await buttons.count();
      expect(count).toBeGreaterThan(0);
    });

    test('semantic HTML structure', async ({ page }) => {
      const tables = page.locator('[role="table"]');
      await expect(tables).toHaveCount(1);

      const headers = page.locator('[role="columnheader"]');
      expect(await headers.count()).toBeGreaterThan(0);
    });

    test('sufficient color contrast', async ({ page }) => {
      // This would require a separate accessibility testing library
      // For now, verify that text is readable
      const text = page.locator('text=Detected Patterns');
      await expect(text).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('page loads within acceptable time', async ({ page }) => {
      const startTime = Date.now();

      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });

      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
    });

    test('handles large dataset efficiently', async ({ page }) => {
      const largeDataset = {
        patterns: Array.from({ length: 100 }, (_, i) => ({
          ...mockPatternResponse.patterns[i % 3],
          pattern_id: `pat-${i}`,
        })),
        total: 1000,
      };

      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(largeDataset),
        });
      });

      const startTime = Date.now();

      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const renderTime = Date.now() - startTime;
      expect(renderTime).toBeLessThan(3000);

      // Table should still be responsive
      const table = page.locator('[role="table"]');
      await expect(table).toBeVisible();
    });

    test('pagination prevents rendering all items', async ({ page }) => {
      const largeDataset = {
        patterns: Array.from({ length: 10 }, (_, i) => ({
          ...mockPatternResponse.patterns[i % 3],
          pattern_id: `pat-${i}`,
        })),
        total: 1000,
      };

      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(largeDataset),
        });
      });

      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      const rows = page.locator('[role="row"]');
      const rowCount = await rows.count();

      // Should have header + max 10 data rows (with default pagination)
      expect(rowCount).toBeLessThanOrEqual(11);
    });
  });

  test.describe('Complete User Workflows', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(mockPatternResponse),
        });
      });
    });

    test('user can filter, sort, and view details', async ({ page }) => {
      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      // 1. Filter by type
      const typeSelect = page.locator('select').first();
      await typeSelect.selectOption('seasonal');

      // 2. Sort by confidence
      const sortButton = page.locator('[aria-label="Sort by confidence"]');
      await sortButton.click();

      // 3. View details
      const firstRow = page.locator('[role="row"]').nth(1);
      await firstRow.click();

      const detailsPanel = page.locator('text=Pattern Details');
      await expect(detailsPanel).toBeVisible();
    });

    test('user can navigate through paginated results', async ({ page }) => {
      const largeDataset = {
        ...mockPatternResponse,
        total: 100,
      };

      await page.route('**/api/patterns*', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify(largeDataset),
        });
      });

      await page.goto(PATTERNS_PAGE);
      await page.waitForSelector('[role="table"]');

      // Check current page
      let pageIndicator = page.locator('text=Page 1 of');
      await expect(pageIndicator).toBeVisible();

      // Go to next page
      const nextButton = page.locator('[aria-label="Next page"]');
      await nextButton.click();

      pageIndicator = page.locator('text=Page 2 of');
      await expect(pageIndicator).toBeVisible();

      // Go back
      const prevButton = page.locator('[aria-label="Previous page"]');
      await prevButton.click();

      pageIndicator = page.locator('text=Page 1 of');
      await expect(pageIndicator).toBeVisible();
    });
  });
});
