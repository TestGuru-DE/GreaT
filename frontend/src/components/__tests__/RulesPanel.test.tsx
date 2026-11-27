// REQ-3003 + REQ-3004: Tests fuer den Regeleditor in RulesPanel (Formular, direktes Speichern, Konflikt-Warnung)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import RulesPanel from "../RulesPanel";
import { rulesApi, categoriesApi, valuesApi } from "../../api/client";

// REQ-6005: i18n mock for RulesPanel tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "rulesPanel.loading": "Lade Regeln...",
        "rulesPanel.needTwoCategories": "Mindestens zwei Kategorien erforderlich um Regeln anzulegen.",
        "rulesPanel.createTitle": "Neue Regel anlegen",
        "rulesPanel.typeLabel": "Regeltyp",
        "rulesPanel.ifCategoryLabel": "Wenn Kategorie",
        "rulesPanel.valueLabel": "Wert",
        "rulesPanel.thenCategoryLabelExclude": "Paar-Kategorie",
        "rulesPanel.thenCategoryLabel": "Dann Kategorie",
        "rulesPanel.thenValueLabelCombine": "Erlaubte Werte (Mehrfachauswahl)",
        "rulesPanel.saveBtn": "Regel speichern",
        "rulesPanel.ruleCount": "{{count}} Regel{{count, select, 1 {} other {n}}}",
        "rulesPanel.noRules": "Noch keine Regeln angelegt.",
        "rulesPanel.ifLabel": "Wenn",
        "rulesPanel.thenLabel": "Dann",
        "rulesPanel.excludeLabel": "Nicht mit",
        "rulesPanel.conflictWarning": "⚠️ Regelwiderspruch mit Regel #{{ids}}",
        "rulesPanel.deleteConfirm": "Regel löschen?",
        "rulesPanel.deleteTitle": "Regel löschen",
        "rulesPanel.saved": "Regel gespeichert.",
        "rulesPanel.saveError": "Fehler beim Speichern.",
        "rulesPanel.conflictWith": "Regelwiderspruch mit Regel #{{ids}}",
        "rulesPanel.typeLabels.exclude": "Verboten (Paar nicht gemeinsam)",
        "rulesPanel.typeLabels.dependency": "Abhängig (Wenn/Dann)",
        "rulesPanel.typeLabels.combine": "Kombinieren (Fan-out)",
      };
      let v = tr[key] ?? key;
      if (params) {
        // Handle i18next pluralization: {{count, select, 1 {} other {n}}}
        if (v.includes("{{count, select, 1 {} other {n}}}") && params.count === 1) {
          v = v.replace(/\{\{count, select, 1 \{\} other \{n\}\}\}/, "");
        } else if (v.includes("{{count, select, 1 {} other {n}}}")) {
          v = v.replace(/\{\{count, select, 1 \{\} other \{n\}\}\}/, "n");
        }
        v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      }
      return v;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock("../../api/client", () => ({
  rulesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  categoriesApi: {
    list: vi.fn(),
  },
  valuesApi: {
    list: vi.fn(),
  },
}));

const categories = [
  { id: 1, name: "Farbe", order_index: 0 },
  { id: 2, name: "Groesse", order_index: 1 },
];

const valuesByCat: Record<number, { value: string }[]> = {
  1: [{ value: "rot" }, { value: "gruen" }],
  2: [{ value: "S" }, { value: "M" }],
};

function comboboxes() {
  return screen.getAllByRole("combobox") as HTMLSelectElement[];
}

describe("RulesPanel - REQ-3003 Regeleditor (Formular + direktes Speichern)", () => {
  beforeEach(() => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(categoriesApi.list).mockResolvedValue(categories as never);
    vi.mocked(valuesApi.list).mockImplementation(
      (catId: number) => Promise.resolve((valuesByCat[catId] ?? []) as never)
    );
  });

  it("zeigt ein Formular mit Typ-Dropdown, Kategorie-Dropdowns und Wert-Dropdowns oberhalb der Regelanzeige", async () => {
    render(<RulesPanel projectId={1} />);

    expect(await screen.findByText("Neue Regel anlegen")).toBeInTheDocument();

    const [typeSelect, ifCatSelect, ifValSelect, thenCatSelect, thenValSelect] = comboboxes();

    // Typ-Dropdown mit den drei Regeltypen
    expect(within(typeSelect).getByText("Abhängig (Wenn/Dann)")).toBeInTheDocument();
    expect(within(typeSelect).getByText("Verboten (Paar nicht gemeinsam)")).toBeInTheDocument();
    expect(within(typeSelect).getByText("Kombinieren (Fan-out)")).toBeInTheDocument();

    // Kategorie-Dropdowns (Wenn/Dann) mit allen Projekt-Kategorien
    expect(within(ifCatSelect).getByText("Farbe")).toBeInTheDocument();
    expect(within(ifCatSelect).getByText("Groesse")).toBeInTheDocument();
    expect(within(thenCatSelect).getByText("Farbe")).toBeInTheDocument();
    expect(within(thenCatSelect).getByText("Groesse")).toBeInTheDocument();

    // Wert-Dropdowns mit den Werten der jeweils gewaehlten Kategorie
    expect(within(ifValSelect).getByText("rot")).toBeInTheDocument();
    expect(within(ifValSelect).getByText("gruen")).toBeInTheDocument();
    expect(within(thenValSelect).getByText("S")).toBeInTheDocument();
    expect(within(thenValSelect).getByText("M")).toBeInTheDocument();

    // Block liegt oberhalb der Regelanzeige
    const heading = screen.getByText("Neue Regel anlegen");
    const rulesHeading = await screen.findByText("0 Regeln");
    expect(heading.compareDocumentPosition(rulesHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it.each([
    ["Normal", ""],
    ["Dark", "theme-dark"],
    ["Heavy Metal", "theme-heavy-metal"],
  ])("zeigt in Theme %s schwarze Feldtexte fuer alle Regel-Selects (REQ-3045)", async (_themeName, themeClass) => {
    document.documentElement.className = themeClass;
    render(<RulesPanel projectId={1} />);

    await screen.findByText("Neue Regel anlegen");
    const [typeSelect, ifCatSelect, ifValSelect, thenCatSelect, thenValSelect] = comboboxes();

    expect(typeSelect).toHaveClass("text-theme-text");
    expect(ifCatSelect).toHaveClass("text-theme-text");
    expect(ifValSelect).toHaveClass("text-theme-text");
    expect(thenCatSelect).toHaveClass("text-theme-text");
    expect(thenValSelect).toHaveClass("text-theme-text");
  });

  it.each([
    ["Normal", ""],
    ["Dark", "theme-dark"],
    ["Heavy Metal", "theme-heavy-metal"],
  ])("zeigt in Theme %s schwarze Textfarbe in der Regelauflistung", async (_themeName, themeClass) => {
    vi.mocked(rulesApi.list).mockResolvedValue([
      {
        id: 12,
        type: "dependency",
        if_category_id: 1,
        if_value: "rot",
        then_category_id: 2,
        then_value: "S",
        then_values_json: null,
      },
    ] as never);

    document.documentElement.className = themeClass;
    render(<RulesPanel projectId={1} />);

    const list = await screen.findByRole("list");
    const ruleItem = within(list).getByText("rot").closest("li");
    expect(ruleItem).not.toBeNull();
    expect(ruleItem!).toHaveClass("text-theme-text");
  });

  it("speichert eine neue Regel direkt ueber den Editor und zeigt sie danach in der Regelanzeige", async () => {
    vi.mocked(rulesApi.create).mockResolvedValue({
      id: 5,
      type: "dependency",
      if_category_id: 1,
      if_value: "gruen",
      then_category_id: 2,
      then_value: "M",
      then_values_json: null,
      conflict_with: [],
    } as never);

    render(<RulesPanel projectId={1} />);
    await screen.findByText("Neue Regel anlegen");

    const [, , ifValSelect, , thenValSelect] = comboboxes();
    fireEvent.change(ifValSelect, { target: { value: "gruen" } });
    fireEvent.change(thenValSelect, { target: { value: "M" } });

    fireEvent.click(screen.getByText("Regel speichern"));

    await waitFor(() => {
      expect(rulesApi.create).toHaveBeenCalledWith(1, {
        type: "dependency",
        if_category_id: 1,
        if_value: "gruen",
        then_category_id: 2,
        then_value: "M",
        then_values: undefined,
      });
    });

    expect(await screen.findByText("Regel gespeichert.")).toBeInTheDocument();
    expect(await screen.findByText("1 Regel")).toBeInTheDocument();

    const list = screen.getByRole("list");
    expect(within(list).getByText("gruen")).toBeInTheDocument();
    expect(within(list).getByText("M")).toBeInTheDocument();
  });
});

describe("RulesPanel - REQ-3004 Regelwiderspruch-Erkennung", () => {
  beforeEach(() => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(categoriesApi.list).mockResolvedValue(categories as never);
    vi.mocked(valuesApi.list).mockImplementation(
      (catId: number) => Promise.resolve((valuesByCat[catId] ?? []) as never)
    );
  });

  it("zeigt beim Speichern eine Konflikt-Warnung mit Regelnummer und hebt die Regel in der Anzeige hervor", async () => {
    vi.mocked(rulesApi.create).mockResolvedValue({
      id: 9,
      type: "dependency",
      if_category_id: 1,
      if_value: "rot",
      then_category_id: 2,
      then_value: "S",
      then_values_json: null,
      conflict_with: [7],
    } as never);

    render(<RulesPanel projectId={1} />);
    await screen.findByText("Neue Regel anlegen");

    fireEvent.click(screen.getByText("Regel speichern"));

    // Widerspruch wird direkt im Regeleditor angezeigt: "Regelwiderspruch mit Regel [Regelnummer]"
    const warnings = await screen.findAllByText(/Regelwiderspruch mit Regel #7/);
    expect(warnings.length).toBeGreaterThanOrEqual(1);

    // Die widersprüchliche Regel ist in der Regelanzeige hervorgehoben
    const list = screen.getByRole("list");
    const ruleItem = within(list).getByText("rot").closest("li");
    expect(ruleItem).not.toBeNull();
    expect(ruleItem!.className).toMatch(/warning/);

    // Speichern ist trotzdem möglich (Warnung, kein Hard-Block) - Regel wurde trotzdem uebernommen
    expect(await screen.findByText("1 Regel")).toBeInTheDocument();
  });

  it("zeigt bei widerspruchsfreier Regel eine Erfolgsmeldung ohne Hervorhebung", async () => {
    vi.mocked(rulesApi.create).mockResolvedValue({
      id: 3,
      type: "dependency",
      if_category_id: 1,
      if_value: "rot",
      then_category_id: 2,
      then_value: "S",
      then_values_json: null,
      conflict_with: [],
    } as never);

    render(<RulesPanel projectId={1} />);
    await screen.findByText("Neue Regel anlegen");

    fireEvent.click(screen.getByText("Regel speichern"));

    expect(await screen.findByText("Regel gespeichert.")).toBeInTheDocument();
    expect(screen.queryByText(/Regelwiderspruch/)).not.toBeInTheDocument();

    const list = screen.getByRole("list");
    const ruleItem = within(list).getByText("rot").closest("li");
    expect(ruleItem!.className).not.toMatch(/warning/);
  });
});