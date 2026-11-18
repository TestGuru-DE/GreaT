import { describe, it, expect, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { PortSettingsCard } from '../PortSettingsCard';

// REQ-6005: i18n mock for PortSettingsCard tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "portSettings.title": "Port-Einstellung",
        "portSettings.label": "Bevorzugter Port",
        "portSettings.description": "Standard ist <strong>8000</strong>. <strong>5173</strong> bleibt nur die Dev-Option. Nach einer Aenderung muss der Server neu gestartet werden.",
        "portSettings.currentUrl": "Aktuelle lokale URL:",
        "portSettings.save": "Speichern",
        "portSettings.error": "Bitte einen Port zwischen 1 und 65535 eingeben.",
        "portSettings.success": "Port {{port}} gespeichert. Neustart erforderlich.",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

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

