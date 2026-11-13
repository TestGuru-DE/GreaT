// REQ-3045/3046/3047/3049: Generierungen-Seite muss in Kern-Themes lesbar bleiben
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import GenerationsPage from "../GenerationsPage";
import { projectsApi, generateApi } from "../../api/client";

vi.mock("../../api/client", () => ({
  projectsApi: {
    list: vi.fn(),
  },
  generateApi: {
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    deleteGeneration: vi.fn(),
  },
}));

describe("GenerationsPage - Theme-Kontrast in Normal/Dark/Steampunk/Heavy Metal", () => {
  beforeEach(() => {
    vi.mocked(projectsApi.list).mockResolvedValue([
      { id: 1, name: "Projekt A" },
    ] as never);
    vi.mocked(generateApi.listGenerations).mockResolvedValue([
      {
        id: 77,
        name: "Run 77",
        strategy: "pairwise",
        created_at: "2026-01-02T00:00:00Z",
        testcase_count: 42,
      },
    ] as never);
  });

  it.each([
    ["Normal", ""],
    ["Dark", "theme-dark"],
    ["Steampunk", "theme-steampunk"],
    ["Heavy Metal", "theme-heavy-metal"],
  ])("nutzt in Theme %s weisse Texte ausser in Strategie-Spalte", async (_themeName, themeClass) => {
    document.documentElement.className = themeClass;
    render(<GenerationsPage />);

    const heading = await screen.findByRole("heading", { name: "Alle Generierungen" });
    const panel = heading.parentElement as HTMLElement;
    expect(panel).toHaveClass("bg-theme-surface");
    expect(panel).not.toHaveClass("bg-white");
    expect(heading).toHaveClass("text-white");

    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: "Name" })).toHaveClass("text-white");
    expect(within(table).getByRole("columnheader", { name: "Projekt" })).toHaveClass("text-white");
    expect(within(table).getByRole("columnheader", { name: "Strategie" })).toHaveClass("text-black");

    expect(screen.getByText("Projekt A")).toHaveClass("text-white");
    expect(screen.getByText("pairwise")).toHaveClass("text-black");

    const jsonButton = screen.getByRole("button", { name: "JSON" });
    const excelButton = screen.getByRole("button", { name: "Excel" });
    const csvButton = screen.getByRole("button", { name: "CSV" });
    expect(jsonButton).toHaveClass("text-white");
    expect(excelButton).toHaveClass("text-white");
    expect(csvButton).toHaveClass("text-white");

    fireEvent.doubleClick(screen.getByText("Run 77"));
    const nameInput = screen.getByDisplayValue("Run 77");
    expect(nameInput).toHaveClass("text-white");

  });
});
