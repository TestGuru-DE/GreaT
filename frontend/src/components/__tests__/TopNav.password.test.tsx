// REQ-4028 AK-3: Tests fuer "Passwort aendern" Eintrag in TopNav
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import TopNav from "../TopNav";
import { useAuthStore } from "../../store/authStore";

vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...(actual as object),
    useNavigate: () => vi.fn(),
  };
});

// REQ-6005: Mock i18n fuer TopNav-Tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "nav.home": "Home",
        "nav.projects": "Projekte",
        "nav.dataclasses": "Datenklassen",
        "nav.generations": "Generierungen",
        "nav.settings": "Einstellungen",
        "nav.changePassword": "Passwort aendern",
        "nav.help": "Hilfe (F1)",
        "nav.apiDocs": "API-Docs",
        "nav.logout": "Logout",
        "nav.logoutTitle": `Abmelden (${params?.username ?? "user"})`,
        "language.switcher.de": "DE",
        "language.switcher.en": "EN",
        "language.switcher.label": "Sprache wechseln",
      };
      return translations[key] ?? key;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock("../../i18n", () => ({
  default: { language: "de" },
}));

describe("TopNav - REQ-4028 Passwort aendern Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: false,
        language: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
        setLanguage: vi.fn(),
      };
      // @ts-expect-error -- Teil-State im Mock
      return selector(state);
    });
  });

  it("zeigt 'Passwort aendern' Link in der Navigation", () => {
    render(
      <MemoryRouter>
        <TopNav />
      </MemoryRouter>
    );

    expect(screen.getByText("Passwort aendern")).toBeInTheDocument();
  });

  it("linkt 'Passwort aendern' zu /account/password", () => {
    render(
      <MemoryRouter>
        <TopNav />
      </MemoryRouter>
    );

    const link = screen.getByText("Passwort aendern");
    expect(link).toHaveAttribute("href", "/account/password");
  });
});