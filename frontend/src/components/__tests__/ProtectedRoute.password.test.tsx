// REQ-4028 AK-1: Tests fuer Route-Guard mit passwordChangeRequired
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

// Mock useAuthStore
vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

// Mock react-router-dom hooks
const mockNavigate = vi.fn();
const mockLocation: { pathname: string } = { pathname: "/app" };

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...(actual as object),
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
    Outlet: () => <div data-testid="outlet">Protected Content</div>,
  };
});

describe("ProtectedRoute - REQ-4028 passwordChangeRequired Guard", () => {
  const mockLoadUser = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoadUser.mockReset();
    mockNavigate.mockReset();
    mockLocation.pathname = "/app";
  });

  it("leitet bei passwordChangeRequired=true auf /account/password um", async () => {
    mockLoadUser.mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: true,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: mockLoadUser,
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    // Re-import after mock change to get fresh component
    const { default: ProtectedRoute } = await import("../ProtectedRoute");

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <ProtectedRoute />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/account/password");
    });
  });

  it("zeigt Content wenn passwordChangeRequired=false", async () => {
    mockLoadUser.mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: false,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: mockLoadUser,
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    const { default: ProtectedRoute } = await import("../ProtectedRoute");

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <ProtectedRoute />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("outlet")).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalledWith("/account/password");
  });

  it("laeuft /account/password auch bei passwordChangeRequired=true", async () => {
    mockLoadUser.mockResolvedValue(undefined);
    mockLocation.pathname = "/account/password";

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: true,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: mockLoadUser,
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });

    const { default: ProtectedRoute } = await import("../ProtectedRoute");

    render(
      <MemoryRouter initialEntries={["/account/password"]}>
        <ProtectedRoute />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("outlet")).toBeInTheDocument();
    });

    // Should NOT redirect away from /account/password
    expect(mockNavigate).not.toHaveBeenCalledWith("/account/password");
  });
});