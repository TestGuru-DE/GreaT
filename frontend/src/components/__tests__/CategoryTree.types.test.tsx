// REQ-5002 / REQ-4016: Kategorie-Typ (Normal, Ergebnis, Ursache, Wirkung) bei der Anlage waehlen
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import CategoryTree from "../CategoryTree";
import { useCategoryStore } from "../../store/categoryStore";

// REQ-6005: i18n mock for CategoryTree types tests
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
        "categoryTree.keyboardHelp.newCategory": "Alt+N: Neue Kategorie",
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
  datanodesApi: { getTree: vi.fn().mockResolvedValue([]) },
  renameApi: { renameCategory: vi.fn(), renameValue: vi.fn() },
  reorderApi: { reorderCategories: vi.fn() },
  categoriesApi: { list: vi.fn().mockResolvedValue([]) },
  categoryPropertiesApi: { updateIsResult: vi.fn(), updateCategoryType: vi.fn() },
}));

describe("CategoryTree - Kategorie-Typ bei der Anlage (REQ-5002)", () => {
  const createCategory = vi.fn().mockResolvedValue(undefined);
  beforeEach(() => {
    createCategory.mockClear();
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [],
      values: {},
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory,
      deleteCategory: vi.fn(),
      fetchValues: vi.fn(),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
  });

  it("bietet Normal, Ergebnis, Ursache und Wirkung an", () => {
    render(<CategoryTree projectId={5} />);
    const select = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
    const labels = Array.from(select.options).map((o) => o.text);
    expect(labels).toEqual(["Normal", "Ergebnis", "Ursache", "Wirkung"]);
  });

  it("sendet Typ 'cause' fuer Ursache", async () => {
    render(<CategoryTree projectId={5} />);
    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "ursache" } });
    fireEvent.change(screen.getByPlaceholderText("Neue Kategorie eingeben..."), { target: { value: "Farbe" } });
    fireEvent.submit(screen.getByPlaceholderText("Neue Kategorie eingeben...").closest("form")!);
    expect(createCategory).toHaveBeenCalledWith(5, "Farbe", "cause", false);
  });

  it("sendet Ergebnis-Flag fuer Ergebnis", async () => {
    render(<CategoryTree projectId={5} />);
    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "ergebnis" } });
    fireEvent.change(screen.getByPlaceholderText("Neue Kategorie eingeben..."), { target: { value: "Ausgabe" } });
    fireEvent.submit(screen.getByPlaceholderText("Neue Kategorie eingeben...").closest("form")!);
    expect(createCategory).toHaveBeenCalledWith(5, "Ausgabe", "standard", true);
  });
});
