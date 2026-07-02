import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setTheme, getTheme } from '../theme'

describe('Steampunk Theme', () => {
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

  it('setTheme steampunk applies theme-steampunk class', () => {
    setTheme('steampunk')
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(true)
  })

  it('steampunk theme persists in localStorage', () => {
    setTheme('steampunk')
    expect(getTheme()).toBe('steampunk')
  })

  it('switching from steampunk to dark works correctly', () => {
    setTheme('steampunk')
    setTheme('dark')
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(false)
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })
})
