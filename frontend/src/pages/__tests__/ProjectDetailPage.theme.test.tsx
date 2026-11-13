// REQ-3045: Theme-System - Frame-/Panel-Hintergruende muessen Theme-Tokens nutzen,
// damit "Theme Dark" & Co. auch in der Projektansicht sichtbar sind (kein hartkodiertes bg-white).
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
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
vi.mock("../../components/RuleVisualization", () => ({
  default: () => <div data-testid="rule-visualization-mock" />,
}));

describe("ProjectDetailPage - REQ-3045 Theme-Frames", () => {
  beforeEach(() => {
    vi.mocked(useProjectStore).mockReturnValue({
      projects: [{ id: 5, name: "Alpha" }],
      loading: false,
      error: null,
      fetchProjects: vi.fn(),
      createProject: vi.fn(),
      deleteProject: vi.fn(),
      bulkDelete: vi.fn(),
      bulkDeleteForce: vi.fn(),
    } as unknown as ReturnType<typeof useProjectStore>);
  });

  it("Breadcrumb-Header nutzt Theme-Token statt hartkodiertem bg-white", () => {
    const { container } = render(<ProjectDetailPage />);
    const header = container.querySelector("header");
    expect(header).not.toBeNull();
    expect(header!.className).not.toMatch(/\bbg-white\b/);
    expect(header!.className).toMatch(/\bbg-theme-(bg|surface)\b/);
  });

  it("linkes Panel (Kategorienbaum) nutzt Theme-Surface-Token statt bg-white", () => {
    const { container } = render(<ProjectDetailPage />);
    const categoryPanel = container.querySelector('[data-testid="category-tree-mock"]')!.closest("div.rounded-2xl");
    expect(categoryPanel).not.toBeNull();
    expect(categoryPanel!.className).not.toMatch(/\bbg-white\b/);
    expect(categoryPanel!.className).toMatch(/\bbg-theme-surface\b/);
  });

  it("rechtes Panel (Tabs) nutzt Theme-Surface-Token statt bg-white", () => {
    const { container } = render(<ProjectDetailPage />);
    const tabPanel = container.querySelector('[data-testid="testcase-panel-mock"]')!.closest("div.rounded-2xl");
    expect(tabPanel).not.toBeNull();
    expect(tabPanel!.className).not.toMatch(/\bbg-white\b/);
    expect(tabPanel!.className).toMatch(/\bbg-theme-surface\b/);
  });

  it("alle sichtbaren Textfarben verwenden Theme-Text-Tokens statt fixem slate-Grau", () => {
    const { container } = render(<ProjectDetailPage />);
    const heading = container.querySelector("h1");
    expect(heading).not.toBeNull();
    expect(heading!.className).not.toMatch(/\btext-slate-800\b/);
    expect(heading!.className).toMatch(/\btext-theme-text\b/);
  });
});
