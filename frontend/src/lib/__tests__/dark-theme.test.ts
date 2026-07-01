import { describe, it, expect, beforeEach } from 'vitest'
import { setTheme, getTheme } from '../theme'

describe('Dark Theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('setTheme dark applies theme-dark class to html', () => {
    setTheme('dark')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })

  it('dark theme persists after page reload simulation', () => {
    setTheme('dark')
    // Simulate reload: clear class, call getTheme
    document.documentElement.className = ''
    const stored = getTheme()
    expect(stored).toBe('dark')
    setTheme(stored)
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })

  it('switching from dark to normal removes theme-dark class', () => {
    setTheme('dark')
    setTheme('normal')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
  })

  it('dark theme uses correct class name (not typo)', () => {
    setTheme('dark')
    expect(document.documentElement.className).toBe('theme-dark')
  })
})
