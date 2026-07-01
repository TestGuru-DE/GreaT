export const THEMES = ['normal', 'dark', 'steampunk', 'rainbow', 'heavy-metal'] as const
export type ThemeName = typeof THEMES[number]

const STORAGE_KEY = 'great-theme'
const THEME_PREFIX = 'theme-'

export function getTheme(): ThemeName {
  const stored = localStorage.getItem(STORAGE_KEY) as ThemeName
  if (stored && THEMES.includes(stored)) return stored
  return 'normal'
}

export function setTheme(theme: ThemeName): void {
  // Alle alten Theme-Klassen entfernen
  THEMES.forEach(t => {
    if (t !== 'normal') {
      document.documentElement.classList.remove(`${THEME_PREFIX}${t}`)
    }
  })
  
  // Neue Theme-Klasse setzen (normal braucht keine extra Klasse)
  if (theme !== 'normal') {
    document.documentElement.classList.add(`${THEME_PREFIX}${theme}`)
  }
  
  localStorage.setItem(STORAGE_KEY, theme)
}

export function initTheme(): void {
  setTheme(getTheme())
}
