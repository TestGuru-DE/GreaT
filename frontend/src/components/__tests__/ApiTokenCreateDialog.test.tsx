// REQ-6012: API-Token-Verwaltung – ApiTokenCreateDialog Tests

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ApiTokenCreateDialog from "../ApiTokenCreateDialog";

// REQ-6005: i18n mock
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "settings.apiTokens.createTitle": "Neues API-Token erstellen",
        "settings.apiTokens.name": "Name",
        "settings.apiTokens.namePlaceholder": "z.B. Jenkins Nightly",
        "settings.apiTokens.nameRequired": "Bitte einen Namen eingeben.",
        "settings.apiTokens.expiresAt": "Ablaufdatum",
        "settings.apiTokens.expiresAtHint": "Maximal 365 Tage, Vorschlag: 90 Tage",
        "settings.apiTokens.scopes": "Bereiche (Scopes)",
        "settings.apiTokens.scopeDescriptions.projects:read": "Projekte lesen",
        "settings.apiTokens.scopeDescriptions.projects:write": "Projekte bearbeiten",
        "settings.apiTokens.scopeDescriptions.generate": "Testfälle generieren",
        "settings.apiTokens.scopeDescriptions.export": "Exportieren",
        "settings.apiTokens.scopeDescriptions.models:read": "Modelle lesen",
        "settings.apiTokens.scopeDescriptions.models:write": "Modelle bearbeiten",
        "settings.apiTokens.createButton": "Neues Token erstellen",
        "settings.apiTokens.warning": "Dieser Token wird nicht mehr angezeigt. Speichere ihn sicher.",
        "settings.apiTokens.copyButton": "Kopieren",
        "settings.apiTokens.understood": "Verstanden",
        "common.cancel": "Abbrechen",
        "common.loading": "Wird geladen...",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

// BUG A-01: Dialog nutzt Auth-Store und Benutzer-API (Besitzer-Auswahl fuer Admins)
vi.mock("../../store/authStore", () => ({
  useAuthStore: (selector: (s: unknown) => unknown) => selector({ user: { role: "editor" } }),
}));
vi.mock("../../api/usersApi", () => ({ usersApi: { list: vi.fn().mockResolvedValue([]) } }));

// Mock apiTokensApi
vi.mock("../../api/apiTokensApi", () => ({
  listTokens: vi.fn(),
  revokeToken: vi.fn(),
  createToken: vi.fn(),
}));

import { createToken } from "../../api/apiTokensApi";

describe("ApiTokenCreateDialog - REQ-6012", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("zeigt nichts, wenn open=false", () => {
    const { container } = render(
      <ApiTokenCreateDialog open={false} onClose={() => {}} onCreated={() => {}} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("zeigt Dialog mit Formular, wenn open=true", () => {
    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );
    expect(screen.getByText("Neues API-Token erstellen")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/z.B. Jenkins/i)).toBeInTheDocument();
  });

  it("zeigt Scope-Checkboxen", () => {
    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );
    expect(screen.getByText("projects:read")).toBeInTheDocument();
    expect(screen.getByText("projects:write")).toBeInTheDocument();
    expect(screen.getByText("generate")).toBeInTheDocument();
  });

  it("zeigt Fehler bei leerem Namen", async () => {
    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );
    const createBtn = screen.getByText("Neues Token erstellen");
    fireEvent.click(createBtn);
    expect(screen.getByText("Bitte einen Namen eingeben.")).toBeInTheDocument();
  });

  it("ruft createToken auf bei gueltigem Formular", async () => {
    (createToken as any).mockResolvedValue({
      token: "great_pat_testtoken123",
      id: 99,
      name: "Test",
      prefix: "great_pat_test",
      scopes: ["projects:read"],
      expires_at: "2026-04-01",
    });

    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );

    const nameInput = screen.getByPlaceholderText(/z.B. Jenkins/i);
    fireEvent.change(nameInput, { target: { value: "Jenkins Nightly" } });

    const createBtn = screen.getByText("Neues Token erstellen");
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(createToken).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Jenkins Nightly",
          scopes: expect.arrayContaining(["projects:read"]),
          // BUG A-04: Backend erwartet expires_in_days (Vorschlag 90 Tage)
          expires_in_days: 90,
        })
      );
    });
  });

  it("zeigt Token nach erfolgreicher Erzeugung", async () => {
    (createToken as any).mockResolvedValue({
      token: "great_pat_secrettoken456",
      id: 100,
      name: "Test",
      prefix: "great_pat_sec",
      scopes: ["projects:read"],
      expires_at: "2026-04-01",
    });

    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );

    const nameInput = screen.getByPlaceholderText(/z.B. Jenkins/i);
    fireEvent.change(nameInput, { target: { value: "TestToken" } });

    const createBtn = screen.getByText("Neues Token erstellen");
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(screen.getByText("great_pat_secrettoken456")).toBeInTheDocument();
    });

    // Warnhinweis sollte sichtbar sein
    expect(screen.getByText(/Dieser Token wird nicht mehr angezeigt/i)).toBeInTheDocument();
  });

  it("zeigt Kopier-Button nach Erzeugung", async () => {
    (createToken as any).mockResolvedValue({
      token: "great_pat_copytest789",
      id: 101,
      name: "Test",
      prefix: "great_pat_copy",
      scopes: ["export"],
      expires_at: "2026-04-01",
    });

    // Mock clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    render(
      <ApiTokenCreateDialog open={true} onClose={() => {}} onCreated={() => {}} />
    );

    const nameInput = screen.getByPlaceholderText(/z.B. Jenkins/i);
    fireEvent.change(nameInput, { target: { value: "CopyTest" } });

    const createBtn = screen.getByText("Neues Token erstellen");
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(screen.getByText("Kopieren")).toBeInTheDocument();
    });
  });

  it("ruft onClose und onCreated auf bei 'Verstanden'", async () => {
    const onCloseMock = vi.fn();
    const onCreatedMock = vi.fn();

    (createToken as any).mockResolvedValue({
      token: "great_pat_done123",
      id: 102,
      name: "Done",
      prefix: "great_pat_done",
      scopes: ["generate"],
      expires_at: "2026-04-01",
    });

    render(
      <ApiTokenCreateDialog open={true} onClose={onCloseMock} onCreated={onCreatedMock} />
    );

    const nameInput = screen.getByPlaceholderText(/z.B. Jenkins/i);
    fireEvent.change(nameInput, { target: { value: "DoneToken" } });

    const createBtn = screen.getByText("Neues Token erstellen");
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(screen.getByText("Verstanden")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Verstanden"));

    expect(onCreatedMock).toHaveBeenCalled();
    expect(onCloseMock).toHaveBeenCalled();
  });
});