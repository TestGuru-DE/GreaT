import { describe, it, expect, beforeEach } from 'vitest'
import { getTheme, setTheme, THEMES } from '../theme'

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

  it('THEMES contains all 5 themes', () => {
    expect(THEMES).toContain('normal')
    expect(THEMES).toContain('dark')
    expect(THEMES).toContain('steampunk')
    expect(THEMES).toContain('rainbow')
    expect(THEMES).toContain('heavy-metal')
  })

  it('getTheme returns "normal" for unknown stored value', () => {
    localStorage.setItem('great-theme', 'unknown-theme')
    expect(getTheme()).toBe('normal')
  })

  it('setTheme with "normal" removes all theme classes', () => {
    setTheme('dark')
    setTheme('normal')
    expect(document.documentElement.classList.contains('theme-dark')).toBe(false)
    expect(document.documentElement.classList.contains('theme-normal')).toBe(false)
  })
})
