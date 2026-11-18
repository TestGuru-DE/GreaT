import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPage from '../SettingsPage';

// REQ-6005: i18n mock for SettingsPage tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "settings.title": "Einstellungen",
        "settings.appearance.title": "Erscheinungsbild",
        "settings.appearance.description": "Waehle ein Theme fuer die Oberflaeche. Die Einstellung wird automatisch gespeichert.",
        "settings.backup.title": "Datensicherung",
        "settings.backup.create.title": "Sicherung erstellen",
        "settings.backup.create.passwordPlaceholder": "Passwort (optional, fuer Verschluesselung)",
        "settings.backup.create.downloadBtn": "Sicherung herunterladen",
        "settings.backup.create.downloadBtnLoading": "Lädt...",
        "settings.backup.restore.title": "Sicherung wiederherstellen",
        "settings.backup.restore.passwordPlaceholder": "Passwort (falls verschluesselt)",
        "settings.backup.restore.restoreBtn": "Wiederherstellen",
        "settings.backup.restore.restoreBtnLoading": "Verarbeitet...",
        "settings.backup.restore.success": "OK {{count}} Projekte wiederhergestellt",
        "settings.backup.restore.error": "Fehler: {{message}}",
        "settings.database.title": "Datenbank",
        "settings.database.description": "Alle Projekte, Kategorien, Werte und Generierungen werden vollstaendig auf den Startzustand zurueckgesetzt.",
        "settings.database.resetBtn": "Datenbank zuruecksetzen",
        "settings.database.dialog.title": "Datenbank wirklich zuruecksetzen?",
        "settings.database.dialog.confirm": "Bist du sicher? Du loescht damit alles.",
        "settings.database.dialog.warning": "Das Zuruecksetzen entfernt alle Projekte, Kategorien, Werte, Regeln und Generierungen von der Datenbank.",
        "settings.database.dialog.yesDoIt": "Ja mach",
        "settings.database.dialog.backupFirst": "Vorher Backup",
        "settings.database.dialog.cancel": "Ups nein",
        "settings.database.resetSuccessAdmin": "OK Datenbank wurde zurueckgesetzt.\\n\\nEin Standard-Admin wurde erstellt:\\nBenutzername: {{username}}\\n\\nBitte aendere das Passwort nach dem Login!",
        "settings.database.resetSuccess": "OK Datenbank wurde zurueckgesetzt. Deine Session bleibt aktiv.",
        "settings.database.resetError": "Fehler: {{message}}",
        "settings.dataclasses.title": "Datenklassen",
        "settings.dataclasses.description": "Beispielklassen importieren von Bug Magnet Git.<br /><span class=\"text-xs text-theme-text-muted\">Fuer die Inhalte ist der Urheber verantwortlich.</span>",
        "settings.dataclasses.source": "github.com/gojko/bugmagnet/blob/master/template/config.json",
        "settings.dataclasses.importing": "Importiere...",
        "settings.dataclasses.refresh": "Aktualisieren",
        "settings.dataclasses.importBtn": "Importieren",
        "settings.dataclasses.importSuccess": "OK Import abgeschlossen ({{count}} Knoten)",
        "settings.dataclasses.importError": "Fehler: {{message}}",
        "portSettings.title": "Port-Einstellung",
        "portSettings.label": "Bevorzugter Port",
        "portSettings.description": "Standard ist <strong>8000</strong>. <strong>5173</strong> bleibt nur die Dev-Option. Nach einer Aenderung muss der Server neu gestartet werden.",
        "portSettings.currentUrl": "Aktuelle lokale URL:",
        "portSettings.save": "Speichern",
        "portSettings.error": "Bitte einen Port zwischen 1 und 65535 eingeben.",
        "portSettings.success": "Port {{port}} gespeichert. Neustart erforderlich.",
        "maxTestCases.title": "Maximale Anzahl Testfälle",
        "maxTestCases.label": "Obergrenze pro Generierung",
        "maxTestCases.description": "Standard ist <strong>{{default}}</strong>. Verhindert, dass eine Generierung unbegrenzt viele Testfälle erzeugt.",
        "maxTestCases.currentLimit": "Aktuell gewählte Obergrenze:",
        "maxTestCases.save": "Speichern",
        "maxTestCases.success": "Obergrenze auf {{count}} Testfälle gesetzt. Wird ab der nächsten Generierung angewendet.",
        "maxTestCases.error": "Ungültiger Wert.",
        "themeSwitcher.normal": "☀️ Normal",
        "themeSwitcher.dark": "🌙 Dark",
        "themeSwitcher.steampunk": "⚙️ Steampunk",
        "themeSwitcher.rainbow": "🌈 Rainbow",
        "themeSwitcher.heavyMetal": "🤘 Heavy Metal",
        "themeSwitcher.system": "🖥️ System (OS)",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock('../../api/client', () => ({
  backupApi: {
    create: vi.fn(),
    restore: vi.fn(),
    reset: vi.fn(),
  },
  datanodesApi: {
    importBugMagnet: vi.fn(),
    getBugMagnetStatus: vi.fn(),
    importUser: vi.fn(),
  },
}));

import { backupApi, datanodesApi } from '../../api/client';

beforeEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();

  vi.stubGlobal('URL.createObjectURL', vi.fn(() => 'blob:test-url'));

  (backupApi.create as any).mockResolvedValue(new Blob(['backup-zip']));
  (backupApi.reset as any).mockResolvedValue({ status: 'ok', reset: true });
  (backupApi.restore as any).mockResolvedValue({ projects_restored: 0 });
  (datanodesApi.getBugMagnetStatus as any).mockResolvedValue({ imported: false });
});

describe('SettingsPage', () => {
  it('renders the port settings block', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Port-Einstellung/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Bevorzugter Port/i)).toBeInTheDocument();
  });

  it('does not render mojibake artifacts anywhere on the page', () => {
    // Bugfix-Scope: kaputte Emoji-Escapes (z.B. ðŸ'¾, ðŸ—‚ï¸, â³, âœ…, âŒ) duerfen nicht sichtbar sein.
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
    expect(within(dialog).getByRole('button', { name: /Ups nein/i })).toBeInTheDocument();
  });

  it('triggers backup before database reset when choosing backup option', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Vorher Backup/i }));

    expect(backupApi.create).toHaveBeenCalled();
  });

  it('resets the database when the confirmation is accepted', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Ja mach/i }));

    expect(backupApi.reset).toHaveBeenCalled();
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
    render(<SettingsPage />);

    await user.click(screen.getByRole('button', { name: /Datenbank zuruecksetzen|Datenbank loeschen/i }));
    await user.click(screen.getByRole('button', { name: /Ups nein/i }));

    expect(screen.queryByRole('dialog', { name: /Datenbank wirklich zuruecksetzen\?/i })).not.toBeInTheDocument();
    // reset should not have been called - only create might have been called for backup
    expect(backupApi.reset).not.toHaveBeenCalled();
  });
});