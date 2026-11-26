// REQ-6006 / BUG C-20: Export des Klassifikationsbaums
import { describe, expect, it } from "vitest";
import { buildExportSvg } from "../classificationTreeExport";

function svgFixture(): SVGSVGElement {
  const host = document.createElement("div");
  host.innerHTML = `
    <svg viewBox="0 0 400 300" width="800" height="600" class="x" style="color:red">
      <rect data-part="background" x="0" y="0" width="400" height="300" fill="#ffffff"/>
      <g data-part="tree"><rect x="1" y="1" width="10" height="10" fill="#312e81"/>
        <rect data-export="skip" x="0" y="0" width="12" height="12" fill="none"/></g>
      <g data-part="matrix"><circle cx="5" cy="200" r="5" fill="#0f172a"/></g>
    </svg>`;
  return host.querySelector("svg") as unknown as SVGSVGElement;
}

describe("buildExportSvg", () => {
  it("erzeugt ein eigenstaendiges SVG mit Namensraum (frueher ungueltig ohne xmlns)", () => {
    const text = buildExportSvg(svgFixture(), { withMatrix: true, treeHeight: 120 });
    expect(text.startsWith('<?xml version="1.0" encoding="UTF-8"?>')).toBe(true);
    const doc = new DOMParser().parseFromString(text, "image/svg+xml");
    expect(doc.getElementsByTagName("parsererror")).toHaveLength(0);
    expect(doc.documentElement.namespaceURI).toBe("http://www.w3.org/2000/svg");
    expect(doc.documentElement.getAttribute("width")).toBe("400");
    expect(doc.documentElement.hasAttribute("class")).toBe(false);
  });

  it("enthaelt die Matrix nur auf Wunsch und entfernt Bedienelemente", () => {
    const withMatrix = buildExportSvg(svgFixture(), { withMatrix: true, treeHeight: 120 });
    const withoutMatrix = buildExportSvg(svgFixture(), { withMatrix: false, treeHeight: 120 });
    expect(withMatrix).toContain("<circle");
    expect(withoutMatrix).not.toContain("<circle");
    expect(withoutMatrix).toContain('viewBox="0 0 400 136"');
    expect(withMatrix).not.toContain("data-export");
  });
});
