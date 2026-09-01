import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SettingsPage from '../SettingsPage';

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => ({ imported: false }),
  })));
});

describe('SettingsPage', () => {
  it('renders the port settings block', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Port-Einstellung/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Bevorzugter Port/i)).toBeInTheDocument();
  });

  it('does not render mojibake artifacts anywhere on the page', () => {
    // Bugfix-Scope: kaputte Emoji-Escapes (z.B. ðŸ’¾, ðŸ—‚ï¸, â³, âœ…, âŒ) duerfen nicht sichtbar sein.
    const { container } = render(<SettingsPage />);

    expect(container.textContent).not.toMatch(/ðŸ/);
    expect(container.textContent).not.toMatch(/â³|âœ…|âŒ/);
  });

  it('does not render a visible "(REQ-4011)" traceability marker in the UI', () => {
    // Bugfix-Scope: Requirement-IDs sind Doku-Traceability, keine UI-Texte.
    render(<SettingsPage />);

    expect(screen.queryByText(/\(REQ-4011\)/)).not.toBeInTheDocument();
  });

  it('renders the backup section heading with a real emoji instead of a mojibake sequence', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Datensicherung/i)).toBeInTheDocument();
  });

  it('renders the data classes section heading without mojibake', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Datenklassen/i)).toBeInTheDocument();
  });

  // REQ-4018
  it('renders the max-testcases settings block with default 1000', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Maximale Anzahl Testfälle/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Obergrenze pro Generierung/i)).toHaveValue(1000);
  });
});
