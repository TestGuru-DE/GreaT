// REQ-4022: Tests fuer StaleDataWarning-Integration in ProjectDetailPage
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProjectDetailPage from "../ProjectDetailPage";
import { useProjectStore } from "../../store/projectStore";
import { useConflictStore } from "../../store/conflictStore";
import type { ConflictInfo } from "../../api/handlers";

// Mock react-router-dom
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as any),
    useParams: () => ({ id: "5" }),
    useNavigate: () => vi.fn(),
  };
});

// Mock projectStore
vi.mock("../../store/projectStore", () => ({
  useProjectStore: vi.fn(),
}));

// Mock conflictStore
vi.mock("../../store/conflictStore", () => ({
  useConflictStore: vi.fn(),
}));

// Mock child components
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
vi.mock("../../components/RuleVisualization", () => ({
  default: () => <div data-testid="rule-visualization-mock" />,
}));

// Mock StaleDataWarning
vi.mock("../../components/StaleDataWarning", () => ({
  default: function MockStaleDataWarning({
    visible,
    modifiedBy,
    onReload,
    onOverwrite,
    onClose,
  }: {
    visible: boolean;
    modifiedBy?: string;
    onReload: () => void;
    onOverwrite: () => void;
    onClose: () => void;
  }) {
    if (!visible) return null;
    return (
      <div data-testid="stale-data-warning">
        <span data-testid="modified-by">
          {modifiedBy || "unknown"}
        </span>
        <button onClick={onReload} data-testid="reload-btn">
          Neu laden
        </button>
        <button onClick={onOverwrite} data-testid="overwrite-btn">
          Trotzdem ueberschreiben
        </button>
        <button onClick={onClose} data-testid="close-btn">
          Schliessen
        </button>
      </div>
    );
  },
}));

describe("ProjectDetailPage - StaleDataWarning Integration - REQ-4022", () => {
  let fetchProjects: ReturnType<typeof vi.fn>;
  let conflictState: {
    conflict: ConflictInfo | null;
    visible: boolean;
    setConflict: ReturnType<typeof vi.fn>;
    clearConflict: ReturnType<typeof vi.fn>;
    onReload: ReturnType<typeof vi.fn>;
    onOverwrite: ReturnType<typeof vi.fn>;
    onClose: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    fetchProjects = vi.fn().mockResolvedValue(undefined);

    conflictState = {
      conflict: null,
      visible: false,
      setConflict: vi.fn(),
      clearConflict: vi.fn(),
      onReload: vi.fn(),
      onOverwrite: vi.fn(),
      onClose: vi.fn(),
    };

    vi.mocked(useProjectStore).mockReturnValue({
      projects: [{ id: 5, name: "Test Projekt" }],
      loading: false,
      error: null,
      fetchProjects,
      createProject: vi.fn(),
      deleteProject: vi.fn(),
      bulkDelete: vi.fn(),
      bulkDeleteForce: vi.fn(),
    } as unknown as ReturnType<typeof useProjectStore>);

    vi.mocked(useConflictStore).mockImplementation((selector) => {
      // @ts-expect-error - selector returns the right value
      return selector(conflictState);
    });
  });

  it("zeigt StaleDataWarning nicht wenn kein Konflikt (visible=false)", () => {
    render(
      <MemoryRouter>
        <ProjectDetailPage />
      </MemoryRouter>
    );

    expect(screen.queryByTestId("stale-data-warning")).not.toBeInTheDocument();
  });

  it("zeigt StaleDataWarning wenn Konflikt vorliegt (visible=true)", () => {
    conflictState.visible = true;
    conflictState.conflict = {
      type: "version_conflict",
      message: "Version mismatch",
      clientVersion: 1,
      serverVersion: 2,
      modifiedBy: "admin",
    };

    render(
      <MemoryRouter>
        <ProjectDetailPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId("stale-data-warning")).toBeInTheDocument();
    expect(screen.getByTestId("modified-by")).toHaveTextContent("admin");
  });

  it("uebergibt modifiedBy aus conflict an StaleDataWarning", () => {
    conflictState.visible = true;
    conflictState.conflict = {
      type: "version_conflict",
      message: "Version mismatch",
      clientVersion: 1,
      serverVersion: 2,
      modifiedBy: "max.mustermann",
    };

    render(
      <MemoryRouter>
        <ProjectDetailPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId("modified-by")).toHaveTextContent("max.mustermann");
  });

  it("ruft fetchProjects auf wenn 'Neu laden' geklickt wird", () => {
    conflictState.visible = true;
    conflictState.conflict = {
      type: "version_conflict",
      message: "Version mismatch",
      clientVersion: 1,
      serverVersion: 2,
    };

    render(
      <MemoryRouter>
        <ProjectDetailPage />
      </MemoryRouter>
    );

    const reloadBtn = screen.getByTestId("reload-btn");
    fireEvent.click(reloadBtn);

    // onReload aus conflictStore sollte aufgerufen werden
    expect(conflictState.onReload).toHaveBeenCalled();
    // fetchProjects sollte aufgerufen werden fuer Reload
    expect(fetchProjects).toHaveBeenCalled();
  });

  it("ruft clearConflict auf wenn 'Schliessen' geklickt wird", () => {
    conflictState.visible = true;
    conflictState.conflict = {
      type: "version_conflict",
      message: "Version mismatch",
      clientVersion: 1,
      serverVersion: 2,
    };

    render(
      <MemoryRouter>
        <ProjectDetailPage />
      </MemoryRouter>
    );

    const closeBtn = screen.getByTestId("close-btn");
    fireEvent.click(closeBtn);

    expect(conflictState.onClose).toHaveBeenCalled();
  });
});