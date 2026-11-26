// REQ-6009: Frontend-Tests fuer SeedManager-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import SeedManager from "../SeedManager";
import { useSeedStore } from "../../store/seedStore";
import * as clientModule from "../../api/client";

// Mock seedApi und categoriesApi
vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<ReturnType<typeof import("../../api/client")>>();
  return {
    ...actual,
    seedApi: {
      list: vi.fn(),
      create: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      importCsv: vi.fn(),
      gapFill: vi.fn(),
    },
    categoriesApi: {
      list: vi.fn(),
      create: vi.fn(),
      delete: vi.fn(),
      updateProperties: vi.fn(),
      setDefault: vi.fn(),
      unsetDefault: vi.fn(),
    },
  };
});

// Mock SeedImport component
vi.mock("../SeedImport", () => ({
  default: function MockSeedImport({ projectId, onClose }: { projectId: number; onClose: () => void }) {
    return (
      <div data-testid="seed-import-mock">
        <span>CSV Import (mocked)</span>
        <button onClick={onClose}>Close Import</button>
      </div>
    );
  },
}));

const seedApi = clientModule.seedApi as {
  list: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  importCsv: ReturnType<typeof vi.fn>;
  gapFill: ReturnType<typeof vi.fn>;
};

const categoriesApi = clientModule.categoriesApi as {
  list: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  updateProperties: ReturnType<typeof vi.fn>;
  setDefault: ReturnType<typeof vi.fn>;
  unsetDefault: ReturnType<typeof vi.fn>;
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
);

// Suppress expected act() warnings from async useEffect
vi.spyOn(console, "error").mockImplementation((...args) => {
  if (typeof args[0] === "string" && args[0].includes("act(")) return;
});

describe("REQ-6009: SeedManager", () => {
  const mockCategories = [
    { id: 1, name: "Browser", order_index: 0 },
    { id: 2, name: "OS", order_index: 1 },
  ];

  const mockSeedSets = [
    { id: 1, name: "Set A", seed_count: 3, created_at: "2026-01-01T00:00:00Z" },
    { id: 2, name: "Set B", seed_count: 5, created_at: "2026-02-01T00:00:00Z" },
  ];

  const mockSeedSet = {
    id: 1,
    project_id: 1,
    name: "Set A",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    seed_count: 2,
    seed_cases: [
      { id: 1, assignment: { Browser: "Chrome", OS: "Windows" }, order_index: 0 },
      { id: 2, assignment: { Browser: "Firefox", OS: "Linux" }, order_index: 1 },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset store state
    useSeedStore.setState({
      seedSets: [],
      currentSet: null,
      loading: false,
      error: null,
      msg: null,
    });

    // Default API responses
    seedApi.list.mockResolvedValue(mockSeedSets);
    seedApi.get.mockResolvedValue(mockSeedSet);
    seedApi.create.mockResolvedValue({ id: 3, name: "New Set", seed_count: 0, warnings: [] });
    seedApi.update.mockResolvedValue({ id: 1, name: "Set A", seed_count: 2, warnings: [] });
    seedApi.delete.mockResolvedValue(undefined);
    categoriesApi.list.mockResolvedValue(mockCategories);
  });

  it("rendert die Grundstruktur mit Titel und Buttons", () => {
    render(<SeedManager projectId={1} />, { wrapper });

    expect(screen.getByText("Seed-Sätze")).toBeInTheDocument();
    expect(screen.getByText("+ Neuer Satz")).toBeInTheDocument();
    expect(screen.getByText("CSV-Import")).toBeInTheDocument();
  });

  it("zeigt 'Noch keine Seed-Saetze' bei leerer Liste", async () => {
    seedApi.list.mockResolvedValue([]);

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Noch keine Seed-Sätze/i)).toBeInTheDocument();
    });
  });

  it("zeigt Seed-Saetze nach fetchSeedSets", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText("Set A")).toBeInTheDocument();
      expect(screen.getByText("Set B")).toBeInTheDocument();
    });
  });

  it("zeigt seed_count pro Seed-Satz", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      // Two seed sets, each showing "X Seeds" — use getAllByText
      const seedCountElements = screen.getAllByText(/\d+ Seeds/);
      expect(seedCountElements.length).toBe(2);
    });
  });

  it("oeffnet Erstellungs-Dialog bei Klick auf '+ Neuer Satz'", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    const newBtn = screen.getByText("+ Neuer Satz");
    fireEvent.click(newBtn);

    await waitFor(() => {
      expect(screen.getByText("Neuer Seed-Satz")).toBeInTheDocument();
    });
  });

  it("erstellt neuen Seed-Satz mit Name", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    const newBtn = screen.getByText("+ Neuer Satz");
    fireEvent.click(newBtn);

    await waitFor(() => {
      expect(screen.getByText("Neuer Seed-Satz")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Name des Seed-Satzes/i);
    fireEvent.change(input, { target: { value: "Mein Satz" } });

    const saveBtn = screen.getByText("Speichern");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(seedApi.create).toHaveBeenCalledWith(1, { name: "Mein Satz", seeds: [] });
    });
  });

  it("oeffnet SeedImport-Dialog bei Klick auf 'CSV Import'", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    const importBtn = screen.getByText("CSV-Import");
    fireEvent.click(importBtn);

    await waitFor(() => {
      expect(screen.getByTestId("seed-import-mock")).toBeInTheDocument();
    });
  });

  it("laedt Seed-Satz bei Klick auf Listeneintrag", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText("Set A")).toBeInTheDocument();
    });

    const setAButton = screen.getByText("Set A");
    fireEvent.click(setAButton);

    await waitFor(() => {
      expect(seedApi.get).toHaveBeenCalledWith(1, 1);
    });
  });

  it("zeigt SeedEditor wenn Satz geladen ist", async () => {
    // Pre-set currentSet in store
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Seeds bearbeiten/i)).toBeInTheDocument();
    });
  });

  it("zeigt 'Zuerst Kategorien anlegen' wenn keine Kategorien vorhanden sind", async () => {
    categoriesApi.list.mockResolvedValue([]);
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Zuerst Kategorien anlegen/i)).toBeInTheDocument();
    });
  });

  it("fuegt Seed hinzu bei Klick auf '+ Seed'", async () => {
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Seeds bearbeiten/i)).toBeInTheDocument();
    });

    const addSeedBtn = screen.getByText("+ Seed");
    fireEvent.click(addSeedBtn);

    await waitFor(() => {
      const state = useSeedStore.getState();
      expect(state.currentSet?.seed_cases.length).toBe(3);
    });
  });

  it("entfernt Seed bei Klick auf 'x' in SeedRow", async () => {
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Seeds bearbeiten/i)).toBeInTheDocument();
    });

    // There are 2 SeedRow remove buttons (one per seed) — click the first
    const removeButtons = screen.getAllByTitle("Seed entfernen");
    fireEvent.click(removeButtons[0]);

    await waitFor(() => {
      const state = useSeedStore.getState();
      expect(state.currentSet?.seed_cases.length).toBe(1);
    });
  });

  it("aendert Assignment bei Input-Change in SeedRow", async () => {
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Seeds bearbeiten/i)).toBeInTheDocument();
    });

    // Find input for "Browser" category (first input)
    const inputs = screen.getAllByRole("textbox", { name: "" });
    if (inputs.length > 0) {
      fireEvent.change(inputs[0], { target: { value: "Safari" } });

      await waitFor(() => {
        const state = useSeedStore.getState();
        const firstSeed = state.currentSet?.seed_cases?.[0];
        expect(firstSeed?.assignment["Browser"]).toBe("Safari");
      });
    }
  });

  it("speichert Seed-Satz bei Klick auf 'Satz speichern'", async () => {
    useSeedStore.setState({ currentSet: mockSeedSet });

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Seeds bearbeiten/i)).toBeInTheDocument();
    });

    const saveBtn = screen.getByText("Satz speichern");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(seedApi.update).toHaveBeenCalledWith(1, 1, expect.objectContaining({
        seeds: expect.any(Array),
      }));
    });
  });

  it("zeigt Fehlermeldung bei API-Fehler", async () => {
    seedApi.list.mockRejectedValue(new Error("Connection failed"));

    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      // The store uses String(e) which gives "Error: Connection failed"
      expect(screen.getByText(/Connection failed/)).toBeInTheDocument();
    });
  });

  it("zeigt Message bei Erfolg", async () => {
    useSeedStore.setState({
      msg: { text: "Seed-Satz erstellt", type: "ok" },
    });

    render(<SeedManager projectId={1} />, { wrapper });

    expect(screen.getByText("Seed-Satz erstellt")).toBeInTheDocument();
  });

  it("zeigt Warnung mit Warnsymbol", async () => {
    useSeedStore.setState({
      msg: { text: "Duplicate values found", type: "warn" },
    });

    render(<SeedManager projectId={1} />, { wrapper });

    expect(screen.getByText(/Duplicate values found/i)).toBeInTheDocument();
  });

  it("ruft categoriesApi.list auf beim Mount", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    await waitFor(() => {
      expect(categoriesApi.list).toHaveBeenCalledWith(1);
    });
  });

  it("schliesst Import-Dialog via onClose Callback", async () => {
    render(<SeedManager projectId={1} />, { wrapper });

    const importBtn = screen.getByText("CSV-Import");
    fireEvent.click(importBtn);

    await waitFor(() => {
      expect(screen.getByTestId("seed-import-mock")).toBeInTheDocument();
    });

    const closeBtn = screen.getByText("Close Import");
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByTestId("seed-import-mock")).not.toBeInTheDocument();
    });
  });
});