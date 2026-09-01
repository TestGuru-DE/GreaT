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
});
