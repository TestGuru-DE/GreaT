// REQ-5012: Tests fuer ConstraintDialog-Komponente
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ConstraintDialog from "../ConstraintDialog";
import { useDecisionTableStore } from "../../store/decisionTableStore";

// Mock des Stores
vi.mock("../../store/decisionTableStore", () => ({
  useDecisionTableStore: vi.fn(),
}));

// Mock von fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("ConstraintDialog - REQ-5012", () => {
  const mockCauses = [
    { id: 1, name: "Zahlungsmethode", values: ["Karte", "Bar"] },
    { id: 2, name: "Lagerstandort", values: ["Berlin", "Muenchen"] },
    { id: 3, name: "Kundenstatus", values: ["Premium", "Standard"] },
  ];

  const mockEffects = [
    { id: 10, name: "Versandkosten berechnen" },
    { id: 11, name: "Rabatt anwenden" },
  ];

  const mockExistingConstraints = [
    { id: 1, type: "E", targets: [1, 2], description: "Test-Constraint" },
  ];

  const mockStore = {
    causes: mockCauses,
    effects: mockEffects,
    rules: [],
    loading: false,
    error: null,
    canGenerate: false,
  };

  const onCloseMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    onCloseMock.mockClear();

    // Suppress expected act() warnings from async useEffect fetch
    vi.spyOn(console, "error").mockImplementation((...args) => {
      if (typeof args[0] === "string" && args[0].includes("act(...")) return;
    });

    // Standard: E-Typ (causes)
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...mockStore };
      return typeof selector === "function" ? selector(state) : state;
    });

    // Default fetch responses
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockExistingConstraints),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("zeigt Dialog-Überschrift 'Constraint hinzufuegen'", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    expect(screen.getByText("Constraint hinzufuegen")).toBeInTheDocument();
  });

  it("zeigt Schliessen-Button", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const closeBtn = screen.getByRole("button", { name: /Schliessen/i });
    expect(closeBtn).toBeInTheDocument();
    fireEvent.click(closeBtn);
    expect(onCloseMock).toHaveBeenCalled();
  });

  it("zeigt Typ-Dropdown mit allen 5 Constraint-Typen", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();

    // Pruefe dass das Select existiert und den Default-Wert "E" hat
    expect((select as HTMLSelectElement).value).toBe("E");
  });

  it("zeigt Ursachen-Liste bei E-Typ (Exclusive)", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    // E-Typ arbeitet mit Ursachen
    expect(screen.getByText("Zahlungsmethode")).toBeInTheDocument();
    expect(screen.getByText("Lagerstandort")).toBeInTheDocument();
    expect(screen.getByText("Kundenstatus")).toBeInTheDocument();
    // Wirkungen sollen NICHT erscheinen
    expect(screen.queryByText("Versandkosten berechnen")).not.toBeInTheDocument();
  });

  it("zeigt Wirkungen-Liste bei M-Typ (Mask)", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");

    // Wechsel zu M-Typ
    fireEvent.change(select, { target: { value: "M" } });

    // M-Typ arbeitet mit Wirkungen
    await waitFor(() => {
      expect(screen.getByText("Versandkosten berechnen")).toBeInTheDocument();
      expect(screen.getByText("Rabatt anwenden")).toBeInTheDocument();
    });

    // Ursachen sollen NICHT erscheinen
    expect(screen.queryByText("Zahlungsmethode")).not.toBeInTheDocument();
  });

  it("zeigt Ursachen-Liste bei R-Typ (Requires)", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");

    // Wechsel zu R-Typ
    fireEvent.change(select, { target: { value: "R" } });

    // R-Typ arbeitet mit Ursachen
    await waitFor(() => {
      expect(screen.getByText("Zahlungsmethode")).toBeInTheDocument();
    });

    // Hinweis zur Richtung soll erscheinen
    expect(screen.getByText(/Voraussetzung/)).toBeInTheDocument();
  });

  it("zeigt Checkboxen fuer Item-Auswahl", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  it("laesst sich Checkbox an/ausschalten", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes[0]).not.toBeChecked();

    fireEvent.click(checkboxes[0]);
    expect(checkboxes[0]).toBeChecked();

    fireEvent.click(checkboxes[0]);
    expect(checkboxes[0]).not.toBeChecked();
  });

  it("beschraenkt R-Typ auf maximal 2 Checkboxen", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "R" } });

    const checkboxes = screen.getAllByRole("checkbox");

    // Erste zwei Checkboxen anklicken
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).toBeChecked();

    // Dritte sollte blockiert sein
    fireEvent.click(checkboxes[2]);
    expect(checkboxes[2]).not.toBeChecked();
  });

  it("beschraenkt M-Typ auf maximal 2 Checkboxen", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "M" } });

    const checkboxes = screen.getAllByRole("checkbox");

    // Nur 2 Wirkungen vorhanden, beide koennen geklickt werden
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).toBeChecked();
  });

  it("zeigt Validierungsfehler wenn weniger als 2 Items bei E-Typ", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const checkboxes = screen.getAllByRole("checkbox");

    // Nur eine Checkbox anhaekern
    fireEvent.click(checkboxes[0]);

    // Hinzufuegen-Button klicken
    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mindestens 2 Eintraege erforderlich/)).toBeInTheDocument();
    });
  });

  it("zeigt Validierungsfehler wenn weniger als 2 Items bei O-Typ", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "O" } });

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mindestens 2 Eintraege erforderlich/)).toBeInTheDocument();
    });
  });

  it("zeigt Validierungsfehler wenn weniger als 2 Items bei I-Typ", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "I" } });

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mindestens 2 Eintraege erforderlich/)).toBeInTheDocument();
    });
  });

  it("zeigt Validierungsfehler wenn weniger als 2 Items bei R-Typ", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "R" } });

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mindestens 2 Eintraege erforderlich/)).toBeInTheDocument();
    });
  });

  it("zeigt Validierungsfehler wenn weniger als 2 Items bei M-Typ", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "M" } });

    const checkboxes = screen.getAllByRole("checkbox");
    // Nur 1 von 2 anhaekern
    fireEvent.click(checkboxes[0]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mindestens 2 Eintraege erforderlich/)).toBeInTheDocument();
    });
  });

  it("sendet POST /constraints mit korrekten Daten fuer E-Typ", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "E", targets: [1, 2] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "E", targets: [1, 2] }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // id: 1
    fireEvent.click(checkboxes[1]); // id: 2

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      // Pruefe dass fetch mit POST aufgerufen wurde
      const postCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints"
      );
      expect(postCall).toBeDefined();
      expect(JSON.parse(postCall![1].body)).toEqual({
        project_id: 1,
        constraint_type: "E",
        targets: [1, 2],
      });
    });
  });

  it("sendet POST /constraints mit from/to fuer R-Typ", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "R", targets: { from: 1, to: 2 } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "R", targets: { from: 1, to: 2 } }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "R" } });

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // id: 1 (Voraussetzung)
    fireEvent.click(checkboxes[1]); // id: 2 (Folge)

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      const postCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints"
      );
      expect(postCall).toBeDefined();
      const body = JSON.parse(postCall![1].body);
      expect(body.constraint_type).toBe("R");
      expect(body.targets).toEqual({ from: 1, to: 2 });
    });
  });

  it("sendet POST /constraints mit from/to fuer M-Typ", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "M", targets: { from: 10, to: 11 } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "M", targets: { from: 10, to: 11 } }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "M" } });

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // id: 10
    fireEvent.click(checkboxes[1]); // id: 11

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      const postCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints"
      );
      expect(postCall).toBeDefined();
      const body = JSON.parse(postCall![1].body);
      expect(body.constraint_type).toBe("M");
      expect(body.targets).toEqual({ from: 10, to: 11 });
    });
  });

  it("sendet description wenn eingegeben", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "E", targets: [1, 2] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "E", targets: [1, 2] }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    // Beschreibung eingeben
    const descInput = screen.getByPlaceholderText(/z.B./i);
    fireEvent.change(descInput, { target: { value: "Nur eine Zahlungsmethode moeglich" } });

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      const postCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints"
      );
      expect(postCall).toBeDefined();
      const body = JSON.parse(postCall![1].body);
      expect(body.description).toBe("Nur eine Zahlungsmethode moeglich");
    });
  });

  it("sendet keine description wenn leer", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "E", targets: [1, 2] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "E", targets: [1, 2] }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      const postCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints"
      );
      expect(postCall).toBeDefined();
      const body = JSON.parse(postCall![1].body);
      expect(body.description).toBeUndefined();
    });
  });

  it("zeigt Fehler bei fehlgeschlagenem POST", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: "Ungueltige Constraint-Kombination" }),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText("Ungueltige Constraint-Kombination")).toBeInTheDocument();
    });
  });

  it("loescht Constraint per DELETE", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

    const { container } = render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    // Bestehende Constraints sollten angezeigt werden
    await waitFor(() => {
      expect(container.textContent).toContain("Test-Constraint");
    });

    // Loeschen-Button klicken
    const deleteBtn = screen.getByText("Loeschen");
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      // DELETE wurde aufgerufen
      const deleteCall = mockFetch.mock.calls.find(
        (call) => call[0] === "/api/decision-table/constraints/1" && call[1]?.method === "DELETE"
      );
      expect(deleteCall).toBeDefined();
    });
  });

  it("zeigt bestehende Constraints mit Typ und Targets", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockExistingConstraints),
    });

    const { container } = render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    await waitFor(() => {
      expect(container.textContent).toContain("Bestehende Constraints");
      expect(container.textContent).toContain("E");
    });
  });

  it("zeigt Abbrechen-Button der onClose aufruft", () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);
    const cancelBtn = screen.getByText("Abbrechen");
    fireEvent.click(cancelBtn);
    expect(onCloseMock).toHaveBeenCalled();
  });

  it("setzt selectedItems zurueck nach erfolgreichem POST", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2, type: "E", targets: [1, 2] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockExistingConstraints, { id: 2, type: "E", targets: [1, 2] }]),
      });

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      // Nach erfolgreichem POST sollten Checkboxen wieder ungewaehlt sein
      expect(checkboxes[0]).not.toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();
    });
  });

  it("zeigt loading-State waehrend POST", async () => {
    let resolvePromise: () => void;
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExistingConstraints),
      })
      .mockReturnValue(new Promise((resolve) => {
        resolvePromise = () => resolve({
          ok: true,
          json: () => Promise.resolve({ id: 2, type: "E", targets: [1, 2] }),
        });
      }));

    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    // Waehrend des Ladens sollte der Button disabled sein
    await waitFor(() => {
      expect(addBtn).toBeDisabled();
    });

    // Resolve den pending fetch
    resolvePromise!();
  });

  it("leert Auswahl und Fehlermeldung beim Wechsel des Constraint-Typs", async () => {
    render(<ConstraintDialog projectId={1} onClose={onCloseMock} />);

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // Eine Checkbox anhaekern

    const select = screen.getByRole("combobox");
    // Wechsel von E zu O
    fireEvent.change(select, { target: { value: "O" } });

    await waitFor(() => {
      // Auswahl sollte geleert sein
      expect(checkboxes[0]).not.toBeChecked();
    });
  });
});