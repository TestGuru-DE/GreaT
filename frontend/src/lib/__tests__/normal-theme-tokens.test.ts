/**
 * REQ-3045: "Normal"-Theme zeigt HSV-Farben (Hintergrund BLAU, Schrift WEISS, Akzente ROT).
 *
 * Das Normal-Theme wird als .theme-normal CSS-Klasse implementiert.
 * :root ist die helle Basis (wird von "System (OS)" bei Light-Mode verwendet).
 *
 * Diese Tests lesen die tatsaechliche CSS-Datei (Source of Truth fuer Theme-Tokens),
 * damit sie echte Regressionen erkennen und nicht nur eine Kopie der Werte sind.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readNormalThemeBlock(): string {
  const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf-8')
  const match = css.match(/\.theme-normal\s*{([^}]*)}/)
  if (!match) throw new Error('.theme-normal Block nicht gefunden in index.css')
  return match[1]
}

// WCAG 2.0 relative Luminanz
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

describe('REQ-3045 Normal-Theme (HSV: Hintergrund blau, Schrift weiss, Akzent rot)', () => {

  it('index.css .theme-normal Block existiert', () => {
    const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf-8')
    expect(css).toMatch(/\.theme-normal\s*{/)
  })

  it('.theme-normal --color-bg ist Blau (#1e3a8a)', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-bg:\s*#1e3a8a;/)
  })

  it('.theme-normal --color-surface ist ein abgesetztes Blau', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-surface:\s*#1e40af;/)
  })

  it('.theme-normal --color-surface-hover ist definiert', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-surface-hover:\s*#1d4ed8;/)
  })

  it('.theme-normal --color-text-primary ist Weiss (#ffffff)', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-text-primary:\s*#ffffff;/)
  })

  it('.theme-normal --color-text-secondary/--color-text-muted sind helle Blaetoene', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-text-secondary:\s*#dbeafe;/)
    expect(block).toMatch(/--color-text-muted:\s*#93c5fd;/)
  })

  it('.theme-normal --color-accent ist Rot (#dc2626)', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-accent:\s*#dc2626;/)
  })

  it('.theme-normal --color-accent-hover ist ein dunkleres Rot', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-accent-hover:\s*#b91c1c;/)
  })

  it('.theme-normal --color-accent-text ist Weiss (Lesbarkeit auf rotem Accent-Button)', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-accent-text:\s*#ffffff;/)
  })

  it('.theme-normal --color-danger/--color-success/--color-warning sind definiert', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/--color-danger:\s*#f87171;/)
    expect(block).toMatch(/--color-success:\s*#4ade80;/)
    expect(block).toMatch(/--color-warning:\s*#fbbf24;/)
  })

  it('.theme-normal setzt color-scheme: dark (dunkler Hintergrund fuer native Formularelemente)', () => {
    const block = readNormalThemeBlock()
    expect(block).toMatch(/color-scheme:\s*dark;/)
  })

  it('Kontrast Text-Primary (#ffffff) auf Hintergrund (#1e3a8a) erfuellt WCAG AA (>=4.5:1)', () => {
    const ratio = contrastRatio('#ffffff', '#1e3a8a')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
  })

  it('Kontrast Accent-Text (#ffffff) auf Accent-Farbe (#dc2626) erfuellt WCAG AA (>=4.5:1)', () => {
    const ratio = contrastRatio('#ffffff', '#dc2626')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
  })

  it('Kontrast Text-Secondary (#dbeafe) auf Hintergrund (#1e3a8a) erfuellt WCAG AA (>=4.5:1)', () => {
    const ratio = contrastRatio('#dbeafe', '#1e3a8a')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
  })
})