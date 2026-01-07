const { test, expect } = require('@playwright/test');

test.describe('Icon Library Page', () => {
    test.beforeEach(async ({ page }) => {
        // Assuming the app is running on port 8001
        await page.goto('http://localhost:8001/icons');
    });

    test('should load the icon management page', async ({ page }) => {
        await expect(page).toHaveTitle(/Icon Management/);
        await expect(page.locator('h1')).toContainText('FortiGate Dashboard');
    });

    test('should display search and filter controls', async ({ page }) => {
        await expect(page.locator('#search-input')).toBeVisible();
        await expect(page.locator('#manufacturer-filter')).toBeVisible();
        await expect(page.locator('#device-type-filter')).toBeVisible();
    });

    test('should load icons into the grid', async ({ page }) => {
        // Wait for loading to disappear
        await page.waitForSelector('#loading', { state: 'hidden' });
        const iconCards = page.locator('.icon-card');
        await expect(iconCards.first()).toBeVisible();
    });

    test('should open icon details modal on click', async ({ page }) => {
        await page.waitForSelector('#loading', { state: 'hidden' });
        await page.locator('.icon-card').first().click();
        await expect(page.locator('#icon-modal')).toBeVisible();
        await expect(page.locator('#modal-title')).not.toBeEmpty();
    });
});
