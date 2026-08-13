/**
 * Theme-Kontrast-Tests (REQ-3046 Dark, REQ-3047 Steampunk, REQ-3049 Heavy Metal)
 * WCAG AA: Kontrast ≥ 4.5:1 für Normal-Text
 */
import { describe, test, expect } from 'vitest'

// Vereinfachte relative Luminanz-Berechnung nach WCAG 2.0
function luminance(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  const toLinear = (c: number) => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b)
}

function contrastRatio(hex1: string, hex2: string): number {
  const l1 = luminance(hex1)
  const l2 = luminance(hex2)
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  return (lighter + 0.05) / (darker + 0.05)
}

describe('Theme Contrast WCAG AA (≥4.5:1)', () => {
  test('Dark: Text (#e2e8f0) auf Hintergrund (#1a1a2e)', () => {
    const ratio = contrastRatio('#e2e8f0', '#1a1a2e')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Dark text-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Dark: Muted Text (#94a3b8) auf Hintergrund (#1a1a2e)', () => {
    const ratio = contrastRatio('#94a3b8', '#1a1a2e')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Dark text-muted-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Steampunk: Text (#f5deb3) auf Hintergrund (#1c1410)', () => {
    const ratio = contrastRatio('#f5deb3', '#1c1410')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Steampunk text-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Steampunk: Muted Text (#c9a96e) auf Hintergrund (#1c1410)', () => {
    const ratio = contrastRatio('#c9a96e', '#1c1410')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Steampunk text-muted-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Heavy Metal: Text (#f0f0f0) auf Hintergrund (#0d0d0d)', () => {
    const ratio = contrastRatio('#f0f0f0', '#0d0d0d')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Heavy Metal text-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Heavy Metal: Muted Text (#a0a0a0) auf Hintergrund (#0d0d0d)', () => {
    const ratio = contrastRatio('#a0a0a0', '#0d0d0d')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Heavy Metal text-muted-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Light: Text (#1e293b) auf Hintergrund (#ffffff)', () => {
    const ratio = contrastRatio('#1e293b', '#ffffff')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Light text-bg: ${ratio.toFixed(2)}:1`)
  })

  test('Rainbow: Text (#1e003d) auf Hintergrund (#fff5fe)', () => {
    const ratio = contrastRatio('#1e003d', '#fff5fe')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
    console.log(`Rainbow text-bg: ${ratio.toFixed(2)}:1`)
  })
})
