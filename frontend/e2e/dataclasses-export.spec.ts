/**
 * E2E Test: REQ-4013 Datenklassen Export
 * Testet den Export-Endpunkt direkt (API-Level) und via Frontend-Button.
 * Läuft gegen http://localhost:8000 (Start.bat).
 */
import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

test.describe("REQ-4013: Datenklassen Export", () => {

  test("Export-API liefert gueltige JSON-Datei (direkt)", async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/datanodes/export-user`);

    // Status 200
    expect(response.status()).toBe(200);

    // Content-Disposition: attachment mit .json
    const contentDisposition = response.headers()["content-disposition"] ?? "";
    expect(contentDisposition).toContain("attachment");
    expect(contentDisposition).toContain(".json");

    // Body ist gueltiges JSON
    const text = await response.text();
    const data = JSON.parse(text);
    expect(data).toHaveProperty("version");
    expect(data).toHaveProperty("datanodes");
    expect(Array.isArray(data.datanodes)).toBe(true);

    console.log(
      `Export OK: version=${data.version}, ${data.datanodes.length} Eintraege`
    );
  });

  test("Export-Button laedt JSON herunter (UI)", async ({ page }) => {
    // Frontend laden (Port 8000)
    await page.goto(`${BASE_URL}/app`);
    await page.waitForLoadState("networkidle");

    // Navigiere zu "Datenklassen"
    await page.click('text=Datenklassen');
    await page.waitForLoadState("networkidle");

    // Seite geladen?
    await expect(page.locator("text=Datenklassen-Bibliothek")).toBeVisible({ timeout: 8000 });

    // Download-Event abfangen und Export-Button klicken
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.locator('a[href*="export-user"], a[download*="dataclasses"], a:has-text("Exportieren")').first().click(),
    ]);

    // Dateiname enthält .json
    expect(download.suggestedFilename()).toMatch(/\.json$/);

    // Dateiinhalt ist gueltiges JSON
    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream) {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }
    const text = Buffer.concat(chunks).toString("utf-8");
    const data = JSON.parse(text);

    expect(data).toHaveProperty("version");
    expect(data).toHaveProperty("datanodes");
    expect(Array.isArray(data.datanodes)).toBe(true);

    console.log(
      `UI Export OK: Datei="${download.suggestedFilename()}", version=${data.version}, ${data.datanodes.length} Eintraege`
    );
  });
});