// REQ-6006: Tests fuer ClassificationTreeMatrix
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import ClassificationTreeMatrix from "../ClassificationTreeMatrix";
import { generateApi } from "../../api/client";

vi.mock("../../api/client", () => ({
  generateApi: {
    listGenerations: vi.fn(),
    getTestcases: vi.fn(),
  },
}));

// Mock react-i18next directly (same pattern as all other tests)
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: ((key: string, params?: { defaultValue?: string }) => {
      const translations: Record<string, string> = {
        "classificationTree.selectGeneration": "Generierung:",
        "classificationTree.addTestCase": "Testfall",
        "classificationTree.addTestCaseComingSoon": "Manuelle Testfaelle folgen.",
        "classificationTree.loading": "Laden...",
        "classificationTree.origin": "Herkunft",
        "classificationTree.seed": "Seed",
        "classificationTree.generated": "ergaenzt",
        "classificationTree.noTestcases": "Keine Testfaelle. Zuerst generieren.",
        "classificationTree.errorValue": "Fehlerwert",
      };
      return params?.defaultValue ?? translations[key] ?? key;
    }) as any,
    i18n: { language: "de", getFixedT: () => () => "" },
  }),
}));

describe("ClassificationTreeMatrix", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: API returns { generations: [...] }
    vi.mocked(generateApi.listGenerations).mockResolvedValue({
      generations: [
        { id: 1, name: "pairwise-1", strategy: "pairwise" },
        { id: 2, name: "each-1", strategy: "each" },
      ],
    } as never);
    vi.mocked(generateApi.getTestcases).mockResolvedValue({
      testcases: [
        { id: 1, name: "TC_1", assignments: { Browser: "Chrome" } },
        { id: 2, name: "TC_2", assignments: { Browser: "Firefox" } },
      ],
      risk_summary: { total_risk: 10, max_possible_risk: 20, risk_coverage_percent: 50, testcase_count: 2 },
      result_categories: [],
    } as never);
  });

  it("laedt generations und zeigt Dropdown", async () => {
    render(
      <ClassificationTreeMatrix
        categories={[{ id: 1, name: "Browser", order_index: 0 }]}
        projectId={1}
      />
    );

    await waitFor(() => {
      const select = screen.getByRole("combobox");
      expect(select).toBeTruthy();
      expect((select as HTMLSelectElement).options.length).toBe(2);
    });
  });

  it("zeigt Testfaelle nach Generierungsauswahl", async () => {
    render(
      <ClassificationTreeMatrix
        categories={[{ id: 1, name: "Browser", order_index: 0 }]}
        projectId={1}
      />
    );

    await waitFor(() => {
      const rows = document.querySelectorAll("tbody tr");
      expect(rows.length).toBeGreaterThan(0);
    });
  });

  it("leere generations-Antwort (kein Crash)", async () => {
    vi.mocked(generateApi.listGenerations).mockResolvedValueOnce({ generations: [] } as never);

    const { container } = render(
      <ClassificationTreeMatrix
        categories={[{ id: 1, name: "A", order_index: 0 }]}
        projectId={99}
      />
    );

    await waitFor(() => {
      expect(container.textContent).toBeTruthy();
    });
  });

  it("API-Antwort ohne generations-Key (Fallback zu Array)", async () => {
    vi.mocked(generateApi.listGenerations).mockResolvedValueOnce([
      { id: 5, name: "legacy-gen", strategy: "pairwise" },
    ] as never);

    render(
      <ClassificationTreeMatrix
        categories={[{ id: 1, name: "A", order_index: 0 }]}
        projectId={98}
      />
    );

    await waitFor(() => {
      const select = screen.getByRole("combobox");
      expect((select as HTMLSelectElement).options.length).toBe(1);
    });
  });

  it("Fehler bei listGenerations (kein Crash)", async () => {
    vi.mocked(generateApi.listGenerations).mockRejectedValueOnce(new Error("Network error"));

    const { container } = render(
      <ClassificationTreeMatrix
        categories={[{ id: 1, name: "A", order_index: 0 }]}
        projectId={97}
      />
    );

    await waitFor(() => {
      expect(container.textContent).toBeTruthy();
    });
  });
});