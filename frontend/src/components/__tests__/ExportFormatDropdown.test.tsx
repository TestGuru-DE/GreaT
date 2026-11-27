// REQ-6011: Tests für ExportFormatDropdown
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ExportFormatDropdown from "../ExportFormatDropdown";
import { generateApi } from "../../api/client";

// Mock the API
vi.mock("../../api/client", () => ({
  generateApi: {
    exportGeneration: vi.fn(),
  },
}));

// Mock URL.createObjectURL / revokeObjectURL for JSDOM
const mockCreateObjectURL = vi.fn(() => "http://mock.blob/url");
const mockRevokeObjectURL = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  mockCreateObjectURL.mockClear();
  mockRevokeObjectURL.mockClear();

  // @ts-expect-error JSDOM URL mock
  URL.createObjectURL = mockCreateObjectURL;
  // @ts-expect-error JSDOM URL mock
  URL.revokeObjectURL = mockRevokeObjectURL;

  vi.mocked(generateApi.exportGeneration).mockResolvedValue(
    new Blob(['test content'], { type: 'application/octet-stream' }) as never
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ExportFormatDropdown - REQ-6011", () => {
  it("zeigt Export-Button mit aria-expanded=false initially", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveAttribute("aria-haspopup", "menu");
  });

  it("öffnet Dropdown bei Klick", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    expect(() => screen.getByRole("menu")).toThrow();

    fireEvent.click(button);

    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("schließt Dropdown bei zweitem Klick auf Button", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.click(button);
    expect(() => screen.getByRole("menu")).toThrow();
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("zeigt alle 3 Gruppen-Header", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);

    // Group headers are rendered as divs with text content
    const menu = screen.getByRole("menu");
    expect(menu.textContent).toContain("export.menu.groupAutomation");
    expect(menu.textContent).toContain("export.menu.groupTestManagement");
    expect(menu.textContent).toContain("export.menu.groupDocumentation");
  });

  it("hat 12 menuitem-Einträge (5 automation + 3 testmgmt + 4 docs)", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);

    const menuItems = screen.getAllByRole("menuitem");
    expect(menuItems).toHaveLength(12);
  });

  it("schließt Dropdown bei Klick außerhalb", () => {
    render(
      <div>
        <button id="outside">Outside</button>
        <ExportFormatDropdown generationId={1} generationName="Test Gen" />
      </div>
    );

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.mouseDown(document.getElementById("outside")!);
    expect(() => screen.getByRole("menu")).toThrow();
  });

  it("schließt Dropdown bei Escape-Taste", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
    expect(() => screen.getByRole("menu")).toThrow();
  });

  it("öffnet Dropdown bei ArrowDown auf Button", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.keyDown(button, { key: "ArrowDown" });

    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  it("navigiert durch Menü mit Pfeiltasten", () => {
    render(<ExportFormatDropdown generationId={1} generationName="Test Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);

    const menu = screen.getByRole("menu");
    fireEvent.keyDown(menu, { key: "ArrowDown" });

    // After ArrowDown, the second item (index 1) gets the visual focus highlight
    // because index 0 was set on open. ArrowDown moves to index 1.
    const menuItems = screen.getAllByRole("menuitem");
    // The focused item has tabindex="0" and the sky-50 background
    const focusedItem = menuItems.find((item) => item.getAttribute("tabindex") === "0");
    expect(focusedItem).toBeInTheDocument();
    expect(focusedItem).toHaveClass("bg-theme-accent-soft");
  });

  it("führt Export bei Enter auf fokussiertem Item aus", async () => {
    render(<ExportFormatDropdown generationId={42} generationName="MyGen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);

    const menu = screen.getByRole("menu");
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    fireEvent.keyDown(menu, { key: "Enter" });

    await waitFor(() => {
      expect(generateApi.exportGeneration).toHaveBeenCalled();
    });
  });

  it("führt Export bei Klick auf MenuItem aus", async () => {
    render(<ExportFormatDropdown generationId={42} generationName="MyGen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[0]);

    await waitFor(() => {
      expect(generateApi.exportGeneration).toHaveBeenCalledWith(
        42,
        "gherkin",
        "en"
      );
    });
  });

  it("schließt Dropdown nach Export", async () => {
    render(<ExportFormatDropdown generationId={42} generationName="Gen" />);

    const button = screen.getByRole("button", { name: "export.menu.buttonTitle" });
    fireEvent.click(button);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[0]);

    await waitFor(() => {
      expect(() => screen.getByRole("menu")).toThrow();
    });
  });
});