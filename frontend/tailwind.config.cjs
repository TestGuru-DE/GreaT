/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class', // REQ-3045: Theme-System (class-basiert für theme-* Klassen)
  theme: {
    extend: {
      fontFamily: { sans: ['var(--font-sans)'] },
      borderRadius: { DEFAULT: '8px', lg: '10px', xl: '14px', '2xl': '18px' },
      colors: {
        // Theme-Tokens (CSS-Variablen je Theme, siehe src/index.css)
        'theme-bg': 'var(--color-bg)',
        'theme-sidebar': 'var(--color-sidebar)',
        'theme-surface': 'var(--color-surface)',
        'theme-surface-2': 'var(--color-surface-2)',
        'theme-surface-hover': 'var(--color-surface-hover)',
        'theme-border': 'var(--color-border)',
        'theme-border-strong': 'var(--color-border-strong)',
        'theme-accent': 'var(--color-accent)',
        'theme-accent-hover': 'var(--color-accent-hover)',
        'theme-accent-text': 'var(--color-accent-text)',
        'theme-link': 'var(--color-link)',
        'theme-accent-soft': 'var(--color-accent-soft)',
        'theme-danger': 'var(--color-danger)',
        'theme-danger-fill': 'var(--color-danger-fill)',
        'theme-danger-soft': 'var(--color-danger-soft)',
        'theme-danger-border': 'var(--color-danger-border)',
        'theme-success': 'var(--color-success)',
        'theme-success-fill': 'var(--color-success-fill)',
        'theme-success-soft': 'var(--color-success-soft)',
        'theme-success-border': 'var(--color-success-border)',
        'theme-warning': 'var(--color-warning)',
        'theme-warning-soft': 'var(--color-warning-soft)',
        'theme-warning-border': 'var(--color-warning-border)',
        'theme-text': 'var(--color-text-primary)',
        'theme-text-secondary': 'var(--color-text-secondary)',
        'theme-text-muted': 'var(--color-text-muted)',
      },
    },
  },
  plugins: [],
};
