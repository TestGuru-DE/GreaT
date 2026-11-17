/** B-32: Navigation nur nach Login sichtbar */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";

// Mock matchMedia for theme system
beforeEach(() => {
  vi.spyOn(window, "matchMedia").mockReturnValue({
    matches: false,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  } as unknown as MediaQueryList);
});

vi.mock("../lib/theme", () => ({
  setupSystemThemeSync: vi.fn(() => vi.fn()),
}));

describe("App Navigation Visibility", () => {
  it("does not show navigation on /login", () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );
    // TopNav contains "Projekte" NavLink - should NOT be visible on /login
    expect(screen.queryByText('Projekte')).not.toBeInTheDocument();
  });
});