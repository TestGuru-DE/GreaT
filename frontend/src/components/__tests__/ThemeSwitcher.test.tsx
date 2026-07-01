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

  it('active theme is visually highlighted', () => {
    render(<ThemeSwitcher />)
    const normalBtn = screen.getByText(/Normal/i).closest('button')
    expect(normalBtn).toHaveClass('ring-2')
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
