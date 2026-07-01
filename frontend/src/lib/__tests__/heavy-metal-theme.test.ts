import { describe, it, expect, beforeEach } from 'vitest'
import { THEMES, setTheme, getTheme } from '../theme'

describe('Heavy Metal Theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('setTheme heavy-metal applies theme-heavy-metal class', () => {
    setTheme('heavy-metal')
    expect(document.documentElement.classList.contains('theme-heavy-metal')).toBe(true)
  })

  it('heavy-metal theme persists in localStorage', () => {
    setTheme('heavy-metal')
    expect(getTheme()).toBe('heavy-metal')
  })

  it('switching from heavy-metal to steampunk works', () => {
    setTheme('heavy-metal')
    setTheme('steampunk')
    expect(document.documentElement.classList.contains('theme-heavy-metal')).toBe(false)
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(true)
  })

  it('all themes can be cycled without class leakage', () => {
    for (const theme of THEMES) {
      setTheme(theme)
      const activeClasses = Array.from(document.documentElement.classList)
        .filter(c => c.startsWith('theme-'))
      // Entweder genau 1 theme-Klasse (bei non-normal) oder 0 (bei normal)
      expect(activeClasses.length).toBeLessThanOrEqual(1)
      if (theme !== 'normal') {
        expect(activeClasses[0]).toBe(`theme-${theme}`)
      }
    }
  })
})
