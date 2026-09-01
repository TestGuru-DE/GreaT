import { describe, it, expect, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { PortSettingsCard } from '../PortSettingsCard';

describe('PortSettingsCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the default port 8000 and the dev-only note', () => {
    render(<PortSettingsCard />);

    expect(screen.getByLabelText(/Bevorzugter Port/i)).toHaveValue(8000);
    expect(screen.getByText(/5173/i)).toBeInTheDocument();
    expect(screen.getByText(/Dev-Option/i)).toBeInTheDocument();
  });

  it('stores a selected port and reminds about restart', () => {
    render(<PortSettingsCard />);

    fireEvent.change(screen.getByLabelText(/Bevorzugter Port/i), { target: { value: '9000' } });
    fireEvent.click(screen.getByRole('button', { name: /Speichern/i }));

    expect(localStorage.getItem('great-preferred-port')).toBe('9000');
    expect(screen.getByText(/Neustart erforderlich/i)).toBeInTheDocument();
  });
});

