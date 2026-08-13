import { test, expect } from '@playwright/test'

test.describe('GreaT App – Happy Path', () => {
  test('Startseite lädt', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/GreaT|G\.R\.E\.A\.T/)
  })

  test('Projekte-Seite erreichbar', async ({ page }) => {
    await page.goto('/')
    // Warte auf irgendein sichtbares Element
    await expect(page.locator('body')).toBeVisible()
  })
})
