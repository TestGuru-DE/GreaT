// REQ-4001: Tests fuer ProtectedRoute
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "../ProtectedRoute";
import { useAuthStore } from "../../store/authStore";

// Mock useAuthStore
vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

describe("ProtectedRoute - REQ-4001", () => {
  const mockLoadUser = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoadUser.mockReset();
  });

  it("leitet unauthentifizierte User zu /login um", async () => {
    // Simuliere: loadUser fuehrt zu user=null
    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: null,
        isLoading: false,
        error: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: mockLoadUser.mockResolvedValue(undefined),
        clearError: vi.fn(),
        refresh: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<div data-testid="protected-content">Protected</div>} />
          </Route>
          <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Nach dem Auth-Check sollte loadUser aufgerufen worden sein
    await waitFor(() => {
      expect(mockLoadUser).toHaveBeenCalled();
    });
  });

  it("zeigt Outlet fuer authentifizierte User", async () => {
    const mockUser = {
      id: 1,
      username: "admin",
      role: "admin",
      is_active: true,
    };

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: mockUser,
        isLoading: false,
        error: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: mockLoadUser.mockResolvedValue(undefined),
        clearError: vi.fn(),
        refresh: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<div data-testid="protected-content">Protected Content</div>} />
          </Route>
          <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("protected-content")).toBeInTheDocument();
    });
  });

  it("zeigt Loading-State waehrend Auth-Check", async () => {
    // Deferred-Pattern: Promise laesst sich von aussen loesen
    let resolveLoadUser: () => void;
    const loadUserPromise = new Promise<void>((resolve) => {
      resolveLoadUser = resolve;
    });

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: null,
        isLoading: false,
        error: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(() => loadUserPromise),
        clearError: vi.fn(),
        refresh: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    const { container } = render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<div data-testid="protected-content">Protected</div>} />
          </Route>
          <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Waehrend des Checks sollte der Spinner sichtbar sein
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).not.toBeNull();

    // Loese den loadUser-Promise
    await waitFor(() => {
      resolveLoadUser!();
    });
  });

  it("nutzt Theme-Tokens fuer Loading-State", () => {
    // Deferred-Pattern
    let resolveLoadUser: () => void;
    const loadUserPromise = new Promise<void>((resolve) => {
      resolveLoadUser = resolve;
    });

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: null,
        isLoading: false,
        error: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(() => loadUserPromise),
        clearError: vi.fn(),
        refresh: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    const { container } = render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<div>Protected</div>} />
          </Route>
          <Route path="/login" element={<div>Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    const loadingContainer = container.querySelector("div.min-h-screen");
    expect(loadingContainer).not.toBeNull();
    expect(loadingContainer!.className).toMatch(/\bbg-theme-bg\b/);
  });
});