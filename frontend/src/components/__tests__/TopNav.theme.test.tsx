// REQ-3045: Theme-System - TopNav ist auf JEDER Seite sichtbar (auch Projektansicht) und
// muss deshalb Theme-Tokens statt hartkodiertem bg-white / dark:-Varianten nutzen.
// Das Theme-System setzt "theme-dark" (nicht "dark") auf <html>, daher greifen
// Tailwind "dark:"-Klassen bei diesem class-Namensschema NIE.
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import TopNav from "../TopNav";

describe("TopNav - REQ-3045 Theme-Frame", () => {
  it("Header nutzt Theme-Token statt hartkodiertem bg-white", () => {
    const { container } = render(
      <MemoryRouter>
        <TopNav />
      </MemoryRouter>
    );
    const header = container.querySelector("header");
    expect(header).not.toBeNull();
    expect(header!.className).not.toMatch(/\bbg-white\b/);
    expect(header!.className).toMatch(/\bbg-theme-(bg|surface)\b/);
  });

  it("Header verlaesst sich nicht auf wirkungslose dark:-Klassen", () => {
    const { container } = render(
      <MemoryRouter>
        <TopNav />
      </MemoryRouter>
    );
    const header = container.querySelector("header");
    expect(header!.className).not.toMatch(/\bdark:bg-slate-900\b/);
  });
});
