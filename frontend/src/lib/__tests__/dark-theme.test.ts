import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setTheme, getTheme } from '../theme'

describe('Dark Theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    
    // REQ-3062: Mock matchMedia for system theme
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
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
