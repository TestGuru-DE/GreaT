// REQ-4019: Tests fuer GUI-Aktualisierung bei Sichtenwechsel (Navigation)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ProjectDetailPage from "../ProjectDetailPage";
import { useProjectStore } from "../../store/projectStore";

vi.mock("react-router-dom", () => ({
  useParams: () => ({ id: "5" }),
  useNavigate: () => vi.fn(),
}));

vi.mock("../../store/projectStore", () => ({
  useProjectStore: vi.fn(),
}));

vi.mock("../../components/CategoryTree", () => ({
  default: () => <div data-testid="category-tree-mock" />,
}));
vi.mock("../../components/TestCasePanel", () => ({
  default: () => <div data-testid="testcase-panel-mock" />,
}));
vi.mock("../../components/RulesPanel", () => ({
  default: () => <div data-testid="rules-panel-mock" />,
}));
vi.mock("../../components/GenerationsPanel", () => ({
  default: () => <div data-testid="generations-panel-mock" />,
}));

describe("ProjectDetailPage - REQ-4019 Refresh bei Sichtenwechsel (Navigation)", () => {
  let fetchProjects: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchProjects = vi.fn().mockResolvedValue(undefined);
  });

  it("laedt die Projektliste beim Oeffnen der Ansicht neu, auch wenn bereits Projekte im Store vorhanden sind", () => {
    // Store enthaelt bereits Projekte aus einem frueheren Seitenaufruf (moeglicherweise veraltet,
    // z.B. weil der Projektname zwischenzeitlich in einer anderen Ansicht geaendert wurde).
    vi.mocked(useProjectStore).mockReturnValue({
      projects: [{ id: 5, name: "Alpha (alt)" }],
      loading: false,
      error: null,
      fetchProjects,
      createProject: vi.fn(),
      deleteProject: vi.fn(),
      bulkDelete: vi.fn(),
      bulkDeleteForce: vi.fn(),
    } as unknown as ReturnType<typeof useProjectStore>);

    render(<ProjectDetailPage />);

    expect(fetchProjects).toHaveBeenCalledTimes(1);
  });

  it("zeigt weiterhin sofort den bekannten Projektnamen, waehrend die Aktualisierung im Hintergrund laeuft", () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projects: [{ id: 5, name: "Alpha" }],
      loading: false,
      error: null,
      fetchProjects,
      createProject: vi.fn(),
      deleteProject: vi.fn(),
      bulkDelete: vi.fn(),
      bulkDeleteForce: vi.fn(),
    } as unknown as ReturnType<typeof useProjectStore>);

    render(<ProjectDetailPage />);

    expect(screen.getByText(/Projekt Alpha/)).toBeInTheDocument();
  });
});
