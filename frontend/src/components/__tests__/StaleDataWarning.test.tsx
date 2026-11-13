// REQ-4022: Tests fuer StaleDataWarning-Banner
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StaleDataWarning from "../StaleDataWarning";

describe("StaleDataWarning - REQ-4022", () => {
  const mockOnReload = vi.fn();
  const mockOnOverwrite = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderComponent(props?: Partial<React.ComponentProps<typeof StaleDataWarning>>) {
    return render(
      <StaleDataWarning
        modifiedBy={props?.modifiedBy}
        modifiedAt={props?.modifiedAt}
        onReload={props?.onReload ?? mockOnReload}
        onOverwrite={props?.onOverwrite ?? mockOnOverwrite}
        visible={props?.visible ?? true}
        onClose={props?.onClose ?? mockOnClose}
      />
    );
  }

  it("ist nicht sichtbar wenn visible=false", () => {
    renderComponent({ visible: false });
    expect(screen.queryByText(/Diese Ansicht ist veraltet/i)).not.toBeInTheDocument();
  });

  it("zeigt Warnung wenn visible=true", () => {
    renderComponent({ visible: true });
    expect(screen.getByText(/Diese Ansicht ist veraltet/i)).toBeInTheDocument();
  });

  it("zeigt modifiedBy wenn vorhanden", () => {
    renderComponent({ visible: true, modifiedBy: "Max Mustermann" });
    expect(screen.getByText(/Max Mustermann/i)).toBeInTheDocument();
  });

  it("zeigt generische Nachricht ohne modifiedBy", () => {
    renderComponent({ visible: true, modifiedBy: undefined });
    expect(screen.getByText(/anderen Person/i)).toBeInTheDocument();
  });

  it("zeigt modifiedAt wenn vorhanden", () => {
    renderComponent({ visible: true, modifiedAt: "12.10.2025 14:30" });
    expect(screen.getByText(/12\.10\.2025 14:30/)).toBeInTheDocument();
  });

  it('"Neu laden" Button triggert onReload Callback', () => {
    renderComponent({ visible: true });
    const reloadBtn = screen.getByRole("button", { name: /Neu laden/i });
    fireEvent.click(reloadBtn);
    expect(mockOnReload).toHaveBeenCalledTimes(1);
    expect(mockOnOverwrite).not.toHaveBeenCalled();
  });

  it('"Trotzdem ueberschreiben" zeigt Bestaetigungsdialog', () => {
    renderComponent({ visible: true });
    const overwriteBtn = screen.getByRole("button", { name: /Trotzdem ueberschreiben/i });
    fireEvent.click(overwriteBtn);
    // Bestaetigungsdialog erscheint
    expect(screen.getByText(/Ueberschreiben bestaetigen/i)).toBeInTheDocument();
    expect(mockOnOverwrite).not.toHaveBeenCalled(); // noch nicht ausgefuehrt
  });

  it('Bestaetigungsdialog "Abbrechen" schliesst Dialog', () => {
    renderComponent({ visible: true });
    // Oeffne den Bestaetigungsdialog
    const overwriteBtn = screen.getByRole("button", { name: /Trotzdem ueberschreiben/i });
    fireEvent.click(overwriteBtn);
    expect(screen.getByText(/Ueberschreiben bestaetigen/i)).toBeInTheDocument();

    // Klicke Abbrechen
    const cancelBtn = screen.getByRole("button", { name: /Abbrechen/i });
    fireEvent.click(cancelBtn);

    // Dialog sollte geschlossen sein
    expect(screen.queryByText(/Ueberschreiben bestaetigen/i)).not.toBeInTheDocument();
    expect(mockOnOverwrite).not.toHaveBeenCalled();
  });

  it('Bestaetigungsdialog "Trotzdem ueberschreiben" triggert onOverwrite', () => {
    renderComponent({ visible: true });
    // Oeffne den Bestaetigungsdialog
    const overwriteBtn = screen.getByRole("button", { name: /Trotzdem ueberschreiben/i });
    fireEvent.click(overwriteBtn);

    // Bestaetige im Dialog
    const confirmBtns = screen.getAllByRole("button", { name: /Trotzdem ueberschreiben/i });
    // Der zweite Button ist der im Dialog (erster ist der im Banner)
    const confirmBtn = confirmBtns[confirmBtns.length - 1];
    fireEvent.click(confirmBtn);

    expect(mockOnOverwrite).toHaveBeenCalledTimes(1);
    // Dialog sollte geschlossen sein
    expect(screen.queryByText(/Ueberschreiben bestaetigen/i)).not.toBeInTheDocument();
  });

  it("Close-Button schliesst Banner", () => {
    renderComponent({ visible: true });
    const closeBtn = screen.getByRole("button", { name: /Schliessen/i });
    fireEvent.click(closeBtn);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", () => {
    const { container } = renderComponent({ visible: true });
    // Das Banner sollte theme-tokens verwenden (bg-theme-bg + border-theme-warning)
    const bannerEl = container.querySelector(".bg-theme-bg");
    expect(bannerEl).not.toBeNull();
    const borderEl = container.querySelector(".border-theme-warning");
    expect(borderEl).not.toBeNull();
  });
});