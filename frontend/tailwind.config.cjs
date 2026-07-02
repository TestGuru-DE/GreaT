/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class', // REQ-3045: Theme-System (class-basiert für theme-* Klassen)
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        // BUG-1 Fix: CSS-Variablen als Tailwind-Farben verfügbar machen
        'theme-bg': 'var(--color-bg)',
        'theme-surface': 'var(--color-surface)',
        'theme-surface-hover': 'var(--color-surface-hover)',
        'theme-border': 'var(--color-border)',
        'theme-text': 'var(--color-text-primary)',
        'theme-text-secondary': 'var(--color-text-secondary)',
        'theme-text-muted': 'var(--color-text-muted)',
        'theme-accent': 'var(--color-accent)',
        'theme-accent-hover': 'var(--color-accent-hover)',
        'theme-danger': 'var(--color-danger)',
        'theme-success': 'var(--color-success)',
        'theme-warning': 'var(--color-warning)',
      },
    },
  },
  plugins: [],
};
