export const THEMES = ['normal', 'dark', 'steampunk', 'rainbow', 'heavy-metal', 'system'] as const
export type ThemeName = typeof THEMES[number]

// Interne Theme-Klassen (nicht direkt waehlbar)
const INTERNAL_THEMES = ['light'] as const

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

  // Alle alten Theme-Klassen entfernen (inklusive interne)
  THEMES.forEach(t => {
    document.documentElement.classList.remove(`${THEME_PREFIX}${t}`)
  })
  INTERNAL_THEMES.forEach(t => {
    document.documentElement.classList.remove(`${THEME_PREFIX}${t}`)
  })

  // Neue Theme-Klasse setzen
  if (effectiveTheme !== 'normal' && effectiveTheme !== 'light') {
    // dark, steampunk, rainbow, heavy-metal
    document.documentElement.classList.add(`${THEME_PREFIX}${effectiveTheme}`)
  } else if (theme === 'normal') {
    // REQ-3045: Explizites "Normal" -> HSV-Farben (:root, keine Klasse benoetigt)
    // Keine Klasse setzen — :root hat HSV-Farben
  } else if (theme === 'system' && effectiveTheme === 'light') {
    // System=Light -> .theme-light Klasse
    document.documentElement.classList.add(`${THEME_PREFIX}light`)
  }
  // else: system=dark -> .theme-dark (wird durch effectiveTheme='dark' oben gesetzt)

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
