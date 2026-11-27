// REQ-6001: Tests fuer ConstraintBuilder User-Workflows
// Prueft: buildAST-Fix, Fehlermeldungen, Editieren, GUI-Anzeige
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockT = (key: string, params?: Record<string, unknown>): string => {
  const tr: Record<string, string> = {
    "common.loading": "Lade...",
    "constraintBuilder.errorPrefix": "Fehler: {{message}}",
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

import ConstraintBuilder from "../ConstraintBuilder";
import { logicalConstraintsApi, categoriesApi, valuesApi } from "../../api/client";
import type { LogicalConstraint, ConstraintKind, ConstraintNode } from "../../api/client";
import type { Category, Value } from "../../types";

// ---------------------------------------------------------------------------
// Test Data
// ---------------------------------------------------------------------------

const mockCategories: Category[] = [
  { id: 1, name: "Gewicht", order_index: 0 },
  { id: 2, name: "Groesse", order_index: 1 },
  { id: 3, name: "Zielland", order_index: 2 },
  { id: 4, name: "Portopreis", order_index: 3 },
];

const mockValues: Record<number, Value[]> = {
  1: [
    { id: 10, value: "0–500g", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 11, value: "500–1000g", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
  ],
  2: [
    { id: 20, value: "Briefumschlag", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 21, value: "Karton", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
  ],
  3: [
    { id: 30, value: "Deutschland", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 31, value: "International", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
  ],
  4: [
    { id: 40, value: "0,85 €", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
    { id: 41, value: "1,50 €", risk_weight: 1, vtype: "string", allowed: true, is_default: false },
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

// ---------------------------------------------------------------------------
// Setup / Teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(console, "warn").mockImplementation(() => {});
  vi.spyOn(window, "confirm").mockImplementation(() => true);

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
  vi.mocked(logicalConstraintsApi.update).mockImplementation(
    (projectId: number, cid: number, data: { name: string; kind: string; expression: unknown; consequence?: unknown }) =>
      Promise.resolve({
        id: cid,
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
// Tests - User Workflows
// ---------------------------------------------------------------------------

describe("ConstraintBuilder - User Workflows", () => {
  describe("buildAST-Fix: 2 Bedingungen + 2 Folgen", () => {
    it("sollte IF A AND B THEN C AND D korrekt speichern", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      // Name
      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Brief-Regel" } });

      // Kind: implies
      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      fireEvent.change(kindSelect, { target: { value: "implies" } });
      await waitFor(() => {
        expect(screen.getByText("Folge")).toBeInTheDocument();
      });

      // Bedingung: 2 Atome (Gewicht + Groesse)
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);

      // Folge: 2 Atome (Zielland + Portopreis)
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[1]);
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[1]);

      // Speichern
      fireEvent.click(screen.getByText("Constraint speichern"));

      await waitFor(() => {
        expect(logicalConstraintsApi.create).toHaveBeenCalledWith(1, expect.objectContaining({
          name: "Brief-Regel",
          kind: "implies",
        }));
        // Pruefe dass expression und consequence AND-Gruppen sind
        const call = vi.mocked(logicalConstraintsApi.create).mock.calls[0];
        const payload = call[1] as Record<string, unknown>;
        expect((payload.expression as Record<string, unknown>).op).toBe("and");
        expect((payload.consequence as Record<string, unknown>).op).toBe("and");
      });
    });
  });

  describe("buildAST-Fix: 1 Bedingung + 1 Folge", () => {
    it("sollte IF A THEN B korrekt speichern (keine AND-Gruppe)", async () => {
      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Einfach" } });

      const kindSelect = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
      fireEvent.change(kindSelect, { target: { value: "implies" } });
      await waitFor(() => {
        expect(screen.getByText("Folge")).toBeInTheDocument();
      });

      // Bedingung: 1 Atom
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);

      // Folge: 1 Atom
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[1]);

      // Speichern
      fireEvent.click(screen.getByText("Constraint speichern"));

      await waitFor(() => {
        expect(logicalConstraintsApi.create).toHaveBeenCalledWith(1, expect.objectContaining({
          name: "Einfach",
          kind: "implies",
        }));
        // Pruefe dass expression und consequence KEINE AND-Gruppen sind (direkte Atome)
        const call = vi.mocked(logicalConstraintsApi.create).mock.calls[0];
        const payload = call[1] as Record<string, unknown>;
        expect((payload.expression as Record<string, unknown>).op).toBe("eq");
        expect((payload.consequence as Record<string, unknown>).op).toBe("eq");
      });
    });
  });

  describe("Constraint bearbeiten", () => {
    it("sollte bestehendes Constraint laden und aendern", async () => {
      const existingConstraint = makeMockConstraint(
        1,
        "Alte Regel",
        "implies",
        { op: "eq", category_id: 1, value_id: 10 },
        { op: "eq", category_id: 3, value_id: 30 }
      );
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([existingConstraint]);

      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Alte Regel")).toBeInTheDocument();
      });

      // Bearbeiten
      const editButtons = screen.getAllByText("\u270f\ufe0f");
      fireEvent.click(editButtons[0]);
      await waitFor(() => {
        expect(screen.getByText("Bearbeiten")).toBeInTheDocument();
      });

      // Name aendern
      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Neue Regel" } });

      // Speichern
      fireEvent.click(screen.getByText("Constraint speichern"));

      await waitFor(() => {
        expect(logicalConstraintsApi.update).toHaveBeenCalledWith(1, 1, expect.objectContaining({
          name: "Neue Regel",
        }));
      });
    });

    it("sollte AND-Gruppe 2+2 korrekt laden und anzeigen (Postbeispiel)", async () => {
      const existingConstraint = makeMockConstraint(
        1,
        "brief",
        "implies",
        {
          op: "and",
          args: [
            { op: "eq", category_id: 1, value_id: 10 },
            { op: "eq", category_id: 2, value_id: 20 },
          ],
        } as any,
        {
          op: "and",
          args: [
            { op: "eq", category_id: 3, value_id: 30 },
            { op: "eq", category_id: 4, value_id: 40 },
          ],
        } as any
      );
      vi.mocked(logicalConstraintsApi.list).mockResolvedValue([existingConstraint]);

      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("brief")).toBeInTheDocument();
      });

      // Bearbeiten
      const editButtons = screen.getAllByText("\u270f\ufe0f");
      fireEvent.click(editButtons[0]);
      await waitFor(() => {
        expect(screen.getByText("Bearbeiten")).toBeInTheDocument();
      });

      // Name muss geladen sein
      const nameInput = screen.getByPlaceholderText("Constraint-Name...") as HTMLInputElement;
      expect(nameInput.value).toBe("brief");

      // Keine "(leere Bedingung)" - beide Bereiche muessen gefuellt sein
      expect(screen.queryByText("(leere Bedingung)")).not.toBeInTheDocument();

      // Textdarstellung muss die echten Werte zeigen (nicht "?")
      await waitFor(() => {
        const matches = screen.getAllByText(/Gewicht.*Briefumschlag.*THEN.*Deutschland/i);
        expect(matches.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe("Fehlerbehandlung", () => {
    it("sollte Validierungsfehler anzeigen", async () => {
      vi.mocked(logicalConstraintsApi.validate).mockResolvedValue({
        is_valid: false,
        errors: ["Ungueltiger Operator 'xyz'", "Fehlendes Feld 'category_id'"],
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
        expect(screen.getByText("Validierungsfehler: Ungueltiger Operator 'xyz'; Fehlendes Feld 'category_id'")).toBeInTheDocument();
      });
    });

    it("sollte Axios-Fehler mit detail.errors anzeigen", async () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            message: "Ungueltiges Constraint-AST",
            errors: ["Operator 'and' braucht mindestens 2 Argumente in 'args'"],
          },
        },
      };
      vi.mocked(logicalConstraintsApi.create).mockRejectedValue(axiosError);

      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));

      await waitFor(() => {
        expect(screen.getByText("Validierungsfehler: Operator 'and' braucht mindestens 2 Argumente in 'args'")).toBeInTheDocument();
      });
    });

    it("sollte Axios-Fehler mit nur message anzeigen", async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 400,
          data: {
            message: "implies-Constraints brauchen ein 'consequence'-Feld",
          },
        },
      };
      vi.mocked(logicalConstraintsApi.create).mockRejectedValue(axiosError as any);

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

      // Pruefe dass eine Fehlermeldung angezeigt wird (nicht der rohe Axios-Fehler)
      await waitFor(() => {
        expect(screen.getByText(/(implies-Constraints brauchen|Fehler beim Speichern|Speicherfehler)/i)).toBeInTheDocument();
      });
    });

    it("sollte generischen Fehler bei unbekanntem Error anzeigen", async () => {
      vi.mocked(logicalConstraintsApi.create).mockRejectedValue(new Error("Netzwerkfehler"));

      render(<ConstraintBuilder projectId={1} />);
      await waitFor(() => {
        expect(screen.getByText("Bedingung")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Constraint-Name...");
      fireEvent.change(nameInput, { target: { value: "Test" } });
      fireEvent.click(screen.getAllByText("+ Bedingung hinzufuegen")[0]);
      fireEvent.click(screen.getByText("Constraint speichern"));

      await waitFor(() => {
        expect(screen.getByText("Fehler: Netzwerkfehler")).toBeInTheDocument();
      });
    });
  });
});