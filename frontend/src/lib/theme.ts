export const THEMES = ['normal', 'light', 'dark', 'steampunk', 'rainbow', 'heavy-metal', 'system'] as const
export type ThemeName = typeof THEMES[number]

const STORAGE_KEY = 'great-theme'
const THEME_PREFIX = 'theme-'

export function getTheme(): ThemeName {
  const stored = localStorage.getItem(STORAGE_KEY) as ThemeName
  if (stored && THEMES.includes(stored)) return stored
  return 'normal'
}

export function setTheme(theme: ThemeName): void {
  // REQ-3062: Resolve 'system' to effective theme
  const effectiveTheme = getEffectiveTheme(theme)

  // Alle Theme-Klassen entfernen, dann die wirksame setzen.
  // "Normal" = Graphit-Design aus :root (keine Klasse); System -> light oder dark.
  THEMES.forEach(t => {
    document.documentElement.classList.remove(`${THEME_PREFIX}${t}`)
  })
  if (effectiveTheme !== 'normal') {
    document.documentElement.classList.add(`${THEME_PREFIX}${effectiveTheme}`)
  }

  localStorage.setItem(STORAGE_KEY, theme)
}

export function initTheme(): void {
  setTheme(getTheme())
}

/**
 * REQ-3062: Resolve 'system' theme to actual OS preference
 * Returns 'light' (internal) for light mode, 'dark' for dark mode
 */
export function getEffectiveTheme(theme: ThemeName): ThemeName | 'light' {
  if (theme !== 'system') return theme
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * REQ-3062: Setup listener for OS theme changes when 'system' is selected
 */
export function setupSystemThemeSync(onThemeChange: () => void): () => void {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const handler = () => {
    const saved = getTheme()
    if (saved === 'system') {
      setTheme('system')
      onThemeChange()
    }
  }
  mq.addEventListener('change', handler)
  return () => mq.removeEventListener('change', handler)
}
