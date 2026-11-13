import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPage from '../SettingsPage';

beforeEach(() => {
  localStorage.clear();

  vi.stubGlobal('URL.createObjectURL', vi.fn(() => 'blob:test-url'));
  vi.stubGlobal('fetch', vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    if (url === '/api/backup') {
      return {
        ok: true,
        blob: async () => new Blob(['backup-zip']),
      } as Response;
    }
    if (url === '/api/backup/reset') {
      return {
        ok: true,
        json: async () => ({ status: 'ok', reset: true }),
      } as Response;
    }
    return {
      ok: true,
      json: async () => ({ imported: false }),
    } as Response;
  }));
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

  it('renders the reset database button and protection dialog', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    const button = screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i });
    expect(button).toBeInTheDocument();

    await user.click(button);

    const dialog = screen.getByRole('dialog', { name: /Datenbank wirklich zuruecksetzen\?/i });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Ja mach/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Vorher Backup/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Upsi nein/i })).toBeInTheDocument();
  });

  it('triggers backup before database reset when choosing backup option', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Vorher Backup/i }));

    expect(fetchMock).toHaveBeenCalledWith('/api/backup');
  });

  it('resets the database when the confirmation is accepted', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Ja mach/i }));

    expect(fetchMock).toHaveBeenCalledWith('/api/backup/reset', expect.objectContaining({ method: 'POST' }));
  });

  // REQ-4027 AK-12 / REQ-4028: Kein Passwort mehr nach Reset anzeigen
  it('does not display any password in the reset status message (REQ-4027 AK-12)', () => {
    // Nach REQ-4027/4028 duerfe keine Passwoerter mehr im Klartext angezeigt werden.
    // Vorher wurde "Passwort: admin123" angezeigt.
    const { container } = render(<SettingsPage />);

    // Kein "admin123" oder "changeme123!" im Text
    expect(container.textContent).not.toMatch(/admin123/);
    expect(container.textContent).not.toMatch(/changeme123!/);
    // Kein generisches "Passwort:" mit Klartext-Wert
    expect(container.textContent).not.toMatch(/Passwort:\s*\S+/i);
  });

  it('cancels the database reset without sending reset request', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Upsi nein/i }));

    expect(screen.queryByRole('dialog', { name: /Datenbank wirklich zuruecksetzen\?/i })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith('/api/backup/reset', expect.objectContaining({ method: 'POST' }));
  });
});
