import { describe, it, expect, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MaxTestCasesSettingsCard } from '../MaxTestCasesSettingsCard';

describe('MaxTestCasesSettingsCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the default of 1000 test cases', () => {
    render(<MaxTestCasesSettingsCard />);

    expect(screen.getByLabelText(/Obergrenze pro Generierung/i)).toHaveValue(1000);
    expect(screen.getAllByText(/1000/).length).toBeGreaterThan(0);
  });

  it('stores a valid custom value and confirms without requiring a restart', () => {
    render(<MaxTestCasesSettingsCard />);

    fireEvent.change(screen.getByLabelText(/Obergrenze pro Generierung/i), { target: { value: '250' } });
    fireEvent.click(screen.getByRole('button', { name: /Speichern/i }));

    expect(localStorage.getItem('great-max-testcases')).toBe('250');
    expect(screen.getByText(/250 Testfälle gesetzt/i)).toBeInTheDocument();
  });

  it('rejects zero with a visible error message (no silent failure)', () => {
    render(<MaxTestCasesSettingsCard />);

    fireEvent.change(screen.getByLabelText(/Obergrenze pro Generierung/i), { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: /Speichern/i }));

    expect(screen.getByText(/zwischen/i)).toBeInTheDocument();
    expect(localStorage.getItem('great-max-testcases')).toBeNull();
  });

  it('rejects unreasonably large values with a visible error message', () => {
    render(<MaxTestCasesSettingsCard />);

    fireEvent.change(screen.getByLabelText(/Obergrenze pro Generierung/i), { target: { value: '999999999' } });
    fireEvent.click(screen.getByRole('button', { name: /Speichern/i }));

    expect(screen.getByText(/zwischen/i)).toBeInTheDocument();
    expect(localStorage.getItem('great-max-testcases')).toBeNull();
  });

  it('loads a previously stored value on mount', () => {
    localStorage.setItem('great-max-testcases', '42');
    render(<MaxTestCasesSettingsCard />);

    expect(screen.getByLabelText(/Obergrenze pro Generierung/i)).toHaveValue(42);
  });
});
