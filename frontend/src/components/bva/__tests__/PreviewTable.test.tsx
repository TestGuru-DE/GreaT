// REQ-3041: Tests fuer PreviewTable-Komponente
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PreviewTable } from "../PreviewTable";
import type { BVAPoint } from "../../../lib/bva-calc";

describe("PreviewTable", () => {
  it("rendert leere Tabelle wenn keine Punkte", () => {
    render(<PreviewTable points={[]} markAsErrorCase={false} />);
    expect(screen.getByText(/Keine Vorschau/i)).toBeInTheDocument();
  });

  it("rendert Spaltenköpfe", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
    ];
    render(<PreviewTable points={points} markAsErrorCase={false} />);
    expect(screen.getByText("Wert")).toBeInTheDocument();
    expect(screen.getByText("Typ")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("rendert Werte korrekt", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "15", type: "inside", label: "min+ε" },
      { value: "20", type: "boundary", label: "max" },
    ];
    render(<PreviewTable points={points} markAsErrorCase={false} />);
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("markiert alle als erlaubt wenn markAsErrorCase=false", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
    ];
    render(<PreviewTable points={points} markAsErrorCase={false} />);
    expect(screen.getByText("Erlaubt")).toBeInTheDocument();
  });

  it("markiert alle als Fehlerfall wenn markAsErrorCase=true", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
    ];
    render(<PreviewTable points={points} markAsErrorCase={true} />);
    expect(screen.getByText("Fehlerfall")).toBeInTheDocument();
  });

  it("zeigt Labels (min, min+ε, max)", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "11", type: "inside", label: "min+ε" },
    ];
    render(<PreviewTable points={points} markAsErrorCase={false} />);
    expect(screen.getByText("min")).toBeInTheDocument();
    expect(screen.getByText("min+ε")).toBeInTheDocument();
  });
});
