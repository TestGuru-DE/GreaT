// REQ-6012: API-Token-Verwaltung – ApiTokensCard Tests

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ApiTokensCard from "../ApiTokensCard";

// REQ-6005: i18n mock
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "settings.apiTokens.title": "API-Tokens",
        "settings.apiTokens.createButton": "Neues Token erstellen",
        "settings.apiTokens.revokeButton": "Widerrufen",
        "settings.apiTokens.revokeConfirm": "Token wirklich unwiderruflich widerrufen?",
        "settings.apiTokens.empty": "Noch keine API-Tokens erstellt.",
        "settings.apiTokens.expires": "Läuft ab:",
        "settings.apiTokens.lastUsed": "Letzter Gebrauch:",
        "common.loading": "Wird geladen...",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

// Mock apiTokensApi
vi.mock("../../api/apiTokensApi", () => ({
  listTokens: vi.fn(),
  revokeToken: vi.fn(),
  createToken: vi.fn(),
}));

// Mock ApiTokenCreateDialog
vi.mock("../ApiTokenCreateDialog", () => ({
  default: function MockApiTokenCreateDialog({ open, onClose }: any) {
    if (!open) return null;
    return (
      <div data-testid="token-create-dialog">
        <span>Neues API-Token erstellen</span>
        <button onClick={onClose}>Schließen</button>
      </div>
    );
  },
}));

import { listTokens, revokeToken } from "../../api/apiTokensApi";

describe("ApiTokensCard - REQ-6012", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true);
  });

  it("zeigt Ladezustand initial", async () => {
    (listTokens as any).mockReturnValue(new Promise(resolve => setTimeout(() => resolve([]), 100)));
    render(<ApiTokensCard />);
    expect(screen.getByText("Wird geladen...")).toBeInTheDocument();
  });

  it("laedt und zeigt Tokens nach API-Antwort", async () => {
    (listTokens as any).mockResolvedValue([
      {
        id: 1,
        name: "Jenkins",
        prefix: "great_pat_1234",
        scopes: ["projects:read", "generate"],
        created_at: "2026-01-01",
        expires_at: "2026-04-01",
        last_used_at: "2026-01-15",
      },
    ]);
    render(<ApiTokensCard />);
    await waitFor(() => {
      expect(screen.getByText("Jenkins")).toBeInTheDocument();
    });
  });

  it("zeigt 'Neues Token erstellen' Button", async () => {
    (listTokens as any).mockResolvedValue([]);
    render(<ApiTokensCard />);
    await waitFor(() => {
      expect(screen.getByText("Neues Token erstellen")).toBeInTheDocument();
    });
  });

  it("zeigt 'Noch keine API-Tokens' bei leerer Liste", async () => {
    (listTokens as any).mockResolvedValue([]);
    render(<ApiTokensCard />);
    await waitFor(() => {
      expect(screen.getByText("Noch keine API-Tokens erstellt.")).toBeInTheDocument();
    });
  });

  it("zeigt 'Widerrufen' Button pro Token", async () => {
    (listTokens as any).mockResolvedValue([
      {
        id: 1,
        name: "TestToken",
        prefix: "great_pat_abcd",
        scopes: ["projects:read"],
        created_at: "2026-01-01",
        expires_at: "2026-04-01",
      },
    ]);
    render(<ApiTokensCard />);
    await waitFor(() => {
      expect(screen.getAllByText("Widerrufen").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("ruft revokeToken auf bei Klick auf Widerruf", async () => {
    (listTokens as any).mockResolvedValue([
      {
        id: 42,
        name: "ToRevoke",
        prefix: "great_pat_xxxx",
        scopes: ["export"],
        created_at: "2026-01-01",
        expires_at: "2026-04-01",
      },
    ]);
    (revokeToken as any).mockResolvedValue(undefined);

    render(<ApiTokensCard />);
    await waitFor(() => {
      expect(screen.getByText("ToRevoke")).toBeInTheDocument();
    });

    const revokeBtn = screen.getAllByText("Widerrufen")[0];
    fireEvent.click(revokeBtn);

    expect(revokeToken).toHaveBeenCalledWith(42);
  });

  it("oeffnet Erstellungs-Dialog bei Klick auf 'Neues Token erstellen'", async () => {
    (listTokens as any).mockResolvedValue([]);
    render(<ApiTokensCard />);

    await waitFor(() => {
      expect(screen.getByText("Neues Token erstellen")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Neues Token erstellen"));
    await waitFor(() => {
      expect(screen.getByTestId("token-create-dialog")).toBeInTheDocument();
    });
  });
});