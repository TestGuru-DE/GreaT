import { useState } from 'react'
import { THEMES, getTheme, setTheme, type ThemeName } from '../lib/theme'

// REQ-3045 (Sofort-Fix): Label wieder schlichtes "Normal" - "(HSV)" war
// irrefuehrend, da die aktuelle Ziel-Palette (Hintergrund blau, Schrift weiss,
// Akzent ROT) keine Hamburger-SV-Vereinsfarben (Blau/Weiss, kein Rot) mehr sind.
const THEME_LABELS: Record<ThemeName, string> = {
  'normal': '☀️ Normal',
  'dark': '🌙 Dark',
  'steampunk': '⚙️ Steampunk',
  'rainbow': '🌈 Rainbow',
  'heavy-metal': '🤘 Heavy Metal',
  'system': '🖥️ System (OS)',
}

export function ThemeSwitcher() {
  const [current, setCurrent] = useState<ThemeName>(getTheme())

  function handleSelect(theme: ThemeName) {
    setTheme(theme)
    setCurrent(theme)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {THEMES.map(theme => (
        <button
          key={theme}
          onClick={() => handleSelect(theme)}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
            // REQ-3045 (Sofort-Fix): Theme-Tokens statt hartkodiertem bg-blue-50/bg-gray-100,
            // damit der Umschalter selbst dem aktiven Theme sichtbar folgt.
            current === theme
              ? 'ring-2 ring-theme-accent bg-theme-accent text-theme-accent-text'
              : 'bg-theme-surface text-theme-text-secondary hover:bg-theme-surface-hover hover:text-theme-text'
          }`}
        >
          {THEME_LABELS[theme]}
        </button>
      ))}
    </div>
  )
}
