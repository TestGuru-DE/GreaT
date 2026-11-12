/**
 * REQ-3045: "Normal"-Theme = HSV-Farben (Hintergrund BLAU, Schrift WEISS, Akzente ROT).
 * :root hat HSV-Farben (Default und "Normal" Theme).
 * .theme-light ist fuer "System (OS)" bei Light-Mode.
 *
 * Diese Tests lesen die tatsaechliche CSS-Datei (Source of Truth fuer Theme-Tokens).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readRootThemeBlock(): string {
  const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf-8')
  const match = css.match(/:root\s*{([^}]*)}/)
  if (!match) throw new Error(':root Block nicht gefunden in index.css')
  return match[1]
}

function readLightThemeBlock(): string {
  const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf-8')
  const match = css.match(/\.theme-light\s*{([^}]*)}/)
  if (!match) throw new Error('.theme-light Block nicht gefunden in index.css')
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

describe('REQ-3045 :root = HSV (Normal-Theme Default)', () => {

  it(':root --color-bg ist Blau (#1e3a8a)', () => {
    const root = readRootThemeBlock()
    expect(root).toMatch(/--color-bg:\s*#1e3a8a;/)
  })

  it(':root --color-surface ist ein abgesetztes Blau', () => {
    const root = readRootThemeBlock()
    expect(root).toMatch(/--color-surface:\s*#1e40af;/)
  })

  it(':root --color-text-primary ist Weiss (#ffffff)', () => {
    const root = readRootThemeBlock()
    expect(root).toMatch(/--color-text-primary:\s*#ffffff;/)
  })

  it(':root --color-accent ist Rot (#dc2626)', () => {
    const root = readRootThemeBlock()
    expect(root).toMatch(/--color-accent:\s*#dc2626;/)
  })

  it(':root setzt color-scheme: dark', () => {
    const root = readRootThemeBlock()
    expect(root).toMatch(/color-scheme:\s*dark;/)
  })

  it('Kontrast Text-Primary (#ffffff) auf Hintergrund (#1e3a8a) erfuellt WCAG AA', () => {
    const ratio = contrastRatio('#ffffff', '#1e3a8a')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
  })
})

describe('System (OS) Light-Mode: .theme-light', () => {

  it('.theme-light existiert', () => {
    const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf-8')
    expect(css).toMatch(/\.theme-light\s*{/)
  })

  it('.theme-light --color-bg ist Weiss (#ffffff)', () => {
    const block = readLightThemeBlock()
    expect(block).toMatch(/--color-bg:\s*#ffffff;/)
  })

  it('.theme-light --color-text-primary ist Dunkelgrau (#1e293b)', () => {
    const block = readLightThemeBlock()
    expect(block).toMatch(/--color-text-primary:\s*#1e293b;/)
  })

  it('.theme-light --color-accent ist Blau (#0ea5e9)', () => {
    const block = readLightThemeBlock()
    expect(block).toMatch(/--color-accent:\s*#0ea5e9;/)
  })

  it('.theme-light setzt color-scheme: light', () => {
    const block = readLightThemeBlock()
    expect(block).toMatch(/color-scheme:\s*light;/)
  })

  it('Kontrast Text-Primary (#1e293b) auf Hintergrund (#ffffff) erfuellt WCAG AA', () => {
    const ratio = contrastRatio('#1e293b', '#ffffff')
    expect(ratio).toBeGreaterThanOrEqual(4.5)
  })
})