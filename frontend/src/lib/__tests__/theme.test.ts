import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getTheme, setTheme, THEMES, getEffectiveTheme, setupSystemThemeSync } from '../theme'

describe('Theme System', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('getTheme returns default "normal" when nothing stored', () => {
    expect(getTheme()).toBe('normal')
  })

  it('setTheme stores theme in localStorage', () => {
    setTheme('dark')
    expect(localStorage.getItem('great-theme')).toBe('dark')
  })

  it('setTheme sets class on html element', () => {
    setTheme('dark')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })

  it('setTheme removes previous theme class', () => {
    setTheme('dark')
    setTheme('steampunk')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(true)
  })

  it('getTheme returns stored theme', () => {
    localStorage.setItem('great-theme', 'rainbow')
    expect(getTheme()).toBe('rainbow')
  })

  it('THEMES contains all 6 themes', () => {
    expect(THEMES).toContain('normal')
    expect(THEMES).toContain('dark')
    expect(THEMES).toContain('steampunk')
    expect(THEMES).toContain('rainbow')
    expect(THEMES).toContain('heavy-metal')
    expect(THEMES).toContain('system')
  })

  // REQ-3062: System theme tests
  it('THEMES contains system theme', () => {
    expect(THEMES).toContain('system')
  })

  it('getTheme returns "normal" for unknown stored value', () => {
    localStorage.setItem('great-theme', 'unknown-theme')
    expect(getTheme()).toBe('normal')
  })

  it('setTheme with "normal" applies theme-normal class (HSV colors)', () => {
    setTheme('dark')
    setTheme('normal')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
    expect(document.documentElement.classList.contains('theme-normal')).toBe(true)
  })

  it('setTheme with "system" and OS=light applies no class (uses :root)', () => {
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    setTheme('system')
    expect(document.documentElement.classList.contains('theme-normal')).toBe(false)
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
    expect(localStorage.getItem('great-theme')).toBe('system')
  })

  it('setTheme switches from normal to system (OS=light) and removes theme-normal', () => {
    setTheme('normal')
    expect(document.documentElement.classList.contains('theme-normal')).toBe(true)

    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    setTheme('system')
    expect(document.documentElement.classList.contains('theme-normal')).toBe(false)
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
  })
})

// REQ-3062: System theme tests
describe('System Theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('getEffectiveTheme returns dark when OS prefers dark', () => {
    // Mock matchMedia to return dark preference
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    
    expect(getEffectiveTheme('system')).toBe('dark')
  })

  it('getEffectiveTheme returns normal when OS prefers light', () => {
    // Mock matchMedia to return light preference
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    
    expect(getEffectiveTheme('system')).toBe('normal')
  })

  it('getEffectiveTheme returns same theme for non-system themes', () => {
    expect(getEffectiveTheme('dark')).toBe('dark')
    expect(getEffectiveTheme('steampunk')).toBe('steampunk')
    expect(getEffectiveTheme('rainbow')).toBe('rainbow')
  })

  it('setTheme with system applies effective theme class', () => {
    // Mock matchMedia to return dark preference
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    
    setTheme('system')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
    expect(localStorage.getItem('great-theme')).toBe('system')
  })

  it('setupSystemThemeSync registers and cleans up listener', () => {
    const addListener = vi.fn()
    const removeListener = vi.fn()
    
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: addListener,
      removeEventListener: removeListener,
    }))
    
    const cleanup = setupSystemThemeSync(() => {})
    expect(addListener).toHaveBeenCalledWith('change', expect.any(Function))
    
    cleanup()
    expect(removeListener).toHaveBeenCalledWith('change', expect.any(Function))
  })
})
