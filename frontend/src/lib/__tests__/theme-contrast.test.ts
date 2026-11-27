/**
 * Lesbarkeit in allen Themes (Redesign, WCAG 2.1 AA: Kontrast >= 4,5:1 fuer Text).
 *
 * 1. Jedes Theme in src/index.css definiert alle Tokens, und jedes Paar aus
 *    Textfarbe und Flaeche, das die Oberflaeche verwendet, erreicht 4,5:1.
 * 2. Komponenten verwenden keine festen Tailwind-Farben (bg-white, text-slate-700 ...),
 *    sonst ignorieren sie das Theme. Erlaubt: text-white auf Akzent-/Fehler-/Erfolgsflaechen
 *    und halbtransparentes Schwarz hinter Dialogen.
 */
import { describe, test, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const SRC = path.resolve(__dirname, '../..')
const css = fs.readFileSync(path.join(SRC, 'index.css'), 'utf-8')

function luminance(hex: string): number {
  const toLinear = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  const [r, g, b] = [1, 3, 5].map((i) => toLinear(parseInt(hex.slice(i, i + 2), 16) / 255))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

function themeTokens(selector: string): Record<string, string> {
  const escaped = selector.replace('.', '\\.')
  const block = css.match(new RegExp(`(?:^|\\n)${escaped}\\s*\\{([^}]*)\\}`))
  if (!block) throw new Error(`Theme ${selector} fehlt in index.css`)
  return Object.fromEntries([...block[1].matchAll(/--color-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})/g)].map((m) => [m[1], m[2]]))
}

const THEMES = [':root', '.theme-light', '.theme-dark', '.theme-steampunk', '.theme-rainbow', '.theme-heavy-metal']
const SURFACES = ['bg', 'sidebar', 'surface', 'surface-2', 'surface-hover']
const TEXTS = ['text-primary', 'text-secondary', 'text-muted', 'link', 'danger', 'success', 'warning']
const PAIRS: [string, string][] = [
  ...TEXTS.flatMap((t) => SURFACES.map((s) => [t, s] as [string, string])),
  ['accent-text', 'accent'], ['accent-text', 'accent-hover'],
  ['#ffffff', 'accent'], ['#ffffff', 'danger-fill'], ['#ffffff', 'success-fill'],
  ['danger', 'danger-soft'], ['success', 'success-soft'], ['warning', 'warning-soft'], ['link', 'accent-soft'],
  ['text-primary', 'danger-soft'], ['text-primary', 'success-soft'], ['text-primary', 'warning-soft'], ['text-primary', 'accent-soft'],
  // Tooltip: invertierte Farben
  ['bg', 'text-primary'],
]

describe('Theme-Kontrast WCAG AA (>= 4,5:1) fuer alle Themes', () => {
  test.each(THEMES)('%s: alle Text-/Flaechenpaare', (theme) => {
    const tokens = themeTokens(theme)
    const failures: string[] = []
    for (const [fg, bg] of PAIRS) {
      const fgHex = fg.startsWith('#') ? fg : tokens[fg]
      const bgHex = tokens[bg]
      expect(fgHex, `${theme}: Token ${fg} fehlt`).toBeDefined()
      expect(bgHex, `${theme}: Token ${bg} fehlt`).toBeDefined()
      const ratio = contrast(fgHex, bgHex)
      if (ratio < 4.5) failures.push(`${fg} auf ${bg} = ${ratio.toFixed(2)}:1`)
    }
    expect(failures).toEqual([])
  })
})

function sourceFiles(dir: string): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = path.join(dir, e.name)
    if (e.isDirectory()) return e.name === '__tests__' ? [] : sourceFiles(full)
    return /\.(tsx|ts)$/.test(e.name) && !/\.test\./.test(e.name) ? [full] : []
  })
}

const PALETTE = '(?:white|black|gray|slate|zinc|neutral|stone|red|blue|green|yellow|amber|orange|purple|indigo|sky|emerald|pink|rose|teal|cyan|violet|lime|fuchsia|primary)'
const FIXED_COLOR = new RegExp(
  `(?<![\\w-])(?:[a-z-]+:)*(?:bg|text|border(?:-[lrtbxy])?|ring|divide|from|via|to|outline|fill|stroke|placeholder)-${PALETTE}(?:-\\d{2,3})?(?:/\\d+)?(?![\\w-])`,
  'g',
)
const ALLOWED = new Set(['text-white', 'bg-black'])

describe('Keine festen Tailwind-Farben in Komponenten', () => {
  test('alle Farben kommen aus Theme-Tokens', () => {
    const hits: string[] = []
    for (const file of sourceFiles(SRC)) {
      const lines = fs.readFileSync(file, 'utf-8').split('\n')
      lines.forEach((line, i) => {
        if (/^\s*(\/\/|\*|\/\*)/.test(line)) return
        for (const m of line.matchAll(FIXED_COLOR)) {
          const cls = m[0].replace(/^(?:[a-z-]+:)*/, '')
          if (ALLOWED.has(cls) || /^bg-black\/\d+$/.test(cls)) continue
          hits.push(`${path.relative(SRC, file)}:${i + 1} ${m[0]}`)
        }
      })
    }
    expect(hits).toEqual([])
  })
})
