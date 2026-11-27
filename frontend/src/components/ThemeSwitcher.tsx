import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check } from 'lucide-react'
import { THEMES, getTheme, setTheme, type ThemeName } from '../lib/theme'

// REQ-6005: i18n. Redesign: Auswahl als Kacheln mit Farbvorschau (Hintergrund, Flaeche, Akzent).
const THEME_KEYS: Record<ThemeName, string> = {
  'normal': 'themeSwitcher.normal',
  'light': 'themeSwitcher.light',
  'dark': 'themeSwitcher.dark',
  'steampunk': 'themeSwitcher.steampunk',
  'rainbow': 'themeSwitcher.rainbow',
  'heavy-metal': 'themeSwitcher.heavyMetal',
  'system': 'themeSwitcher.system',
}

// Vorschaufarben (entsprechen den Tokens in src/index.css)
const PREVIEW: Record<ThemeName, [string, string, string]> = {
  'normal': ['#1c1c1e', '#2e2e32', '#0a6fdb'],
  'light': ['#f5f5f7', '#ffffff', '#0071e3'],
  'dark': ['#000000', '#232326', '#0a6fdb'],
  'steampunk': ['#1c1410', '#35281d', '#8b5a00'],
  'rainbow': ['#fff5fe', '#fde7f3', '#c0267a'],
  'heavy-metal': ['#0d0d0d', '#242424', '#b01030'],
  'system': ['#f5f5f7', '#1c1c1e', '#0071e3'],
}

export function ThemeSwitcher() {
  const { t } = useTranslation()
  const [current, setCurrent] = useState<ThemeName>(getTheme())

  function handleSelect(theme: ThemeName) {
    setTheme(theme)
    setCurrent(theme)
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {THEMES.map(theme => {
        const [bg, surface, accent] = PREVIEW[theme]
        const active = current === theme
        return (
          <button
            key={theme}
            onClick={() => handleSelect(theme)}
            aria-pressed={active}
            className={`flex items-center gap-2.5 rounded-lg border px-2.5 py-2 text-sm font-medium text-left transition-colors ${
              active
                ? 'border-theme-accent bg-theme-accent-soft text-theme-text'
                : 'border-theme-border text-theme-text-secondary hover:bg-theme-surface-hover hover:text-theme-text'
            }`}
          >
            <span
              className="relative w-7 h-7 rounded-md border border-theme-border shrink-0 overflow-hidden"
              style={{ background: theme === 'system' ? `linear-gradient(135deg, ${bg} 50%, ${surface} 50%)` : bg }}
              aria-hidden="true"
            >
              {theme !== 'system' && (
                <span className="absolute left-1 right-1 bottom-1 h-2 rounded-sm" style={{ background: surface }} />
              )}
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ background: accent }} />
            </span>
            <span className="flex-1 truncate">{t(THEME_KEYS[theme])}</span>
            {active && <Check className="w-4 h-4 text-theme-link" aria-hidden="true" />}
          </button>
        )
      })}
    </div>
  )
}
