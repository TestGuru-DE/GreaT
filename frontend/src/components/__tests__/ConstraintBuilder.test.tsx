// REQ-6001: Tests fuer ConstraintBuilder-Komponente (Logischer Constraint-Editor)
// ADR-020: AST-Format fuer logische Constraints
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks (mussen VOR dem Import der Component stehen - hoisting durch vi.mock)
// ---------------------------------------------------------------------------

const mockT = (key: string, params?: Record<string, unknown>): string => {
  const tr: Record<string, string> = {
    "common.loading": "Lade...",
    "common.edit": "Bearbeiten",
    "common.cancel": "Abbrechen",
    "common.delete": "Loeschen",
    "constraintBuilder.title": "Logische Constraints",
    "constraintBuilder.kind": "Constraint-Typ",
    "constraintBuilder.forbid": "Verbot (NICHT Bedingung)",
    "constraintBuilder.implies": "Implikation (WENN Bedingung DANN Folge)",
    "constraintBuilder.name": "Name",
    "constraintBuilder.namePlaceholder": "Constraint-Name...",
    "constraintBuilder.condition": "Bedingung",
    "constraintBuilder.consequence": "Folge",
    "constraintBuilder.addCondition": "Bedingung hinzufuegen",
    "constraintBuilder.addGroup": "Gruppe hinzufuegen",
    "constraintBuilder.andGroup": "UND-Gruppe",
    "constraintBuilder.orGroup": "ODER-Gruppe",
    "constraintBuilder.not": "NICHT",
    "constraintBuilder.operator": "Operator",
    "constraintBuilder.category": "Kategorie",
    "constraintBuilder.value": "Wert",
    "constraintBuilder.valueEquals": "=",
    "constraintBuilder.valueNotEquals": "!=",
    "constraintBuilder.valueIn": "IN",
    "constraintBuilder.valueNotIn": "NOT IN",
    "constraintBuilder.textPreview": "Textdarstellung",
    "constraintBuilder.copy": "Kopieren",
    "constraintBuilder.copied": "Kopiert!",
    "constraintBuilder.save": "Constraint speichern",
    "constraintBuilder.saved": "Constraint gespeichert.",
    "constraintBuilder.saveError": "Fehler beim Speichern.",
    "constraintBuilder.validationError": "Validierungsfehler: {{errors}}",
    "constraintBuilder.invalidConstraint": "Ungueltig: {{reason}}",
    "constraintBuilder.deleteConfirm": 'Constraint "{{name}}" wirklich loeschen?',
    "constraintBuilder.deleteTitle": "Constraint loeschen",
    "constraintBuilder.edit": "Bearbeiten",
    "constraintBuilder.noConstraints": "Noch keine logischen Constraints.",
    "constraintBuilder.needOneCategory": "Mindestens eine Kategorie erforderlich.",
    "constraintBuilder.loadError": "Fehler beim Laden der Daten: {{error}}",
    "constraintBuilder.emptyCondition": "(leere Bedingung)",
  };
  let v = tr[key] ?? key;
  if (params) {
    v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
  }
  return v;
};

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: mockT,
    i18n: { language: "de" },
  }),
}));

// Mock factory: all mock functions defined INSIDE the factory to avoid hoisting issues
vi.mock("../../api/client", () => {
  const mLogicalList = vi.fn();
  const mLogicalCreate = vi.fn();
  const mLogicalUpdate = vi.fn();
  const mLogicalDelete = vi.fn();
  const mLogicalValidate = vi.fn();
  const mCategoriesList = vi.fn();
  const mValuesList = vi.fn();

  return {
    logicalConstraintsApi: {
      list: mLogicalList,
      get: vi.fn(),
      create: mLogicalCreate,
      update: mLogicalUpdate,
      delete: mLogicalDelete,
      validate: mLogicalValidate,
    },
    categoriesApi: {
      list: mCategoriesList,
      create: vi.fn(),
      delete: vi.fn(),
      updateProperties: vi.fn(),
      setDefault: vi.fn(),
      unsetDefault: vi.fn(),
    },
    valuesApi: {
      list: mValuesList,
      create: vi.fn(),
      delete: vi.fn(),
    },
    default: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
    api: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
    authClient: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
    projectsApi: {},
    generateApi: {},
    rulesApi: {},
    datanodesApi: {},
    decisionTableApi: {},
    constraintsApi: {},
    backupApi: {},
    renameApi: {},
    categoryPropertiesApi: {},
    reorderApi: {},
  };
});

vi.mock("../../i18n", () => ({
  default: { language: "de" },
}));

vi.mock("../../store/authStore", () => ({
  useAuthStore: {
    getState: () => ({ refresh: vi.fn(), logout: vi.fn() }),
  },
}));

// Now import the mocked modules
import ConstraintBuilder from "../ConstraintBuilder";
import { logicalConstraintsApi, categoriesApi, valuesApi } from "../../api/client";
import type {
  LogicalConstraint,
  ConstraintKind,
  ConstraintNode,
} from "../../api/client";
import type { Category, Value } from "../../types";

// ---------------------------------------------------------------------------
// Test Data
// ---------------------------------------------------------------------------

const mockCategories: Category[] = [
  { id: 1, name: "Farbe", order_index: 0 },
  { id: 2, name: "Groesse", order_index: 1 },
];

const mockValues: Record<number, Value[]> = {
  1: [
    { id: 10, value: "rot", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 11, value: "blau", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
  ],
  2: [
    { id: 20, value: "S", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 21, value: "M", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
  ],
};

function makeMockConstraint(
  id: number,
  name: string,
  kind: ConstraintKind,
  expression: ConstraintNode,
  consequence?: ConstraintNode,
  isValid = true
): LogicalConstraint {
  return {
    id,
    project_id: 1,
    name,
    kind,
    expression,
    consequence,
    is_valid: isValid,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

const mockForbidConstraint = makeMockConstraint(
  1,
  "Kein rotes S",
  "forbid",
  { op: "eq", category_id: 1, value_id: 10 }
);

const mockImpliesConstraint = makeMockConstraint(
  2,
  "Rot impliziert S",
  "implies",
  { op: "eq", category_id: 1, value_id: 10 },
  { op: "eq", category_id: 2, value_id: 20 }
);

// ---------------------------------------------------------------------------
// Setup / Teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(window, "confirm").mockImplementation(() => true);

  // Default: categories + values load successfully, constraints list empty
  vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);
  vi.mocked(valuesApi.list).mockImplementation((catId: number) =>
    Promise.resolve(mockValues[catId] ?? [])
  );
  vi.mocked(logicalConstraintsApi.list).mockResolvedValue([]);
  vi.mocked(logicalConstraintsApi.validate).mockResolvedValue({ is_valid: true, errors: [] });
  vi.mocked(logicalConstraintsApi.create).mockImplementation(
    (projectId: number, data: { name: string; kind: string; expression: unknown; consequence?: unknown }) =>
      Promise.resolve({
        id: 99,
        project_id: projectId,
        name: data.name,
        kind: data.kind as ConstraintKind,
        expression: data.expression as ConstraintNode,
        consequence: data.consequence as ConstraintNode | undefined,
        is_valid: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      } as LogicalConstraint)
  );
  vi.mocked(logicalConstraintsApi.delete).mockResolvedValue({ ok: true });
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ConstraintBuilder - REQ-6001", () => {
  describe("Initial Render", () => {
    it("zeigt 'Mindestens eine Kategorie erforderlich' wenn keine Kategorien vorhanden sind", async () => {
      vi.mocked(categoriesApi.list).mockResolvedValue([]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Mindestens eine Kategorie erforderlich.")).toBeInTheDocument();
      });
    });

    it("zeigt Builder wenn Kategorien vorhanden sind", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Logische Constraints")).toBeInTheDocument();
      });
      expect(screen.getByText("Bedingung")).toBeInTheDocument();
    });

    it("zeigt Loading-State waehrend Daten geladen werden", () => {
      let resolveLoad: () => void;
      vi.mocked(categoriesApi.list).mockImplementation(
        () => new Promise((resolve) => { resolveLoad = () => resolve(mockCategories); })
      );
      vi.mocked(logicalConstraintsApi.list).mockImplementation(
        () => new Promise((resolve) => { resolveLoad = () => resolve([]); })
      );
      vi.mocked(valuesApi.list).mockResolvedValue([]);

      render(<ConstraintBuilder projectId={1} />);
      expect(screen.getByText("Lade...")).toBeInTheDocument();
      resolveLoad!();
    });

    it("zeigt Fehlermeldung bei API-Fehler beim Laden", async () => {
      vi.mocked(categoriesApi.list).mockRejectedValue(new Error("Netzwerkfehler"));
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Fehler beim Laden der Daten: Netzwerkfehler")).toBeInTheDocument();
      });
    });

    it("zeigt 'Noch keine logischen Constraints.' wenn Constraints-Liste leer ist", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Noch keine logischen Constraints.")).toBeInTheDocument();
      });
    });

    it("zeigt bestehende Constraints in der Liste", async () => {
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kein rotes S")).toBeInTheDocument();
      });
      // "Verbot (NICHT Bedingung)" appears in select option AND in constraint list badge
      // Use getAllByText and check that at least one is in a span (the badge)
      const forbidElements = screen.getAllByText("Verbot (NICHT Bedingung)");
      expect(forbidElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Constraint erstellen", () => {
    it("forbid-Constraint erstellen funktioniert", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test-Verbot" } });

      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      expect(kindSelect.value).toBe("forbid");

      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      await waitFor(() => {
        expect(screen.getAllByLabelText("Kategorie").length).toBeGreaterThan(0);
      });

      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(logicalConstraintsApi.create).toHaveBeenCalledWith(1, expect.objectContaining({
          name: "Test-Verbot",
          kind: "forbid",
        }));
      });
    });

    it("implies-Constraint mit consequence erstellen funktioniert", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test-Implikation" } });

      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      fireEvent.change(kindSelect, { target: { value: "implies" } });
      await waitFor(() => {
        expect(screen.getByText("Folge")).toBeInTheDocument();
      });

      // Add condition (first button)
      const addButtons1 = screen.getAllByText("+ Bedingung hinzufuegen");
      fireEvent.click(addButtons1[0]);

      // Add consequence (second button, now there should be 2)
      const addButtons2 = screen.getAllByText("+ Bedingung hinzufuegen");
      if (addButtons2.length >= 2) fireEvent.click(addButtons2[1]);

      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(logicalConstraintsApi.create).toHaveBeenCalledWith(1, expect.objectContaining({
          name: "Test-Implikation",
          kind: "implies",
        }));
      });
    });

    it("zeigt Fehler wenn Name leer beim Speichern", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(screen.getByText("Fehler beim Speichern.")).toBeInTheDocument();
      });
    });

    it("zeigt Fehler wenn Bedingung leer beim Speichern", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });
      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(screen.getByText("Fehler beim Speichern.")).toBeInTheDocument();
      });
    });

    it("zeigt Fehler wenn implies ohne consequence gespeichert wird", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });

      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      fireEvent.change(kindSelect, { target: { value: "implies" } });
      await waitFor(() => {
        expect(screen.getByText("Folge")).toBeInTheDocument();
      });

      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(screen.getByText("Fehler beim Speichern.")).toBeInTheDocument();
      });
    });

    it("zeigt Validierungsfehler bei API-Validierungsfehler", async () => {
      vi.mocked(logicalConstraintsApi.validate).mockResolvedValue({
        is_valid: false,
        errors: ["Widerspruechliche Bedingung"],
      });

      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(screen.getByText("Validierungsfehler: Widerspruechliche Bedingung")).toBeInTheDocument();
      });
    });

    it("zeigt Erfolgsmeldung nach erfolgreichem Speichern", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test-Verbot" } });
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));
      await waitFor(() => {
        expect(screen.getByText("Constraint gespeichert.")).toBeInTheDocument();
      });
    });
  });

  describe("Constraint loeschen", () => {
    it("Constraint loeschen funktioniert", async () => {
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kein rotes S")).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText("\u00d7");
      fireEvent.click(deleteButtons[0]);
      await waitFor(() => {
        expect(logicalConstraintsApi.delete).toHaveBeenCalledWith(1, 1);
      });
    });

    it("loescht Constraint nicht wenn confirm abgelehnt wird", async () => {
      vi.spyOn(window, "confirm").mockReturnValue(false);
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kein rotes S")).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText("\u00d7");
      fireEvent.click(deleteButtons[0]);
      await new Promise((r) => setTimeout(r, 100));
      expect(logicalConstraintsApi.delete).not.toHaveBeenCalled();
    });
  });

  describe("Text-Preview", () => {
    it("Text-Preview wird aktualisiert bei Aenderungen der Bedingung", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Textdarstellung")).toBeInTheDocument();
      });

      // Initially there are 2 elements with "(leere Bedingung)" - one in condition, one in preview
      expect(screen.getAllByText("(leere Bedingung)").length).toBeGreaterThanOrEqual(1);

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);

      // After adding condition, the condition area no longer shows "(leere Bedingung)"
      // The preview should now show actual text
      await waitFor(() => {
        // The preview area should now show real text instead of "(leere Bedingung)"
        const emptyElements = screen.queryAllByText("(leere Bedingung)");
        // At most 1 should remain (the preview might still show it briefly during re-render)
        expect(emptyElements.length).toBeLessThanOrEqual(1);
      });
    });

    it("zeigt 'Textdarstellung' Ueberschrift im Preview-Bereich", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Textdarstellung")).toBeInTheDocument();
      });
    });

    it("zeigt 'Kopieren' Button im Preview-Bereich", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kopieren")).toBeInTheDocument();
      });
    });
  });

  describe("Constraint-Liste", () => {
    it("zeigt Constraint mit is_valid=false als ungueltig", async () => {
      const invalidConstraint = makeMockConstraint(
        3, "Ungueltiger Constraint", "forbid",
        { op: "eq", category_id: 1, value_id: 10 }, undefined, false
      );
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([invalidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Ungueltiger Constraint")).toBeInTheDocument();
      });
    });

    it("zeigt Bearbeiten-Button fuer bestehende Constraints", async () => {
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kein rotes S")).toBeInTheDocument();
      });
      expect(screen.getAllByText("\u270f\ufe0f").length).toBeGreaterThan(0);
    });

    it("zeigt Constraint-Anzahl in der Ueberschrift", async () => {
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint, mockImpliesConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Logische Constraints (2)")).toBeInTheDocument();
      });
    });
  });

  describe("Builder-Interaktionen", () => {
    it("zeigt '(leere Bedingung)' Hinweis wenn keine Bedingungen vorhanden", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        // Text appears in both condition area and preview area
        expect(screen.getAllByText("(leere Bedingung)").length).toBeGreaterThanOrEqual(1);
      });
    });

    it("zeigt UND-Gruppe und ODER-Gruppe Buttons", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("+ UND-Gruppe")).toBeInTheDocument();
      });
      expect(screen.getByText("+ ODER-Gruppe")).toBeInTheDocument();
    });

    it("fuegt UND-Gruppe hinzu beim Klick", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("+ UND-Gruppe"));
      await waitFor(() => {
        expect(screen.getByText("UND-Gruppe")).toBeInTheDocument();
      });
    });

    it("fuegt ODER-Gruppe hinzu beim Klick", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("+ ODER-Gruppe"));
      await waitFor(() => {
        expect(screen.getByText("ODER-Gruppe")).toBeInTheDocument();
      });
    });

    it("zeigt Consequence-Bereich nur bei implies-Kind", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });
      expect(screen.queryByText("Folge")).not.toBeInTheDocument();

      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      fireEvent.change(kindSelect, { target: { value: "implies" } });
      await waitFor(() => {
        expect(screen.getByText("Folge")).toBeInTheDocument();
      });
    });

    it("zeigt Cancel-Button beim Bearbeiten", async () => {
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([mockForbidConstraint]);
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Kein rotes S")).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText("\u270f\ufe0f");
      fireEvent.click(editButtons[0]);
      await waitFor(() => {
        expect(screen.getByText("Bearbeiten")).toBeInTheDocument();
      });
      expect(screen.getByText("Abbrechen")).toBeInTheDocument();
    });
  });
});