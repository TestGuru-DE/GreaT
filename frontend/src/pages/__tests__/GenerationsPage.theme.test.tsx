// REQ-3045/3046/3047/3049: Generierungen-Seite muss in Kern-Themes lesbar bleiben
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import GenerationsPage from "../GenerationsPage";
import { projectsApi, generateApi } from "../../api/client";

// REQ-6005: i18n mock for GenerationsPage theme tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "generations.title": "Alle Generierungen",
        "generations.loading": "Lade Generierungen...",
        "generations.empty": "Noch keine Generierungen vorhanden.",
        "generations.deleteConfirm": "Generierung löschen?",
        "generations.renameTitle": "Doppelklick zum Umbenennen",
        "generations.columns.name": "Name",
        "generations.columns.project": "Projekt",
        "generations.columns.strategy": "Strategie",
        "generations.columns.testcases": "Testfälle",
        "generations.columns.date": "Datum",
        "generations.columns.actions": "Aktionen",
        "generations.actions.edit": "✏️",
        "generations.actions.json": "JSON",
        "generations.actions.excel": "Excel",
        "generations.actions.csv": "CSV",
        "generations.actions.delete": "🗑️",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock("../../api/client", () => ({
  projectsApi: {
    list: vi.fn(),
  },
  generateApi: {
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    deleteGeneration: vi.fn(),
  },
  valuesApi: {
    list: vi.fn(),
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
  ])("nutzt in Theme %s theme-tokens fuer Textfarben", async (_themeName, themeClass) => {
    document.documentElement.className = themeClass;
    render(<GenerationsPage />);

    const heading = await screen.findByRole("heading", { name: "Alle Generierungen" });
    const panel = heading.parentElement as HTMLElement;
    expect(panel).toHaveClass("bg-theme-surface");
    expect(panel).not.toHaveClass("bg-white");
    // Component uses text-theme-text for all text
    expect(heading).toHaveClass("text-theme-text");

    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: "Name" })).toHaveClass("text-theme-text");
    expect(within(table).getByRole("columnheader", { name: "Projekt" })).toHaveClass("text-theme-text");
    expect(within(table).getByRole("columnheader", { name: "Strategie" })).toHaveClass("text-theme-text");

    expect(screen.getByText("Projekt A")).toHaveClass("text-theme-text");
    expect(screen.getByText("pairwise")).toHaveClass("text-theme-text");

    const jsonButton = screen.getByRole("button", { name: "JSON" });
    const excelButton = screen.getByRole("button", { name: "Excel" });
    const csvButton = screen.getByRole("button", { name: "CSV" });
    expect(jsonButton).toHaveClass("text-theme-text");
    expect(excelButton).toHaveClass("text-theme-text");
    expect(csvButton).toHaveClass("text-theme-text");

    fireEvent.doubleClick(screen.getByText("Run 77"));
    const nameInput = screen.getByDisplayValue("Run 77");
    expect(nameInput).toHaveClass("text-theme-text");

  });
});