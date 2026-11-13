// REQ-5002 / REQ-4016: Kategorie-Typ (Normal, Ergebnis, Ursache, Wirkung) bei der Anlage waehlen
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import CategoryTree from "../CategoryTree";
import { useCategoryStore } from "../../store/categoryStore";

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
    const select = screen.getByLabelText("Kategorie-Typ") as HTMLSelectElement;
    const labels = Array.from(select.options).map((o) => o.text);
    expect(labels).toEqual(["Normal", "Ergebnis", "Ursache", "Wirkung"]);
  });

  it("sendet Typ 'cause' fuer Ursache", async () => {
    render(<CategoryTree projectId={5} />);
    fireEvent.change(screen.getByLabelText("Kategorie-Typ"), { target: { value: "ursache" } });
    fireEvent.change(screen.getByPlaceholderText("Neue Kategorie eingeben..."), { target: { value: "Farbe" } });
    fireEvent.submit(screen.getByPlaceholderText("Neue Kategorie eingeben...").closest("form")!);
    expect(createCategory).toHaveBeenCalledWith(5, "Farbe", "cause", false);
  });

  it("sendet Ergebnis-Flag fuer Ergebnis", async () => {
    render(<CategoryTree projectId={5} />);
    fireEvent.change(screen.getByLabelText("Kategorie-Typ"), { target: { value: "ergebnis" } });
    fireEvent.change(screen.getByPlaceholderText("Neue Kategorie eingeben..."), { target: { value: "Ausgabe" } });
    fireEvent.submit(screen.getByPlaceholderText("Neue Kategorie eingeben...").closest("form")!);
    expect(createCategory).toHaveBeenCalledWith(5, "Ausgabe", "standard", true);
  });
});
