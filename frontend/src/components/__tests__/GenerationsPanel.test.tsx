// REQ-3045: Export-Buttons muessen in allen Kern-Themes schwarzen Text behalten
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import GenerationsPanel from "../GenerationsPanel";
import { generateApi } from "../../api/client";

vi.mock("../../api/client", () => ({
  generateApi: {
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    deleteGeneration: vi.fn(),
  },
}));

describe("GenerationsPanel - REQ-3045 Export-Kontrast", () => {
  beforeEach(() => {
    vi.mocked(generateApi.listGenerations).mockResolvedValue([
      {
        id: 11,
        name: "Run 1",
        strategy: "pairwise",
        created_at: "2026-01-01T00:00:00Z",
        testcase_count: 12,
      },
    ] as never);
  });

  it.each([
    ["Normal", ""],
    ["Dark", "theme-dark"],
    ["Heavy Metal", "theme-heavy-metal"],
  ])("zeigt in Theme %s schwarze Export-Button-Texte fuer JSON/Excel/CSV", async (_themeName, themeClass) => {
    document.documentElement.className = themeClass;
    render(<GenerationsPanel projectId={1} />);

    const jsonButton = await screen.findByRole("button", { name: "JSON" });
    const excelButton = screen.getByRole("button", { name: "Excel" });
    const csvButton = screen.getByRole("button", { name: "CSV" });

    expect(jsonButton).toHaveClass("text-black");
    expect(excelButton).toHaveClass("text-black");
    expect(csvButton).toHaveClass("text-black");
  });
});
