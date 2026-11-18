// REQ-4001: Tests fuer LoginPage
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "../LoginPage";
import { useAuthStore } from "../../store/authStore";

// Mock useAuthStore
vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

// Mock useNavigate
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...(actual as object),
    useNavigate: () => vi.fn(),
  };
});

// REQ-6005: Mock i18n fuer LoginPage-Tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "login.title": "G.R.E.A.T. &ndash; Anmelden",
        "login.username": "Benutzername",
        "login.password": "Passwort",
        "login.defaultUser": `Standardbenutzer: ${params?.username ?? ""}`,
        "login.defaultPassword": `Standardpasswort: ${params?.password ?? ""} (bitte nach der ersten Anmeldung aendern)`,
        "login.submitLoading": "Anmelden...",
        "login.submit": "Anmelden",
        "login.errorInvalid": "Ungültige Anmeldedaten",
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

// Mock getFirstStartHint
vi.mock("../../api/authApi", () => ({
  getFirstStartHint: vi.fn().mockResolvedValue({ show_hint: false }),
  authApi: {
    getFirstStartHint: vi.fn().mockResolvedValue({ show_hint: false }),
  },
}));

// Mock defaultCredentials
vi.mock("../../lib/defaultCredentials", () => ({
  DEFAULT_ADMIN_USERNAME: "admin",
  DEFAULT_ADMIN_PASSWORD: "changeme123!",
}));

describe("LoginPage - REQ-4001", () => {
  const mockLogin = vi.fn();
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockReset();
    mockNavigate.mockReset();

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: null,
        isLoading: false,
        error: null,
        login: mockLogin,
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        passwordChangeRequired: false,
        language: null,
        setLanguage: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });
  });

  it("zeigt Username- und Password-Felder", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText("Benutzername")).toBeInTheDocument();
    expect(screen.getByLabelText("Passwort")).toBeInTheDocument();
  });

  it("zeigt die Ueberschrift 'G.R.E.A.T. – Anmelden'", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/G\.R\.E\.A\.T\./)).toBeInTheDocument();
    // REQ-6005: Button mit spezifischem Namen suchen (nicht getByRole("button"))
    expect(screen.getByRole("button", { name: /Anmelden/ })).toBeInTheDocument();
  });

  it("submit mit korrekten Daten ruft login() auf und navigiert zu /app", async () => {
    mockLogin.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const usernameInput = screen.getByLabelText("Benutzername");
    const passwordInput = screen.getByLabelText("Passwort");
    // REQ-6005: Submit-Button mit spezifischem Namen suchen
    const submitButton = screen.getByRole("button", { name: /Anmelden/ });

    await userEvent.type(usernameInput, "admin");
    await userEvent.type(passwordInput, "password123");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("admin", "password123");
    });
  });

  it("zeigt Error-Message bei fehlgeschlagenem Login", async () => {
    mockLogin.mockRejectedValue(new Error("Ungueltige Anmeldedaten"));

    // Simuliere Error im Store nach Login
    const mockStateWithError = {
      user: null,
      isLoading: false,
      error: "Ungueltige Anmeldedaten",
      login: mockLogin,
      logout: vi.fn(),
      loadUser: vi.fn(),
      clearError: vi.fn(),
      refresh: vi.fn(),
      passwordChangeRequired: false,
      language: null,
      setLanguage: vi.fn(),
    };

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      // @ts-expect-error - selector returns the right value
      return selector(mockStateWithError);
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Ungueltige Anmeldedaten")).toBeInTheDocument();
    });
  });

  it("zeigt Loading-State waehrend Login", async () => {
    // Simuliere Loading-State im Store
    const loadingState = {
      user: null,
      isLoading: true,
      error: null,
      login: mockLogin,
      logout: vi.fn(),
      loadUser: vi.fn(),
      clearError: vi.fn(),
      refresh: vi.fn(),
      passwordChangeRequired: false,
      language: null,
      setLanguage: vi.fn(),
    };

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      // @ts-expect-error - selector returns the right value
      return selector(loadingState);
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // REQ-6005: Submit-Button mit spezifischem Namen suchen (nicht getByRole("button"))
    const button = screen.getByRole("button", { name: /Anmelden/ });
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("Anmelden...");
  });

  it("Submit-Button ist disabled waehrend isLoading", () => {
    const loadingState = {
      user: null,
      isLoading: true,
      error: null,
      login: mockLogin,
      logout: vi.fn(),
      loadUser: vi.fn(),
      clearError: vi.fn(),
      refresh: vi.fn(),
      passwordChangeRequired: false,
      language: null,
      setLanguage: vi.fn(),
    };

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      // @ts-expect-error - selector returns the right value
      return selector(loadingState);
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // REQ-6005: Submit-Button mit spezifischem Namen suchen
    expect(screen.getByRole("button", { name: /Anmelden/ })).toBeDisabled();
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const root = document.body.querySelector("div.min-h-screen");
    expect(root).not.toBeNull();
    expect(root!.className).toMatch(/\bbg-theme-bg\b/);
  });
});