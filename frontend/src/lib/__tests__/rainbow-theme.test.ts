import { describe, it, expect, beforeEach } from 'vitest'
import { setTheme, getTheme } from '../theme'

describe('Rainbow Theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('setTheme rainbow applies theme-rainbow class', () => {
    setTheme('rainbow')
    expect(document.documentElement.classList.contains('theme-rainbow')).toBe(true)
  })

  it('rainbow theme persists in localStorage', () => {
    setTheme('rainbow')
    expect(getTheme()).toBe('rainbow')
  })

  it('switching from rainbow to normal removes class', () => {
    setTheme('rainbow')
    setTheme('normal')
    expect(document.documentElement.classList.contains('theme-rainbow')).toBe(false)
  })
})
