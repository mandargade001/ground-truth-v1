import { test, expect } from '@playwright/test';

test.describe('GroundTruth E2E', () => {
    const TEST_USER = {
        username: 'test@example.com',
        password: 'password123'
    };

    test.beforeEach(async ({ page }) => {
        // 1. Go to Login
        await page.goto('http://localhost:3000/login');

        // 2. Fill Form
        await page.fill('input[type="text"]', TEST_USER.username);
        await page.fill('input[type="password"]', TEST_USER.password);

        // 3. Submit
        await page.click('button[type="submit"]');

        // 4. Expect Redirect to Home
        await expect(page).toHaveURL('http://localhost:3000/');

        // 5. Verify Sidebar loaded (GroundTruth text)
        await expect(page.locator('text=GroundTruth')).toBeVisible();
    });

    test('should handle file upload and chat', async ({ page }) => {
        // 1. Upload File
        // Create a dummy file
        const fileContent = 'This is a test document about Antigravity.';
        const buffer = Buffer.from(fileContent);

        // Trigger file chooser
        const fileChooserPromise = page.waitForEvent('filechooser');
        // Click the upload area (assuming there is a button or area, we might need a specific selector)
        // Looking at KnowledgeBase.tsx, it has an input type="file" but it's hidden? 
        // Usually standard file inputs work with setInputFiles.
        // Let's assume KnowledgeBase has a label or button that triggers it, or we target 'input[type="file"]' directly.

        // If input is hidden (display:none), Playwright can handle it.
        // We'll target the input directly.
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles({
            name: 'antigravity_test.txt',
            mimeType: 'text/plain',
            buffer: buffer,
        });

        // 2. Wait for upload to complete
        // KnowledgeBase shows a toast or the file in list.
        // We expect "antigravity_test.txt" to appear in the list.
        await expect(page.locator('text=antigravity_test.txt')).toBeVisible({ timeout: 10000 });
        // Expect status to be "Indexed" eventually (polling every 5s)
        await expect(page.locator('text=Indexed')).toBeVisible({ timeout: 15000 });

        // 3. Chat
        const chatInput = page.locator('textarea[placeholder="Type a message..."]'); // Check placeholder
        await chatInput.fill('What is this document about?');
        await page.keyboard.press('Enter');

        // 4. Verify Response
        // Expect "Antigravity" in the response
        await expect(page.locator('text=Antigravity').last()).toBeVisible({ timeout: 15000 });
    });
});
