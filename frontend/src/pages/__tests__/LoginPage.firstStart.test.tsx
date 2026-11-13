// REQ-4027: Tests fuer Erststart-Hinweis auf LoginPage
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "../LoginPage";
import { useAuthStore } from "../../store/authStore";
import * as authApi from "../../api/authApi";

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

// Mock fetch for getFirstStartHint
beforeEach(() => {
  vi.restoreAllMocks();
});

describe("LoginPage - REQ-4027 Erststart-Hinweis", () => {
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
        passwordChangeRequired: false,
        login: mockLogin,
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });
  });

  it("zeigt Erststart-Hinweis bei show_hint: true (AK-2)", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ show_hint: true }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Standardbenutzer: admin")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(
        screen.getByText("Standardpasswort: changeme123! (bitte nach der ersten Anmeldung aendern)")
      ).toBeInTheDocument();
    });
  });

  it("zeigt KEINEN Hinweis bei show_hint: false (AK-3)", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ show_hint: false }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByText("Standardbenutzer: admin")).not.toBeInTheDocument();
      expect(screen.queryByText("Standardpasswort:")).not.toBeInTheDocument();
    });
  });

  it("zeigt KEINEN Hinweis bei Fehler/429 (AK-8)", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve({ detail: "too_many_requests" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByText("Standardbenutzer: admin")).not.toBeInTheDocument();
    });
  });

  it("Login-Formular bleibt bei Fehler voll nutzbar (AK-8)", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "internal_error" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Username und Passwort Felder sind immer sichtbar
    expect(screen.getByLabelText("Benutzername")).toBeInTheDocument();
    expect(screen.getByLabelText("Passwort")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Anmelden/ })).toBeInTheDocument();
  });

  it("Hinweis-Texte stehen unter den richtigen Feldern (AK-2)", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ show_hint: true }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Der "Standardbenutzer"-Text sollte im selben Container wie das Username-Feld sein
      const usernameInput = screen.getByLabelText("Benutzername");
      const usernameContainer = usernameInput.closest("div");
      expect(usernameContainer).not.toBeNull();
      expect(usernameContainer!.textContent).toContain("Standardbenutzer: admin");
    });

    await waitFor(() => {
      // Der "Standardpasswort"-Text sollte im selben Container wie das Passwort-Feld sein
      const passwordInput = screen.getByLabelText("Passwort");
      const passwordContainer = passwordInput.closest("div");
      expect(passwordContainer).not.toBeNull();
      expect(passwordContainer!.textContent).toContain("Standardpasswort: changeme123!");
    });
  });
});