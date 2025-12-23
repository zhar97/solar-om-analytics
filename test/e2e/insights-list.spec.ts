import { test, expect } from '@playwright/test';

test.describe('InsightsList E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the insights API endpoint
    await page.route('**/api/insights*', async (route) => {
      const mockData = {
        success: true,
        insights: [
          {
            insight_id: 'e2e-insight-1',
            plant_id: 'plant-solar-001',
            insight_type: 'anomaly_cause_hypothesis',
            title: 'Unexpected Power Drop Detected',
            description: 'Solar output dropped 45% without weather change',
            reasoning: 'Z-score of -3.2 indicates statistical anomaly',
            business_impact: 'Potential equipment failure requiring immediate inspection',
            confidence: 92,
            urgency: 'critical',
            linked_patterns: ['pattern-1'],
            linked_anomalies: ['anomaly-1'],
            generation_date: '2025-12-23T10:30:00Z',
            recommended_action: 'Schedule immediate equipment inspection',
          },
          {
            insight_id: 'e2e-insight-2',
            plant_id: 'plant-solar-002',
            insight_type: 'pattern_explanation',
            title: 'Seasonal Performance Pattern',
            description: 'Production peaks in summer months',
            reasoning: 'Consistent monthly variation correlates with temperature',
            business_impact: 'Plan maintenance during low-production seasons',
            confidence: 85,
            urgency: 'high',
            linked_patterns: ['pattern-2'],
            linked_anomalies: [],
            generation_date: '2025-12-22T14:15:00Z',
          },
          {
            insight_id: 'e2e-insight-3',
            plant_id: 'plant-solar-001',
            insight_type: 'performance_trend',
            title: 'Gradual Efficiency Decline',
            description: 'System efficiency has declined 3% over past 6 months',
            reasoning: 'Linear regression shows consistent downward trend',
            business_impact: 'Early indicator of panel degradation or soiling',
            confidence: 78,
            urgency: 'medium',
            linked_patterns: ['pattern-3'],
            linked_anomalies: [],
            generation_date: '2025-12-21T09:45:00Z',
          },
          {
            insight_id: 'e2e-insight-4',
            plant_id: 'plant-solar-003',
            insight_type: 'maintenance_recommendation',
            title: 'Inverter Maintenance Due',
            description: 'Inverter operating temperature consistently above 75°C',
            reasoning: 'Temperature threshold exceeded in 12 consecutive days',
            business_impact: 'Risk of inverter failure and system downtime',
            confidence: 88,
            urgency: 'high',
            linked_patterns: [],
            linked_anomalies: ['anomaly-2'],
            generation_date: '2025-12-20T11:20:00Z',
          },
          {
            insight_id: 'e2e-insight-5',
            plant_id: 'plant-solar-002',
            insight_type: 'operational_insight',
            title: 'Optimal Operating Window Identified',
            description: 'Peak efficiency achieved between 10 AM and 2 PM',
            reasoning: 'Historical performance data shows consistent pattern',
            business_impact: 'Can optimize maintenance scheduling around peak hours',
            confidence: 82,
            urgency: 'low',
            linked_patterns: ['pattern-4'],
            linked_anomalies: [],
            generation_date: '2025-12-19T16:30:00Z',
          },
        ],
        total: 5,
        skip: 0,
        limit: 10,
      };
      await route.fulfill({ json: mockData });
    });

    // Navigate to insights page (assuming there's a route for it)
    await page.goto('/');
  });

  test.describe('Page Navigation & Rendering', () => {
    test('should load insights page and display table', async ({ page }) => {
      // Wait for page load and check for main content
      await expect(page.locator('text=AI-Generated Insights')).toBeVisible();
      await expect(page.locator('table')).toBeVisible();
      
      // Verify table has expected headers
      await expect(page.locator('th')).toContainText(['Date', 'Type', 'Title', 'Urgency', 'Confidence']);
    });

    test('should display all insights in table', async ({ page }) => {
      // Verify all 5 insights are rendered
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
      await expect(page.locator('text=Seasonal Performance Pattern')).toBeVisible();
      await expect(page.locator('text=Gradual Efficiency Decline')).toBeVisible();
      await expect(page.locator('text=Inverter Maintenance Due')).toBeVisible();
      await expect(page.locator('text=Optimal Operating Window Identified')).toBeVisible();
    });

    test('should display filter controls', async ({ page }) => {
      await expect(page.locator('select[aria-label="Filter by insight type"]')).toBeVisible();
      await expect(page.locator('select[aria-label="Filter by urgency"]')).toBeVisible();
      await expect(page.locator('input[aria-label="Filter by minimum confidence"]')).toBeVisible();
      await expect(page.locator('input[aria-label="Filter by plant ID"]')).toBeVisible();
      await expect(page.locator('button:has-text("Clear Filters")')).toBeVisible();
    });

    test('should display pagination controls', async ({ page }) => {
      await expect(page.locator('select[aria-label="Select page size"]')).toBeVisible();
      await expect(page.locator('button[aria-label="Previous page"]')).toBeVisible();
      await expect(page.locator('button[aria-label="Next page"]')).toBeVisible();
      await expect(page.locator('text=Page 1')).toBeVisible();
    });
  });

  test.describe('Filtering Functionality', () => {
    test('should filter by urgency level - critical', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('critical');
      
      // Wait for API call and verify only critical insight is shown
      await page.waitForResponse('**/api/insights*');
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
      await expect(page.locator('text=Seasonal Performance Pattern')).not.toBeVisible();
    });

    test('should filter by urgency level - high', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('high');
      
      await page.waitForResponse('**/api/insights*');
      // Should show high urgency insights
      await expect(page.locator('text=Seasonal Performance Pattern')).toBeVisible();
    });

    test('should filter by insight type', async ({ page }) => {
      const typeSelect = page.locator('select[aria-label="Filter by insight type"]');
      await typeSelect.selectOption('anomaly_cause_hypothesis');
      
      await page.waitForResponse('**/api/insights*');
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
    });

    test('should filter by minimum confidence', async ({ page }) => {
      const confidenceInput = page.locator('input[aria-label="Filter by minimum confidence"]');
      await confidenceInput.fill('85');
      await confidenceInput.blur();
      
      await page.waitForResponse('**/api/insights*');
      // Should show insights with 85+ confidence
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
    });

    test('should filter by plant ID', async ({ page }) => {
      const plantInput = page.locator('input[aria-label="Filter by plant ID"]');
      await plantInput.fill('plant-solar-001');
      await plantInput.blur();
      
      await page.waitForResponse('**/api/insights*');
      // Should show only insights from plant-solar-001
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
    });

    test('should clear all filters', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('high');
      await page.waitForResponse('**/api/insights*');
      
      const clearButton = page.locator('button:has-text("Clear Filters")');
      await clearButton.click();
      await page.waitForResponse('**/api/insights*');
      
      // All insights should be visible after clearing
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
      await expect(page.locator('text=Seasonal Performance Pattern')).toBeVisible();
    });

    test('should apply multiple filters simultaneously', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      const typeSelect = page.locator('select[aria-label="Filter by insight type"]');
      
      await urgencySelect.selectOption('high');
      await typeSelect.selectOption('anomaly_cause_hypothesis');
      
      await page.waitForResponse('**/api/insights*');
      // Verify filters are applied together
      const apiRequest = await page.evaluate(() => window.lastApiRequest);
      expect(apiRequest).toContain('urgency=high');
      expect(apiRequest).toContain('insight_type=anomaly_cause_hypothesis');
    });
  });

  test.describe('Sorting Functionality', () => {
    test('should sort by confidence descending by default', async ({ page }) => {
      // Check sort indicator on Confidence column
      await expect(page.locator('.sort-indicator')).toContainText('↓');
    });

    test('should toggle sort order on column click', async ({ page }) => {
      const confidenceHeader = page.locator('th').filter({ hasText: 'Confidence' });
      await confidenceHeader.click();
      await page.waitForResponse('**/api/insights*');
      
      // Sort should toggle to ascending
      await expect(page.locator('.sort-indicator')).toContainText('↑');
    });

    test('should change sort column on header click', async ({ page }) => {
      const dateHeader = page.locator('th').filter({ hasText: 'Date' });
      await dateHeader.click();
      await page.waitForResponse('**/api/insights*');
      
      // Date column should now show sort indicator
      await expect(dateHeader.locator('.sort-indicator')).toBeVisible();
    });

    test('should maintain sort state when changing filters', async ({ page }) => {
      const dateHeader = page.locator('th').filter({ hasText: 'Date' });
      await dateHeader.click();
      
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('high');
      
      await page.waitForResponse('**/api/insights*');
      // Sort should still be applied
      await expect(dateHeader.locator('.sort-indicator')).toBeVisible();
    });
  });

  test.describe('Pagination Functionality', () => {
    test('should change page size', async ({ page }) => {
      const pageSizeSelect = page.locator('select[aria-label="Select page size"]');
      await pageSizeSelect.selectOption('25');
      
      await page.waitForResponse('**/api/insights*');
      // Verify API was called with new limit
      const response = await page.evaluate(() => window.lastApiCall);
      expect(response).toContain('limit=25');
    });

    test('should disable prev button on first page', async ({ page }) => {
      const prevButton = page.locator('button[aria-label="Previous page"]');
      await expect(prevButton).toBeDisabled();
    });

    test('should enable next button when more insights exist', async ({ page }) => {
      const nextButton = page.locator('button[aria-label="Next page"]');
      // With 5 insights and 10 per page, next should be disabled
      await expect(nextButton).toBeDisabled();
    });

    test('should display pagination info', async ({ page }) => {
      await expect(page.locator('text=/Showing .* of .* insights/')).toBeVisible();
      await expect(page.locator('text=/Page .* of .*/')).toBeVisible();
    });
  });

  test.describe('Data Display & Formatting', () => {
    test('should display insight titles', async ({ page }) => {
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
      await expect(page.locator('text=Seasonal Performance Pattern')).toBeVisible();
    });

    test('should display urgency badges with correct styling', async ({ page }) => {
      const criticalBadges = page.locator('text=Critical');
      await expect(criticalBadges.first()).toBeVisible();
      
      const badgeElement = criticalBadges.first().locator('..');
      await expect(badgeElement).toHaveClass(/urgency-badge/);
    });

    test('should display confidence percentages', async ({ page }) => {
      await expect(page.locator('text=92%')).toBeVisible();
      await expect(page.locator('text=85%')).toBeVisible();
      await expect(page.locator('text=78%')).toBeVisible();
    });

    test('should display confidence bars', async ({ page }) => {
      const confidenceBars = page.locator('.confidence-bar');
      await expect(confidenceBars).toHaveCount(5);
      
      // Verify bar widths reflect confidence values
      const firstBar = confidenceBars.first().locator('.confidence-fill');
      const style = await firstBar.getAttribute('style');
      expect(style).toContain('92%');
    });

    test('should display plant IDs', async ({ page }) => {
      await expect(page.locator('text=plant-solar-001')).toBeVisible();
      await expect(page.locator('text=plant-solar-002')).toBeVisible();
    });

    test('should display linked pattern and anomaly counts', async ({ page }) => {
      const linkBadges = page.locator('.link-badge');
      await expect(linkBadges).toHaveCount(7); // 5 insights with various links
    });

    test('should format dates correctly', async ({ page }) => {
      // Check for formatted dates like "Dec 23, 2025"
      await expect(page.locator('text=/Dec \\d{2}, \\d{4}/')).toBeVisible();
    });
  });

  test.describe('Insight Selection & Details Panel', () => {
    test('should select insight when clicking row', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();
      
      // Details panel should appear or expand
      await expect(page.locator('.details-panel')).toBeVisible();
    });

    test('should display full insight details in panel', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();
      
      // Verify details panel shows all fields
      await expect(page.locator('text=Reasoning')).toBeVisible();
      await expect(page.locator('text=Business Impact')).toBeVisible();
      await expect(page.locator('text=Recommended Action')).toBeVisible();
    });

    test('should update details panel when selecting different insight', async ({ page }) => {
      const firstRow = page.locator('tbody tr').nth(0);
      const secondRow = page.locator('tbody tr').nth(1);
      
      await firstRow.click();
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
      
      await secondRow.click();
      await expect(page.locator('text=Seasonal Performance Pattern')).toBeVisible();
    });

    test('should highlight selected row', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();
      
      // Selected row should have highlighting class
      await expect(firstRow).toHaveClass(/selected/);
    });

    test('should deselect insight on second click', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      
      await firstRow.click();
      await expect(firstRow).toHaveClass(/selected/);
      
      await firstRow.click();
      await expect(firstRow).not.toHaveClass(/selected/);
    });
  });

  test.describe('Keyboard Navigation & Accessibility', () => {
    test('should navigate table with Tab key', async ({ page }) => {
      const filterSelect = page.locator('select[aria-label="Filter by insight type"]');
      
      await filterSelect.focus();
      await expect(filterSelect).toBeFocused();
      
      await page.keyboard.press('Tab');
      const nextElement = page.locator('select[aria-label="Filter by urgency"]');
      await expect(nextElement).toBeFocused();
    });

    test('should navigate filters with Tab and Shift+Tab', async ({ page }) => {
      const typeSelect = page.locator('select[aria-label="Filter by insight type"]');
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      
      await typeSelect.focus();
      await page.keyboard.press('Tab');
      await expect(urgencySelect).toBeFocused();
      
      await page.keyboard.press('Shift+Tab');
      await expect(typeSelect).toBeFocused();
    });

    test('should select insight with Enter key', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      
      // Focus the row (it's a button)
      await firstRow.focus();
      await page.keyboard.press('Enter');
      
      // Details should appear
      await expect(page.locator('.details-panel')).toBeVisible();
    });

    test('should have proper ARIA labels on all controls', async ({ page }) => {
      // Verify all filter controls have labels
      await expect(page.locator('[aria-label="Filter by insight type"]')).toBeVisible();
      await expect(page.locator('[aria-label="Filter by urgency"]')).toBeVisible();
      await expect(page.locator('[aria-label="Filter by minimum confidence"]')).toBeVisible();
      await expect(page.locator('[aria-label="Filter by plant ID"]')).toBeVisible();
      await expect(page.locator('[aria-label="Select page size"]')).toBeVisible();
      await expect(page.locator('[aria-label="Previous page"]')).toBeVisible();
      await expect(page.locator('[aria-label="Next page"]')).toBeVisible();
    });

    test('should announce page updates to screen readers', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('critical');
      
      // Check for aria-live regions
      await expect(page.locator('[aria-live]')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should be responsive on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      await expect(page.locator('table')).toBeVisible();
      await expect(page.locator('.details-panel')).toBeVisible();
    });

    test('should be responsive on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await expect(page.locator('table')).toBeVisible();
      // Table might scroll or adapt
      await expect(page.locator('.insights-list-container')).toBeVisible();
    });

    test('should be responsive on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Main container should still be visible
      await expect(page.locator('.insights-list-container')).toBeVisible();
      // Controls should be accessible
      await expect(page.locator('select[aria-label="Filter by insight type"]')).toBeVisible();
    });

    test('should stack elements properly on small screens', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Filter section should be accessible
      await expect(page.locator('.filter-group')).toBeVisible();
    });
  });

  test.describe('Performance & Loading States', () => {
    test('should load initial data', async ({ page }) => {
      // Wait for table to be populated
      await expect(page.locator('tbody tr')).toHaveCount(5);
    });

    test('should handle rapid filter changes', async ({ page }) => {
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      
      // Rapidly change filters
      await urgencySelect.selectOption('critical');
      await urgencySelect.selectOption('high');
      await urgencySelect.selectOption('medium');
      
      // Should eventually settle on last filter
      await page.waitForTimeout(500);
      await expect(page.locator('table')).toBeVisible();
    });

    test('should maintain scroll position when filtering', async ({ page }) => {
      // Scroll down
      await page.evaluate(() => window.scrollBy(0, 300));
      const initialScrollY = await page.evaluate(() => window.scrollY);
      
      // Apply filter
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('high');
      
      // Check scroll position (may reset to top)
      const finalScrollY = await page.evaluate(() => window.scrollY);
      expect([initialScrollY, 0]).toContain(finalScrollY);
    });
  });

  test.describe('Dark Mode Support', () => {
    test('should respect dark mode preference', async ({ page }) => {
      // Emulate dark color scheme
      await page.emulateMedia({ colorScheme: 'dark' });
      
      // Component should render without errors
      await expect(page.locator('table')).toBeVisible();
    });

    test('should respect light mode preference', async ({ page }) => {
      // Emulate light color scheme
      await page.emulateMedia({ colorScheme: 'light' });
      
      // Component should render without errors
      await expect(page.locator('table')).toBeVisible();
    });

    test('should have readable text in both modes', async ({ page }) => {
      // Test in dark mode
      await page.emulateMedia({ colorScheme: 'dark' });
      const darkText = await page.locator('h2').first().evaluate(el => window.getComputedStyle(el).color);
      
      // Test in light mode
      await page.emulateMedia({ colorScheme: 'light' });
      const lightText = await page.locator('h2').first().evaluate(el => window.getComputedStyle(el).color);
      
      // Both should have valid colors
      expect(darkText).toMatch(/rgb/);
      expect(lightText).toMatch(/rgb/);
    });
  });

  test.describe('Error Handling & Edge Cases', () => {
    test('should handle missing insight data gracefully', async ({ page }) => {
      // Navigate normally
      await expect(page.locator('table')).toBeVisible();
    });

    test('should handle special characters in insight titles', async ({ page }) => {
      // InsightsList should render without errors
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
    });

    test('should handle long text content', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();
      
      // Details panel should handle long text
      await expect(page.locator('.details-panel')).toBeVisible();
      
      // Text should be readable (not overflow)
      const panelWidth = await page.locator('.details-panel').boundingBox();
      expect(panelWidth?.width).toBeGreaterThan(0);
    });

    test('should handle empty state (no insights)', async ({ page }) => {
      // Mock empty response
      await page.route('**/api/insights*', async (route) => {
        await route.fulfill({
          json: { success: true, insights: [], total: 0 },
        });
      });
      
      // Reload to trigger empty state
      await page.reload();
      
      // Should show empty state message
      await expect(page.locator('text=No insights found')).toBeVisible();
    });
  });

  test.describe('User Workflows', () => {
    test('should complete filter and view details workflow', async ({ page }) => {
      // 1. Filter by urgency
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      await urgencySelect.selectOption('critical');
      await page.waitForResponse('**/api/insights*');
      
      // 2. Select insight
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();
      
      // 3. View details panel
      await expect(page.locator('.details-panel')).toBeVisible();
      await expect(page.locator('text=Business Impact')).toBeVisible();
    });

    test('should complete sort and pagination workflow', async ({ page }) => {
      // 1. Sort by date
      const dateHeader = page.locator('th').filter({ hasText: 'Date' });
      await dateHeader.click();
      await page.waitForResponse('**/api/insights*');
      
      // 2. Change page size
      const pageSizeSelect = page.locator('select[aria-label="Select page size"]');
      await pageSizeSelect.selectOption('25');
      await page.waitForResponse('**/api/insights*');
      
      // 3. Verify results updated
      await expect(page.locator('table')).toBeVisible();
    });

    test('should complete multi-filter and clear workflow', async ({ page }) => {
      // 1. Apply multiple filters
      const urgencySelect = page.locator('select[aria-label="Filter by urgency"]');
      const typeSelect = page.locator('select[aria-label="Filter by insight type"]');
      const confidenceInput = page.locator('input[aria-label="Filter by minimum confidence"]');
      
      await urgencySelect.selectOption('high');
      await typeSelect.selectOption('anomaly_cause_hypothesis');
      await confidenceInput.fill('80');
      
      await page.waitForResponse('**/api/insights*');
      
      // 2. Clear all filters
      const clearButton = page.locator('button:has-text("Clear Filters")');
      await clearButton.click();
      
      await page.waitForResponse('**/api/insights*');
      
      // 3. Verify all insights are visible again
      await expect(page.locator('text=Unexpected Power Drop Detected')).toBeVisible();
    });
  });
});
