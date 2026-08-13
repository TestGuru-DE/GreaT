import { test, expect } from '@playwright/test'

test('API Health-Check erreichbar', async ({ request }) => {
  // Direkt Backend ansprechen
  const response = await request.get('http://localhost:8000/health')
  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  expect(body.status).toBe('ok')
})
