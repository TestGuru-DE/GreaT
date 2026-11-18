// REQ-4019: Tests fuer GUI-Aktualisierung nach Schliessen von Dialogen (Grenzwertanalyse etc.)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import CategoryTree from "../CategoryTree";
import { useCategoryStore } from "../../store/categoryStore";
import { datanodesApi } from "../../api/client";

// REQ-6005: i18n mock for CategoryTree tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "categoryTree.newCategoryPlaceholder": "Neue Kategorie eingeben...",
        "categoryTree.newValuePlaceholder": "Neuer Wert... (Enter)",
        "categoryTree.noCategories": "Noch keine Kategorien",
        "categoryTree.noCategoriesHint": "Gib oben einen Namen ein und klicke +",
        "categoryTree.noValues": "Noch keine Werte",
        "categoryTree.valuesCount": "{{count}} Werte",
        "categoryTree.loadValues": "Werte laden (klick)",
        "categoryTree.contextMenu.rename": "Umbenennen (F2)",
        "categoryTree.contextMenu.typeNormal": "Typ: Normal",
        "categoryTree.contextMenu.typeCause": "Typ: Ursache",
        "categoryTree.contextMenu.typeEffect": "Typ: Wirkung",
        "categoryTree.contextMenu.addValue": "Wert hinzufügen",
        "categoryTree.contextMenu.applyDataClass": "Datenklasse anwenden...",
        "categoryTree.contextMenu.bva": "Grenzwertanalyse...",
        "categoryTree.contextMenu.delete": "Löschen",
        "categoryTree.contextMenu.setDefault": "★ Als Default markieren",
        "categoryTree.contextMenu.unsetDefault": "✕ Default entfernen",
        "categoryTree.categoryType.normal": "Normal",
        "categoryTree.categoryType.ergebnis": "Ergebnis",
        "categoryTree.categoryType.ursache": "Ursache",
        "categoryTree.categoryType.wirkung": "Wirkung",
        "dataNodeApplyDialog.title": "Datenklasse anwenden auf: {{categoryName}}",
        "dataNodeApplyDialog.apply": "Übernehmen",
        "dataNodeApplyDialog.cancel": "Abbrechen",
        "dataNodeApplyDialog.search": "Suche...",
        "dataNodeTree.category": "Kategorie",
        "dataNodeTree.group": "Gruppe",
        "dataNodeTree.class": "Klasse",
        "dataNodeTree.addChild": "Unterpunkt",
        "dataNodeTree.addValue": "Wert",
        "dataNodeTree.value": "Wert",
        "dataNodeTree.valuePlaceholder": "Neuer Wert...",
        "dataNodeTree.childPlaceholder": "Name der Gruppe/Klasse...",
        "dataNodeTree.delete": "Löschen",
        "dataNodeTree.deleteConfirm": "Knoten und alle Unterpunkte löschen?",
        "dataNodeTree.expand": "Aufklappen",
        "dataNodeTree.collapse": "Zuklappen",
        "dataNodeTree.valuesCount": "{{count}} Werte",
        "contextMenu.rename": "Umbenennen (F2)",
        "contextMenu.delete": "Löschen",
        "bvaDialog.title": "Grenzwertanalyse: {{categoryName}}",
        "bvaDialog.cancel": "Abbrechen",
        "bvaDialog.apply": "Anwenden",
        "undoRedo.undo": "Rückgängig",
        "undoRedo.redo": "Wiederholen",
        "undoRedo.undoTitle": "Rückgängig (Strg+Z)",
        "undoRedo.redoTitle": "Wiederholen (Strg+Y)",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock("../../store/categoryStore", () => ({
  useCategoryStore: vi.fn(),
}));

vi.mock("../../api/client", () => ({
  categoriesApi: { setDefault: vi.fn() },
  categoryPropertiesApi: { updateIsResult: vi.fn() },
  datanodesApi: { getTree: vi.fn().mockResolvedValue([]) },
  renameApi: { category: vi.fn(), value: vi.fn() },
  reorderApi: { categories: vi.fn() },
}));

// BVADialog wird als einfache Test-Doppel gemockt, damit onClose/onApply gezielt ausgeloest werden koennen,
// ohne die komplexe interne BVA-Logik (Backend-Aufrufe, Fokus-Trap) mitzutesten.
vi.mock("../bva/BVADialog", () => ({
  BVADialog: ({ isOpen, onClose, onApply }: { isOpen: boolean; onClose: () => void; onApply: (v: string[]) => void }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="bva-dialog-mock">
        <button onClick={onClose}>MockAbbrechen</button>
        <button onClick={() => onApply(["1", "2"])}>MockAnwenden</button>
      </div>
    );
  },
}));

describe("CategoryTree - REQ-4019 Refresh nach Dialog-Schluss", () => {
  const category = { id: 1, name: "Kategorie 1", order_index: 0, is_result: false };
  const value = { id: 10, value: "A", risk_weight: 1, vtype: "string", allowed: true, is_default: false };

  let fetchValues: ReturnType<typeof vi.fn>;
  let fetchCategories: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchValues = vi.fn().mockResolvedValue(undefined);
    fetchCategories = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [category],
      values: { 1: [value] },
      loading: false,
      error: null,
      fetchCategories,
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues,
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
  });

  function expandCategory() {
    // Kategorie-Header anklicken, um sie aufzuklappen (setzt expanded[1] = true)
    fireEvent.click(screen.getByText("Kategorie 1"));
  }

  it("aktualisiert die Werte, wenn der BVA-Dialog per 'Abbrechen' geschlossen wird", async () => {
    render(<CategoryTree projectId={5} />);
    expandCategory();

    fireEvent.click(screen.getByTitle("Grenzwertanalyse..."));
    expect(screen.getByTestId("bva-dialog-mock")).toBeInTheDocument();

    fetchValues.mockClear();
    fireEvent.click(screen.getByText("MockAbbrechen"));

    expect(screen.queryByTestId("bva-dialog-mock")).not.toBeInTheDocument();
    expect(fetchValues).toHaveBeenCalledWith(1);
  });

  it("aktualisiert die Werte weiterhin, wenn der BVA-Dialog per 'Anwenden' geschlossen wird (Regression)", async () => {
    render(<CategoryTree projectId={5} />);
    expandCategory();

    fireEvent.click(screen.getByTitle("Grenzwertanalyse..."));
    fetchValues.mockClear();
    fireEvent.click(screen.getByText("MockAnwenden"));

    expect(fetchValues).toHaveBeenCalledWith(1);
  });
});

// Tech-Debt-Cleanup (Sprint 10, Aufgabe 7 / p3-dc-ux): Legacy-DataClassDialog wurde durch den
// DataNode-Baum-Dialog (REQ-4018) ersetzt. `dataClassCat` wurde nirgends mehr gesetzt (toter State),
// der alte Dialog war unerreichbar. Diese Tests sichern ab, dass (a) der Legacy-Code nicht wieder
// eingefuehrt wird und (b) der aktive Kontextmenue-/Dialogpfad ("Datenklasse anwenden...") weiterhin
// funktioniert.
describe("CategoryTree - Legacy-DataClassDialog entfernt (Tech-Debt-Cleanup, Sprint 10 Aufg. 7)", () => {
  const category = { id: 1, name: "Kategorie 1", order_index: 0, is_result: false };

  beforeEach(() => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [category],
      values: {},
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues: vi.fn().mockResolvedValue(undefined),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
  });

  it("importiert/rendert keinen Legacy-DataClassDialog mehr (Guard gegen Wiedereinfuehrung)", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(here, "..", "CategoryTree.tsx"), "utf-8");
    expect(source).not.toMatch(/DataClassDialog/);
  });

  it("oeffnet ueber das Kontextmenue 'Datenklasse anwenden...' weiterhin den DataNode-Baum-Dialog (REQ-4018)", async () => {
    render(<CategoryTree projectId={5} />);

    fireEvent.contextMenu(screen.getByText("Kategorie 1"));
    fireEvent.click(screen.getByText("Datenklasse anwenden..."));

    await waitFor(() => {
      expect(datanodesApi.getTree).toHaveBeenCalled();
    });
    expect(
      await screen.findByText("Datenklasse anwenden auf: Kategorie 1")
    ).toBeInTheDocument();
  });
});
