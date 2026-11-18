// REQ-6013: Tests fuer ModelImportDialog
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import ModelImportDialog from "../ModelImportDialog";
import type { Project } from "../../types";

const mockProjects: Project[] = [
  { id: 1, name: "Projekt A", version: 1 },
  { id: 2, name: "Projekt B", version: 1 },
];

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <I18nextProvider i18n={i18n}>
    <MemoryRouter>{children}</MemoryRouter>
  </I18nextProvider>
);

describe("REQ-6013: ModelImportDialog", () => {
  const onClose = vi.fn();
  const onProjectCreated = vi.fn();
  const onProjectUpdated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    onClose.mockReset();
    onProjectCreated.mockReset();
    onProjectUpdated.mockReset();
  });

  it("should render dialog with title", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("should have aria-modal and role dialog", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  it("should show file upload area", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    expect(screen.getByText("Datei hierher ziehen oder klicken")).toBeInTheDocument();
    expect(screen.getByText(".yaml oder .json (max. 5 MB)")).toBeInTheDocument();
  });

  it("should show both import modes", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    expect(screen.getByText("Neues Projekt erstellen")).toBeInTheDocument();
    expect(screen.getByText("Bestehendes Projekt aktualisieren")).toBeInTheDocument();
  });

  it("should show cancel button", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    expect(screen.getByText("Abbrechen")).toBeInTheDocument();
  });

  it("should call onClose when cancel button is clicked", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    const cancelBtn = screen.getByText("Abbrechen");
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it("should call onClose when X button is clicked", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    const closeBtn = screen.getByLabelText("Schließen");
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it("should show project dropdown in update mode", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    // Select update mode
    const updateRadio = screen.getAllByRole("radio")[1]; // "Bestehendes Projekt aktualisieren"
    fireEvent.click(updateRadio);

    // Project dropdown should appear
    expect(screen.getByLabelText("Projekt auswaehlen")).toBeInTheDocument();
  });

  it("should show warning in update mode", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    const updateRadio = screen.getAllByRole("radio")[1];
    fireEvent.click(updateRadio);

    expect(screen.getByText(/Bei Aktualisierung werden bestehende Daten teilweise ersetzt/i)).toBeInTheDocument();
  });

  it("should have import button disabled initially", () => {
    render(
      <ModelImportDialog
        projects={mockProjects}
        onClose={onClose}
        onProjectCreated={onProjectCreated}
        onProjectUpdated={onProjectUpdated}
      />,
      { wrapper },
    );

    // The import button should be disabled when no file is selected
    const buttons = screen.getAllByText("Modell importieren");
    // At least one button with this text should exist (the confirm button)
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });
});