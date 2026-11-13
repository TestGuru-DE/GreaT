import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeSwitcher } from '../ThemeSwitcher'

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('renders all 5 theme options', () => {
    render(<ThemeSwitcher />)
    expect(screen.getByText(/Normal/i)).toBeInTheDocument()
    expect(screen.getByText(/Dark/i)).toBeInTheDocument()
    expect(screen.getByText(/Steampunk/i)).toBeInTheDocument()
    expect(screen.getByText(/Rainbow/i)).toBeInTheDocument()
    expect(screen.getByText(/Heavy Metal/i)).toBeInTheDocument()
  })

  it('clicking a theme option applies theme', () => {
    render(<ThemeSwitcher />)
    fireEvent.click(screen.getByText(/Dark/i))
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })

  // REQ-3045 (Sofort-Fix): Die Sprint-11-Zwischenbezeichnung "Normal (HSV)" passte
  // nicht mehr zur neuen Ziel-Palette (Hintergrund blau, Schrift weiss, Akzent ROT -
  // Hamburger-SV-Vereinsfarben kennen kein Rot). Label daher wieder auf schlichtes
  // "Normal" zurueckgesetzt, um Nutzer nicht mit falscher Farb-Assoziation zu verwirren.
  it('renders plain "Normal" label for the normal theme (kein irrefuehrendes "(HSV)")', () => {
    render(<ThemeSwitcher />)
    expect(screen.getByText(/^☀️ Normal$/)).toBeInTheDocument()
  })

  it('active theme is visually highlighted', () => {
    render(<ThemeSwitcher />)
    const normalBtn = screen.getByText(/Normal/i).closest('button')
    expect(normalBtn).toHaveClass('ring-2')
  })

  // REQ-3045 (Sofort-Fix): Buttons nutzten hartkodierte bg-blue-50/bg-gray-100 statt
  // Theme-Tokens - dadurch sah der Umschalter selbst in jedem Theme gleich (hell) aus.
  it('aktiver Theme-Button nutzt Theme-Accent-Token statt hartkodiertem bg-blue-50', () => {
    render(<ThemeSwitcher />)
    const normalBtn = screen.getByText(/Normal/i).closest('button')!
    expect(normalBtn.className).not.toMatch(/\bbg-blue-50\b/)
    expect(normalBtn.className).toMatch(/\bbg-theme-accent\b/)
  })

  it('inaktiver Theme-Button nutzt Theme-Surface-Token statt hartkodiertem bg-gray-100', () => {
    render(<ThemeSwitcher />)
    const darkBtn = screen.getByText(/Dark/i).closest('button')!
    expect(darkBtn.className).not.toMatch(/\bbg-gray-100\b/)
    expect(darkBtn.className).toMatch(/\bbg-theme-surface\b/)
  })

  it('clicking different theme switches correctly', () => {
    render(<ThemeSwitcher />)
    
    fireEvent.click(screen.getByText(/Steampunk/i))
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(true)
    expect(localStorage.getItem('great-theme')).toBe('steampunk')
    
    fireEvent.click(screen.getByText(/Rainbow/i))
    expect(document.documentElement.classList.contains('theme-steampunk')).toBe(false)
    expect(document.documentElement.classList.contains('theme-rainbow')).toBe(true)
    expect(localStorage.getItem('great-theme')).toBe('rainbow')
  })
})
