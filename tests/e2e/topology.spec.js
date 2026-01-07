const { test, expect } = require('@playwright/test');

test.describe('Topology View', () => {
    test.beforeEach(async ({ page }) => {
        // Force 'local' organization to ensure we see our mapped home hardware
        await page.goto('http://localhost:8001/topology?org_id=local');
    });

    test('should load the topology page', async ({ page }) => {
        await expect(page).toHaveTitle(/Network Topology/);
        // Correct selector from topology.html
        await page.waitForSelector('#topologyCanvas', { state: 'visible' });
    });

    test('should identify real devices in the topology', async ({ page }) => {
        // Wait for at least one device icon to be rendered, indicating data is loaded
        await page.waitForSelector('.device-icon', { timeout: 15000 });

        // Check for specific real-world devices rendered on the canvas
        // They are rendered as .device-icon elements with text labels below them
        const lgTv = page.locator('text=LGwebOSTV');
        const caServer = page.locator('text=CASERVER');

        await expect(lgTv).toBeVisible({ timeout: 15000 });
        await expect(caServer).toBeVisible({ timeout: 15000 });
    });

    test('should show device tooltip on hover', async ({ page }) => {
        await page.waitForSelector('.device-icon');
        const firstDevice = page.locator('.device-icon').first();

        await firstDevice.hover();

        const tooltip = page.locator('#deviceTooltip');
        await expect(tooltip).toHaveClass(/show/);
        await expect(tooltip).not.toBeEmpty();
    });
});
