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

describe("TopNav - REQ-4028 Passwort aendern Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: false,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: vi.fn(),
        changePassword: vi.fn(),
      };
      // @ts-expect-error
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