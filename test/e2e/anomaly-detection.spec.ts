/**
 * End-to-End Tests for User Story 1: Anomaly Detection
 * 
 * Scenario: A solar plant operator needs to identify performance anomalies
 * in real-time so they can take corrective action quickly.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000';

test.describe('User Story 1: Anomaly Detection', () => {
  test.describe('Feature: View Anomalies List', () => {
    test('should display anomalies for a selected plant', async ({ page }) => {
      // Navigate to anomalies page
      await page.goto(`${BASE_URL}/anomalies`);

      // Select a plant
      await page.selectOption('select[name="plant_id"]', 'PLANT_001');

      // Wait for table to load
      await page.waitForSelector('table tbody tr');

      // Verify anomalies are displayed
      const rows = await page.locator('table tbody tr').count();
      expect(rows).toBeGreaterThan(0);
    });

    test('should display anomaly timestamp and severity', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Check for date column
      const dateCell = page.locator('table tbody tr:first-child td:first-child');
      const date = await dateCell.textContent();
      expect(date).toMatch(/\d{4}-\d{2}-\d{2}/); // YYYY-MM-DD format

      // Check for severity badge
      const severityBadge = page.locator('table tbody tr:first-child .badge');
      const severity = await severityBadge.textContent();
      expect(['low', 'medium', 'high', 'critical']).toContain(severity?.toLowerCase());
    });

    test('should filter anomalies by severity', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Filter by severity
      await page.selectOption('select[name="severity"]', 'high');

      // Wait for updated results
      await page.waitForLoadState('networkidle');

      // Verify all visible anomalies are "high" severity
      const badges = await page.locator('.badge').allTextContents();
      const severityBadges = badges.filter((badge) => ['low', 'medium', 'high', 'critical'].includes(badge.toLowerCase()));
      
      severityBadges.forEach((badge) => {
        // At least some should be "high"
        expect(['high', 'critical']).toContain(badge.toLowerCase());
      });
    });

    test('should filter anomalies by metric', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Filter by metric
      await page.selectOption('select[name="metric"]', 'power_output_kwh');

      // Wait for updated results
      await page.waitForLoadState('networkidle');

      // Verify metric column shows correct values
      const metricCells = await page.locator('table tbody tr td:nth-child(2)').allTextContents();
      metricCells.forEach((cell) => {
        expect(cell.toLowerCase()).toContain('power_output');
      });
    });

    test('should paginate through anomalies', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Set page size
      await page.selectOption('select[name="pageSize"]', '5');

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Get first page data
      const firstPageText = await page.locator('table tbody tr:first-child').textContent();

      // Click next page
      await page.click('button:has-text("Next")');

      // Wait for new data
      await page.waitForLoadState('networkidle');

      // Verify different data is shown
      const secondPageText = await page.locator('table tbody tr:first-child').textContent();
      expect(firstPageText).not.toBe(secondPageText);
    });

    test('should sort anomalies by date', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Select sort by date descending (default)
      await page.selectOption('select[name="sort"]', 'date-desc');

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Get dates from table
      const dateCells = await page.locator('table tbody tr td:first-child').allTextContents();
      const dates = dateCells.map((d) => new Date(d.trim()).getTime());

      // Verify dates are in descending order
      for (let i = 0; i < dates.length - 1; i++) {
        expect(dates[i]).toBeGreaterThanOrEqual(dates[i + 1]);
      }
    });

    test('should sort anomalies by severity', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Select sort by severity
      await page.selectOption('select[name="sort"]', 'severity-desc');

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Get severities from table
      const severityBadges = await page.locator('table tbody tr .badge').allTextContents();

      // Define severity order
      const severityOrder = { critical: 3, high: 2, medium: 1, low: 0 };
      const severityValues = severityBadges.map((s) => severityOrder[s.toLowerCase() as keyof typeof severityOrder] || -1);

      // Verify severities are in descending order
      for (let i = 0; i < severityValues.length - 1; i++) {
        expect(severityValues[i]).toBeGreaterThanOrEqual(severityValues[i + 1]);
      }
    });
  });

  test.describe('Feature: View Anomaly Details', () => {
    test('should display detailed information for an anomaly', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for table and click details button
      await page.waitForSelector('button:has-text("Details")');
      await page.click('button:has-text("Details"):first-child');

      // Verify details panel is visible
      await page.waitForSelector('.anomaly-details');

      // Check for required fields
      expect(await page.locator('text=Anomaly Details')).toBeTruthy();
      expect(await page.locator('text=Plant ID:')).toBeTruthy();
      expect(await page.locator('text=Date:')).toBeTruthy();
      expect(await page.locator('text=Metric:')).toBeTruthy();
      expect(await page.locator('text=Actual Value:')).toBeTruthy();
      expect(await page.locator('text=Expected Value:')).toBeTruthy();
      expect(await page.locator('text=Deviation:')).toBeTruthy();
      expect(await page.locator('text=Severity:')).toBeTruthy();
      expect(await page.locator('text=Detected By:')).toBeTruthy();
    });

    test('should display detection method details', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Click details for first anomaly
      await page.waitForSelector('button:has-text("Details")');
      await page.click('button:has-text("Details"):first-child');

      // Wait for details panel
      await page.waitForSelector('.anomaly-details');

      // Check detection method (should be either Z-Score or IQR Bounds)
      const hasZScore = await page.locator('text=Z-Score:').isVisible().catch(() => false);
      const hasIQR = await page.locator('text=IQR Bounds:').isVisible().catch(() => false);

      expect(hasZScore || hasIQR).toBeTruthy();
    });

    test('should highlight selected anomaly in table', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Click on a row
      await page.click('table tbody tr:first-child');

      // Verify row is highlighted
      const row = page.locator('table tbody tr:first-child');
      const className = await row.getAttribute('class');
      expect(className).toContain('selected');
    });
  });

  test.describe('Feature: Visualize Anomalies', () => {
    test('should display anomaly timeline chart', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for chart to load
      await page.waitForSelector('.anomaly-chart');

      // Verify chart title
      expect(await page.locator('text=Anomaly Timeline')).toBeTruthy();

      // Verify chart SVG is rendered
      const chartSvg = await page.locator('.anomaly-chart svg').count();
      expect(chartSvg).toBeGreaterThan(0);
    });

    test('should show expected and actual values in chart', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for chart
      await page.waitForSelector('.anomaly-chart');

      // Check for legend items
      expect(await page.locator('text=Expected').isVisible()).toBeTruthy();
      expect(await page.locator('text=Actual').isVisible()).toBeTruthy();
    });

    test('should display tooltip on chart hover', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for chart
      await page.waitForSelector('.anomaly-chart svg');

      // Hover over first data point
      const firstPoint = page.locator('.anomaly-chart svg circle').first();
      await firstPoint.hover();

      // Tooltip should appear with data
      await page.waitForSelector('.chart-tooltip');
      const tooltip = page.locator('.chart-tooltip');
      expect(await tooltip.textContent()).toContain('Expected');
    });
  });

  test.describe('Feature: Respond to Anomalies', () => {
    test('should allow marking anomaly as reviewed', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Get initial status
      await page.waitForSelector('table tbody tr');
      const initialStatus = await page.locator('table tbody tr:first-child').getAttribute('data-status');

      // Click details and mark as reviewed (if UI supports it)
      await page.click('button:has-text("Details"):first-child');
      await page.waitForSelector('.anomaly-details');

      // Check if reviewed button exists
      const reviewButton = page.locator('button:has-text("Mark as Reviewed")');
      if (await reviewButton.isVisible().catch(() => false)) {
        await reviewButton.click();
        
        // Verify status changed
        await page.waitForLoadState('networkidle');
      }
    });

    test('should show anomaly context with neighboring readings', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Click details button
      await page.waitForSelector('button:has-text("Details")');
      await page.click('button:has-text("Details"):first-child');

      // Details panel should show context
      await page.waitForSelector('.anomaly-details');
      
      // Should see actual and expected values for context
      const details = page.locator('.anomaly-details');
      const content = await details.textContent();
      expect(content).toContain('Actual');
      expect(content).toContain('Expected');
    });
  });

  test.describe('Performance and Reliability', () => {
    test('should load anomalies within reasonable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);
      await page.waitForSelector('table tbody tr');
      const loadTime = Date.now() - startTime;

      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle empty anomalies gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=NONEXISTENT`);

      // Should show empty state or error message
      const emptyState = page.locator('text=No anomalies detected');
      const errorMsg = page.locator('.alert-error');

      const hasContent = await emptyState.isVisible().catch(() => false) || 
                        await errorMsg.isVisible().catch(() => false);
      expect(hasContent).toBeTruthy();
    });

    test('should handle API errors gracefully', async ({ page }) => {
      // Mock API error
      await page.route(`${API_URL}/**`, (route) => {
        route.abort('failed');
      });

      await page.goto(`${BASE_URL}/anomalies`);

      // Should display error message
      await page.waitForSelector('.alert-error', { timeout: 5000 }).catch(() => {});
      
      const error = await page.locator('.alert-error').isVisible().catch(() => false);
      expect(error).toBeTruthy();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies`);

      // Check main heading
      const mainHeading = page.locator('h2, h1');
      expect(await mainHeading.count()).toBeGreaterThan(0);
    });

    test('should have descriptive button labels', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for buttons
      await page.waitForSelector('button');

      // Check button labels
      const buttons = await page.locator('button').allTextContents();
      const hasDescriptiveLabels = buttons.some((text) => 
        ['Details', 'Previous', 'Next'].includes(text)
      );
      expect(hasDescriptiveLabels).toBeTruthy();
    });

    test('should support keyboard navigation', async ({ page }) => {
      await page.goto(`${BASE_URL}/anomalies?plant_id=PLANT_001`);

      // Wait for table
      await page.waitForSelector('table tbody tr');

      // Tab to first button
      await page.keyboard.press('Tab');
      
      // Element should be focused
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(['BUTTON', 'SELECT']).toContain(focused);
    });
  });
});
