// REQ-4024: Tests fuer AuditTooltip
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AuditTooltip from "../AuditTooltip";

describe("AuditTooltip - REQ-4024", () => {
  it("zeigt nichts wenn keine Daten vorhanden", () => {
    const { container } = render(
      <AuditTooltip entityType="Kategorie" />
    );
    // Die Komponente gibt null zurueck, also sollte nichts gerendert werden
    expect(container.firstChild).toBeNull();
  });

  it("zeigt entityType-Text wenn Daten vorhanden", () => {
    render(
      <AuditTooltip
        entityType="Kategorie"
        lastModifiedBy="admin"
        lastModifiedAt="2025-10-12T14:30:00"
      />
    );
    expect(screen.getByText("Kategorie")).toBeInTheDocument();
  });

  it("zeigt nur modifiedBy wenn nur das vorhanden ist", () => {
    render(
      <AuditTooltip
        entityType="Testfall"
        lastModifiedBy="max"
      />
    );
    expect(screen.getByText("Testfall")).toBeInTheDocument();
  });

  it("zeigt nur modifiedAt wenn nur das vorhanden ist", () => {
    render(
      <AuditTooltip
        entityType="Wert"
        lastModifiedAt="2025-10-12T14:30:00"
      />
    );
    expect(screen.getByText("Wert")).toBeInTheDocument();
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", () => {
    const { container } = render(
      <AuditTooltip
        entityType="Kategorie"
        lastModifiedBy="admin"
        lastModifiedAt="2025-10-12T14:30:00"
      />
    );
    // Der Trigger sollte theme-tokens verwenden
    const trigger = container.querySelector(".text-theme-text-secondary");
    expect(trigger).not.toBeNull();
  });
});