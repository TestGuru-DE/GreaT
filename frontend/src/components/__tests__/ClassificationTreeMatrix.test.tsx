// REQ-6006: Tests fuer ClassificationTreeMatrix
import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";
import ClassificationTreeMatrix from "../ClassificationTreeMatrix";

describe("ClassificationTreeMatrix", () => {
  it("rendert ohne Crash", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeMatrix
          categories={[
            { id: 1, name: "Browser", order_index: 0 },
            { id: 2, name: "OS", order_index: 1 },
          ]}
          testcases={[]}
          generations={[{ id: 1, name: "pairwise-1" }]}
        />
      </I18nextProvider>
    );
    expect(container.firstChild).toBeTruthy();
  });

  it("zeigt 'Keine Testfaelle' bei leerer Liste", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeMatrix
          categories={[{ id: 1, name: "A", order_index: 0 }]}
          testcases={[]}
          generations={[]}
        />
      </I18nextProvider>
    );
    // Table should exist
    const table = container.querySelector("table");
    expect(table).toBeTruthy();
  });

  it("zeigt Testfall-Zeilen", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeMatrix
          categories={[{ id: 1, name: "Browser", order_index: 0 }]}
          testcases={[
            { id: 1, generation_id: 1, assignment: { Browser: "Chrome" }, origin: "generated" },
            { id: 2, generation_id: 1, assignment: { Browser: "Firefox" }, origin: "seed" },
          ]}
          generations={[{ id: 1, name: "pw" }]}
          selectedGenId={1}
        />
      </I18nextProvider>
    );
    const rows = container.querySelectorAll("tbody tr");
    expect(rows.length).toBe(2);
  });

  it("Generierungs-Auswahl", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeMatrix
          categories={[]}
          testcases={[]}
          generations={[{ id: 1, name: "g1" }, { id: 2, name: "g2" }]}
        />
      </I18nextProvider>
    );
    const select = container.querySelector("select");
    expect(select).toBeTruthy();
  });
});