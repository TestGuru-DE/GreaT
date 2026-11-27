// REQ-6009: Frontend-Tests fuer SeedImport-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import SeedImport from "../SeedImport";
import { useSeedStore } from "../../store/seedStore";
import * as clientModule from "../../api/client";

// Mock seedApi
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
  };
});

const seedApi = clientModule.seedApi as {
  list: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  importCsv: ReturnType<typeof vi.fn>;
  gapFill: ReturnType<typeof vi.fn>;
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
);

describe("REQ-6009: SeedImport", () => {
  const onCloseMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    onCloseMock.mockReset();

    // Reset store state
    useSeedStore.setState({
      seedSets: [],
      currentSet: null,
      loading: false,
      error: null,
      msg: null,
    });

    // Default API responses
    seedApi.importCsv.mockResolvedValue({
      id: 1,
      name: "Imported Set",
      seed_count: 5,
      warnings: [],
    });
    seedApi.list.mockResolvedValue([]);
  });

  it("rendert Dialog mit Titel 'CSV Import'", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("CSV-Import")).toBeInTheDocument();
  });

  it("zeigt Name-Input-Feld", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    const input = screen.getByPlaceholderText(/z\. B\. Meine Seeds/i);
    expect(input).toBeInTheDocument();
  });

  it("zeigt Datei-Drop-Zone", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText(/CSV-Datei hier ablegen/i)).toBeInTheDocument();
  });

  it("zeigt 'durchsuchen' Button in Drop-Zone", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("durchsuchen")).toBeInTheDocument();
  });

  it("zeigt CSV-Format Info", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("CSV-Format")).toBeInTheDocument();
    expect(screen.getByText(/Erste Zeile: Kategorien/i)).toBeInTheDocument();
  });

  it("zeigt Abbrechen-Button", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("Abbrechen")).toBeInTheDocument();
  });

  it("zeigt Importieren-Button", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("Importieren")).toBeInTheDocument();
  });

  it("Importieren-Button ist disabled ohne Name und Datei", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    const importBtn = screen.getByText("Importieren");
    expect(importBtn).toBeDisabled();
  });

  it("Importieren-Button bleibt disabled wenn nur Name gesetzt", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    const input = screen.getByPlaceholderText(/z\. B\. Meine Seeds/i);
    fireEvent.change(input, { target: { value: "Mein Satz" } });

    const importBtn = screen.getByText("Importieren");
    expect(importBtn).toBeDisabled();
  });

  it("Importieren-Button ist disabled wenn loading=true", () => {
    useSeedStore.setState({ loading: true });

    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    // Even with name filled, loading disables the button
    const input = screen.getByPlaceholderText(/z\. B\. Meine Seeds/i);
    fireEvent.change(input, { target: { value: "Mein Satz" } });

    const importBtn = screen.getByText("Importiere …");
    expect(importBtn).toBeDisabled();
  });

  it("zeigt 'Importiere...' Text waehrend loading", () => {
    useSeedStore.setState({ loading: true });

    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("Importiere …")).toBeInTheDocument();
  });

  it("ruft onClose bei Abbrechen auf", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    const cancelBtn = screen.getByText("Abbrechen");
    fireEvent.click(cancelBtn);

    expect(onCloseMock).toHaveBeenCalled();
  });

  it("zeigt Message aus Store bei Erfolg", async () => {
    useSeedStore.setState({
      msg: { text: "5 Seeds importiert", type: "ok" },
    });

    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText("5 Seeds importiert")).toBeInTheDocument();
  });

  it("zeigt Warnung aus Store mit Warnsymbol", async () => {
    useSeedStore.setState({
      msg: { text: "Row 2 has missing values", type: "warn" },
    });

    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    expect(screen.getByText(/Row 2 has missing values/i)).toBeInTheDocument();
  });

  it("zeigt Format-Beispiel in <pre>", () => {
    render(<SeedImport projectId={1} onClose={onCloseMock} />, { wrapper });

    const pre = document.querySelector("pre");
    expect(pre).toBeInTheDocument();
    expect(pre?.textContent).toContain("KategorieA");
  });
});