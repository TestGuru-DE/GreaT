export const THEMES = ['normal', 'dark', 'steampunk', 'rainbow', 'heavy-metal', 'system'] as const
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
  
  // Alle alten Theme-Klassen entfernen
  THEMES.forEach(t => {
    if (t !== 'normal' && t !== 'system') {
      document.documentElement.classList.remove(`${THEME_PREFIX}${t}`)
    }
  })
  
  // Neue Theme-Klasse setzen (normal braucht keine extra Klasse)
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
 */
export function getEffectiveTheme(theme: ThemeName): Exclude<ThemeName, 'system'> {
  if (theme !== 'system') return theme as Exclude<ThemeName, 'system'>
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'normal'
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
