// REQ-5002/REQ-4016: Kategorie-Typ wird im Baum visuell angezeigt (Badge U/W/E)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import CategoryTree from "../CategoryTree";
import { useCategoryStore } from "../../store/categoryStore";

vi.mock("../../store/categoryStore", () => ({
  useCategoryStore: vi.fn(),
}));
vi.mock("../../api/client", () => ({
  datanodesApi: { getTree: vi.fn().mockResolvedValue([]) },
  renameApi: { renameCategory: vi.fn(), renameValue: vi.fn(), category: vi.fn(), value: vi.fn() },
  reorderApi: { reorderCategories: vi.fn(), categories: vi.fn() },
  categoriesApi: { list: vi.fn().mockResolvedValue([]), setDefault: vi.fn() },
  categoryPropertiesApi: { updateIsResult: vi.fn(), updateCategoryType: vi.fn() },
}));
vi.mock("../bva/BVADialog", () => ({
  BVADialog: ({ isOpen, onClose, onApply }: any) => {
    if (!isOpen) return null;
    return (
      <div data-testid="bva-dialog-mock">
        <button onClick={onClose}>MockAbbrechen</button>
        <button onClick={() => onApply(["1", "2"])}>MockAnwenden</button>
      </div>
    );
  },
}));

describe("CategoryTree - Kategorie-Typ visuell anzeigen", () => {
  beforeEach(() => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [],
      values: {},
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
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

  it("zeigt 'U' Badge fuer Ursache-Kategorie", () => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [{ id: 1, name: "Farbe", order_index: 0, category_type: "cause" as const, is_result: false }],
      values: { 1: [] },
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues: vi.fn(),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
    render(<CategoryTree projectId={5} />);
    expect(screen.getByText("U")).toBeInTheDocument();
  });

  it("zeigt 'W' Badge fuer Wirkung-Kategorie", () => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [{ id: 2, name: "Ausgabe", order_index: 0, category_type: "effect" as const, is_result: false }],
      values: { 2: [] },
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues: vi.fn(),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
    render(<CategoryTree projectId={5} />);
    expect(screen.getByText("W")).toBeInTheDocument();
  });

  it("zeigt 'E' Badge fuer Ergebnis-Kategorie (is_result)", () => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [{ id: 3, name: "Ergebnis", order_index: 0, category_type: "standard" as const, is_result: true }],
      values: { 3: [] },
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues: vi.fn(),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
    render(<CategoryTree projectId={5} />);
    expect(screen.getByText("E")).toBeInTheDocument();
  });

  it("zeigt kein Badge fuer normale Kategorie", () => {
    vi.mocked(useCategoryStore).mockReturnValue({
      categories: [{ id: 4, name: "Normal", order_index: 0, category_type: "standard" as const, is_result: false }],
      values: { 4: [] },
      loading: false,
      error: null,
      fetchCategories: vi.fn(),
      createCategory: vi.fn(),
      deleteCategory: vi.fn(),
      fetchValues: vi.fn(),
      createValue: vi.fn(),
      deleteValue: vi.fn(),
      canUndo: false,
      canRedo: false,
      undo: vi.fn(),
      redo: vi.fn(),
    } as unknown as ReturnType<typeof useCategoryStore>);
    render(<CategoryTree projectId={5} />);
    expect(screen.queryByText("U")).not.toBeInTheDocument();
    expect(screen.queryByText("W")).not.toBeInTheDocument();
    expect(screen.queryByText("E")).not.toBeInTheDocument();
  });
});