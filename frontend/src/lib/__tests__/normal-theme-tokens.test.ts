/**
 * Redesign (PO-Vorgabe 27.11.2026): "Normal" ist das Graphit-Design aus dem Designbeispiel,
 * "Hell" (.theme-light) die helle Variante im selben Stil. Ersetzt die blaue Palette aus REQ-3045.
 */
import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const css = fs.readFileSync(path.resolve(__dirname, '../../index.css'), 'utf-8')

function block(selector: string): string {
  const m = css.match(new RegExp(`(?:^|\\n)${selector.replace('.', '\\.')}\\s*\\{([^}]*)\\}`))
  if (!m) throw new Error(`${selector} fehlt`)
  return m[1]
}

describe('Normal (:root) = Graphit', () => {
  const root = block(':root')
  it('dunkler Graphit-Hintergrund', () => {
    expect(root).toMatch(/--color-bg:\s*#1c1c1e;/)
  })
  it('helle Schrift', () => {
    expect(root).toMatch(/--color-text-primary:\s*#f5f5f7;/)
  })
  it('blauer Akzent mit weisser Schrift', () => {
    expect(root).toMatch(/--color-accent:\s*#0a6fdb;/)
    expect(root).toMatch(/--color-accent-text:\s*#ffffff;/)
  })
  it('color-scheme: dark', () => {
    expect(root).toMatch(/color-scheme:\s*dark;/)
  })
})

describe('Hell (.theme-light)', () => {
  const light = block('.theme-light')
  it('heller Hintergrund, weisse Karten, dunkle Schrift', () => {
    expect(light).toMatch(/--color-bg:\s*#f5f5f7;/)
    expect(light).toMatch(/--color-surface:\s*#ffffff;/)
    expect(light).toMatch(/--color-text-primary:\s*#1d1d1f;/)
  })
  it('color-scheme: light', () => {
    expect(light).toMatch(/color-scheme:\s*light;/)
  })
})
