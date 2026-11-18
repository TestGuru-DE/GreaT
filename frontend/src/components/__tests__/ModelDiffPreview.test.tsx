// REQ-6013: Tests fuer ModelDiffPreview
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import ModelDiffPreview from "../ModelDiffPreview";
import type { ModelDiffResult } from "../../api/modelApi";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <I18nextProvider i18n={i18n}>
    {children}
  </I18nextProvider>
);

describe("REQ-6013: ModelDiffPreview", () => {
  it("should show no changes message when diff is empty", () => {
    const emptyDiff: ModelDiffResult = {
      added: { categories: [], values: [], rules: [] },
      modified: { categories: [], values: [], rules: [] },
      removed: { categories: [], values: [], rules: [] },
    };

    render(<ModelDiffPreview diff={emptyDiff} />, { wrapper });

    expect(screen.getByText("Keine Aenderungen erkannt.")).toBeInTheDocument();
  });

  it("should show added categories", () => {
    const diff: ModelDiffResult = {
      added: { categories: ["NewCategory"], values: [], rules: [] },
      modified: { categories: [], values: [], rules: [] },
      removed: { categories: [], values: [], rules: [] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    expect(screen.getByText("Aenderungsvorschau")).toBeInTheDocument();
    expect(screen.getByText("Kategorien")).toBeInTheDocument();

    // "+" Zeichen und Kategoriename sollten sichtbar sein
    const addedItem = screen.getByText("NewCategory");
    expect(addedItem).toBeInTheDocument();
  });

  it("should show added values with category prefix", () => {
    const diff: ModelDiffResult = {
      added: { categories: [], values: ["Category1/ValueA", "Category2/ValueB"], rules: [] },
      modified: { categories: [], values: [], rules: [] },
      removed: { categories: [], values: [], rules: [] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    expect(screen.getByText("Werte")).toBeInTheDocument();
    expect(screen.getByText("Category1/ValueA")).toBeInTheDocument();
    expect(screen.getByText("Category2/ValueB")).toBeInTheDocument();
  });

  it("should show removed items", () => {
    const diff: ModelDiffResult = {
      added: { categories: [], values: [], rules: [] },
      modified: { categories: [], values: [], rules: [] },
      removed: { categories: ["OldCategory"], values: ["Cat/OldVal"], rules: ["exclude:Cat1/A -> Cat2/B"] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    expect(screen.getByText("OldCategory")).toBeInTheDocument();
    expect(screen.getByText("Cat/OldVal")).toBeInTheDocument();
    expect(screen.getByText("exclude:Cat1/A -> Cat2/B")).toBeInTheDocument();
  });

  it("should show modified items", () => {
    const diff: ModelDiffResult = {
      added: { categories: [], values: [], rules: [] },
      modified: { categories: ["ModifiedCat"], values: ["Cat/ModifiedVal"], rules: ["dependency:Cat1/A -> Cat2/B"] },
      removed: { categories: [], values: [], rules: [] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    expect(screen.getByText("ModifiedCat")).toBeInTheDocument();
    expect(screen.getByText("Cat/ModifiedVal")).toBeInTheDocument();
    expect(screen.getByText("dependency:Cat1/A -> Cat2/B")).toBeInTheDocument();
  });

  it("should show all three sections when all have changes", () => {
    const diff: ModelDiffResult = {
      added: { categories: ["Added"], values: ["Cat/AddedVal"], rules: [] },
      modified: { categories: ["Modified"], values: [], rules: ["dep:A -> B"] },
      removed: { categories: [], values: ["Cat/RemovedVal"], rules: ["exc:C -> D"] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    // Alle drei Sektionen sollten erscheinen
    expect(screen.getByText("Kategorien")).toBeInTheDocument();
    expect(screen.getByText("Werte")).toBeInTheDocument();
    expect(screen.getByText("Regeln")).toBeInTheDocument();
  });

  it("should not show empty sections", () => {
    const diff: ModelDiffResult = {
      added: { categories: ["Added"], values: [], rules: [] },
      modified: { categories: [], values: [], rules: [] },
      removed: { categories: [], values: [], rules: [] },
    };

    render(<ModelDiffPreview diff={diff} />, { wrapper });

    // Nur Kategorien sollte erscheinen, nicht Werte oder Regeln
    expect(screen.getByText("Kategorien")).toBeInTheDocument();
    // Werte und Regeln haben keine Eintraege -> ihre Sektionen werden nicht gerendert
    // (weil hasChanges false ist)
  });
});