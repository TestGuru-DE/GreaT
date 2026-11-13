// REQ-3045 (Sofort-Fix): SettingsPage enthaelt den ThemeSwitcher selbst - hier ist
// es besonders kritisch, dass die Seite dem Theme folgt, sonst wirkt ein
// Theme-Wechsel fuer den Nutzer "wirkungslos". Vor dem Fix nutzte die Seite
// hartkodierte "bg-white dark:bg-slate-800" / "text-slate-800" Klassen, die von
// der Theme-Engine (Klasse "theme-*" statt "dark") nie erreicht werden.
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import SettingsPage from "../SettingsPage";

vi.mock("../../components/PortSettingsCard", () => ({
  PortSettingsCard: () => <div data-testid="port-settings-mock" />,
}));
vi.mock("../../components/MaxTestCasesSettingsCard", () => ({
  MaxTestCasesSettingsCard: () => <div data-testid="max-testcases-mock" />,
}));

describe("SettingsPage - REQ-3045 Theme-Tokens statt hartkodierter Light-Farben", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ imported: false }) }) as unknown as typeof fetch;
  });

  it("Ueberschrift nutzt Theme-Text-Token statt hartkodiertem text-slate-800", () => {
    const { container } = render(<SettingsPage />);
    const heading = container.querySelector("h1");
    expect(heading).not.toBeNull();
    expect(heading!.className).not.toMatch(/\btext-slate-800\b/);
    expect(heading!.className).toMatch(/\btext-theme-text\b/);
  });

  it('"Erscheinungsbild"-Sektion (ThemeSwitcher-Container) nutzt Theme-Surface-Token statt bg-white', () => {
    const { getByText } = render(<SettingsPage />);
    const sectionHeading = getByText("Erscheinungsbild");
    const section = sectionHeading.closest("section")!;
    expect(section.className).not.toMatch(/\bbg-white\b/);
    expect(section.className).toMatch(/\bbg-theme-surface\b/);
  });
});
