// REQ-3045 (Sofort-Fix): ProjectsPage ist die Startseite der App und muss dem
// aktiven Theme folgen. Vor dem Fix verwendete die Seite hartkodierte
// "bg-slate-50 dark:bg-slate-900" / "bg-white dark:bg-slate-800" / "text-slate-800"
// Klassen. Das Theme-System setzt aber die Klasse "theme-dark" (nicht "dark") auf
// <html>, wodurch Tailwinds "dark:"-Variante NIE greift (siehe TopNav.tsx-Kommentar).
// Ergebnis: Diese zentrale Seite blieb IMMER hell/weiss/schwarz, unabhaengig vom
// gewaehlten Theme - Kernursache der Nutzerbeschwerde.
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import ProjectsPage from "../ProjectsPage";
import { useProjectStore } from "../../store/projectStore";

vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
}));

vi.mock("../../store/projectStore", () => ({
  useProjectStore: vi.fn(),
}));

vi.mock("../../api/client", () => ({
  generateApi: { listGenerations: vi.fn().mockResolvedValue([]) },
}));

describe("ProjectsPage - REQ-3045 Theme-Tokens statt hartkodierter Light-Farben", () => {
  beforeEach(() => {
    vi.mocked(useProjectStore).mockReturnValue({
      projects: [],
      loading: false,
      error: null,
      fetchProjects: vi.fn(),
      createProject: vi.fn(),
      deleteProject: vi.fn(),
      bulkDelete: vi.fn(),
      bulkDeleteForce: vi.fn(),
    } as unknown as ReturnType<typeof useProjectStore>);
  });

  it("Root-Container nutzt bg-theme-bg statt hartkodiertem bg-slate-50", () => {
    const { container } = render(<ProjectsPage />);
    const root = container.firstChild as HTMLElement;
    expect(root.className).not.toMatch(/\bbg-slate-50\b/);
    expect(root.className).toMatch(/\bbg-theme-bg\b/);
  });

  // Redesign (PO-Vorgabe 27.11.2026): grosser Seitentitel wie im Designbeispiel ersetzt B-33
  it("zeigt den Seitentitel als h1 mit Theme-Text-Token", () => {
    const { container } = render(<ProjectsPage />);
    const heading = container.querySelector("h1");
    expect(heading).not.toBeNull();
    expect(heading!.className).toMatch(/\bpage-title\b/);
    expect(heading!.className).toMatch(/\btext-theme-text\b/);
  });

  it("Karten-Container (Projekte-Panel) nutzt Theme-Surface-Token statt bg-white", () => {
    const { container } = render(<ProjectsPage />);
    const panel = container.querySelector("main > div.card");
    expect(panel).not.toBeNull();
    expect(panel!.className).not.toMatch(/\bbg-white\b/);
    expect(panel!.className).toMatch(/\bbg-theme-surface\b/);
  });
});
