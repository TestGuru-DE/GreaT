import { useState } from 'react'
import { THEMES, getTheme, setTheme, type ThemeName } from '../lib/theme'

const THEME_LABELS: Record<ThemeName, string> = {
  'normal': '☀️ Normal',
  'dark': '🌙 Dark',
  'steampunk': '⚙️ Steampunk',
  'rainbow': '🌈 Rainbow',
  'heavy-metal': '🤘 Heavy Metal',
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
            current === theme
              ? 'ring-2 ring-blue-500 dark:ring-sky-400 bg-blue-50 dark:bg-sky-900/30 dark:text-sky-300'
              : 'bg-gray-100 dark:bg-slate-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'
          }`}
        >
          {THEME_LABELS[theme]}
        </button>
      ))}
    </div>
  )
}
