// REQ-3041: Tests fuer NumberlineVisualization-Komponente
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { NumberlineVisualization } from "../NumberlineVisualization";
import type { BVAPoint } from "../../../lib/bva-calc";

describe("NumberlineVisualization", () => {
  it("rendert SVG-Element", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "20", type: "boundary", label: "max" },
    ];
    const { container } = render(<NumberlineVisualization points={points} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("rendert Linie", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "20", type: "boundary", label: "max" },
    ];
    const { container } = render(<NumberlineVisualization points={points} />);
    const line = container.querySelector("line");
    expect(line).toBeInTheDocument();
  });

  it("rendert Marker fuer jeden Punkt", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "15", type: "inside", label: "mid" },
      { value: "20", type: "boundary", label: "max" },
    ];
    const { container } = render(<NumberlineVisualization points={points} />);
    const circles = container.querySelectorAll("circle");
    expect(circles).toHaveLength(3);
  });

  it("rendert Labels unterhalb der Marker", () => {
    const points: BVAPoint[] = [
      { value: "10", type: "boundary", label: "min" },
      { value: "20", type: "boundary", label: "max" },
    ];
    const { container } = render(<NumberlineVisualization points={points} />);
    const texts = container.querySelectorAll("text");
    expect(texts.length).toBeGreaterThanOrEqual(2);
  });

  it("behandelt leere Liste", () => {
    const { container } = render(<NumberlineVisualization points={[]} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    const circles = container.querySelectorAll("circle");
    expect(circles).toHaveLength(0);
  });

  it("behandelt einzelnen Punkt", () => {
    const points: BVAPoint[] = [
      { value: "42", type: "boundary", label: "single" },
    ];
    const { container } = render(<NumberlineVisualization points={points} />);
    const circles = container.querySelectorAll("circle");
    expect(circles).toHaveLength(1);
  });
});
