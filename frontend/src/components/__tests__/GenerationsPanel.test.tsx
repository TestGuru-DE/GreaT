// REQ-3009: GenerationsPanel rendering
// REQ-6005: i18n
// REQ-6011: Export-Menü-Dropdown
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import GenerationsPanel from "../GenerationsPanel";
import { generateApi } from "../../api/client";

vi.mock("../../api/client", () => ({
  generateApi: {
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    deleteGeneration: vi.fn(),
    exportGeneration: vi.fn(),
  },
}));

describe("GenerationsPanel - REQ-3009 / REQ-6011", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(generateApi.listGenerations).mockResolvedValue([
      {
        id: 11,
        name: "Run 1",
        strategy: "pairwise",
        created_at: "2026-01-01T00:00:00Z",
        testcase_count: 12,
      },
    ] as never);
    vi.mocked(generateApi.exportGeneration).mockResolvedValue(
      new Blob(['test content'], { type: 'application/octet-stream' }) as never
    );
  });

  it("zeigt Export-Button mit Dropdown-Pfeil", async () => {
    render(<GenerationsPanel projectId={1} />);

    const exportButton = await screen.findByRole("button", {
      name: "export.menu.buttonTitle",
    });
    expect(exportButton).toBeInTheDocument();
  });

  it("öffnet Dropdown bei Klick auf Export-Button", async () => {
    render(<GenerationsPanel projectId={1} />);

    const exportButton = await screen.findByRole("button", {
      name: "export.menu.buttonTitle",
    });

    expect(() => screen.getByRole("menu")).toThrow();
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByRole("menu")).toBeInTheDocument();
    });
  });

  it("zeigt gruppierte Format-Einträge im Dropdown", async () => {
    render(<GenerationsPanel projectId={1} />);

    const exportButton = await screen.findByRole("button", {
      name: "export.menu.buttonTitle",
    });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByRole("menu")).toBeInTheDocument();
    });

    // Check for menu items
    const menuItems = screen.getAllByRole("menuitem");
    expect(menuItems.length).toBeGreaterThan(0);
  });

  it("schließt Dropdown nach Auswahl eines Formats", async () => {
    render(<GenerationsPanel projectId={1} />);

    const exportButton = await screen.findByRole("button", {
      name: "export.menu.buttonTitle",
    });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByRole("menu")).toBeInTheDocument();
    });

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[0]);

    await waitFor(() => {
      expect(() => screen.getByRole("menu")).toThrow();
    });
  });

  it("ruft exportGeneration API bei Format-Auswahl auf", async () => {
    render(<GenerationsPanel projectId={1} />);

    const exportButton = await screen.findByRole("button", {
      name: "export.menu.buttonTitle",
    });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByRole("menu")).toBeInTheDocument();
    });

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[0]);

    await waitFor(() => {
      expect(generateApi.exportGeneration).toHaveBeenCalledWith(
        11,
        expect.any(String),
        expect.any(String)
      );
    });
  });
});