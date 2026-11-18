// REQ-6013: Tests fuer ModelExportDropdown
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import ModelExportDropdown from "../ModelExportDropdown";
import * as modelApi from "../../api/modelApi";

// Mock the API
vi.mock("../../api/modelApi", () => ({
  exportModel: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../Toast", () => ({
  useToastStore: {
    getState: vi.fn(() => ({
      add: vi.fn(),
    })),
  },
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <I18nextProvider i18n={i18n}>
    <MemoryRouter>{children}</MemoryRouter>
  </I18nextProvider>
);

describe("REQ-6013: ModelExportDropdown", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(modelApi.exportModel).mockResolvedValue(undefined);
  });

  it("should render export button", () => {
    render(
      <ModelExportDropdown projectId={1} projectName="TestProject" />,
      { wrapper },
    );

    expect(screen.getByRole("button", { name: /Modell exportieren/i })).toBeInTheDocument();
  });

  it("should open dropdown on click", () => {
    render(
      <ModelExportDropdown projectId={1} projectName="TestProject" />,
      { wrapper },
    );

    const button = screen.getByRole("button", { name: /Modell exportieren/i });
    fireEvent.click(button);

    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  it("should show YAML and JSON options", () => {
    render(
      <ModelExportDropdown projectId={1} projectName="TestProject" />,
      { wrapper },
    );

    const button = screen.getByRole("button", { name: /Modell exportieren/i });
    fireEvent.click(button);

    const menu = screen.getByRole("menu");
    expect(menu).toBeInTheDocument();

    // Check for menu items
    const menuItems = screen.getAllByRole("menuitem");
    expect(menuItems.length).toBe(2);
  });

  it("should call exportModel with yaml format on YAML click", async () => {
    render(
      <ModelExportDropdown projectId={1} projectName="TestProject" />,
      { wrapper },
    );

    const button = screen.getByRole("button", { name: /Modell exportieren/i });
    fireEvent.click(button);

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[0]); // YAML option

    expect(modelApi.exportModel).toHaveBeenCalledWith(1, "yaml", "TestProject");
  });

  it("should call exportModel with json format on JSON click", async () => {
    render(
      <ModelExportDropdown projectId={1} projectName="TestProject" />,
      { wrapper },
    );

    const button = screen.getByRole("button", { name: /Modell exportieren/i });
    fireEvent.click(button);

    const menuItems = screen.getAllByRole("menuitem");
    fireEvent.click(menuItems[1]); // JSON option

    expect(modelApi.exportModel).toHaveBeenCalledWith(1, "json", "TestProject");
  });
});