// REQ-6006 / BUG C-20: Export des Klassifikationsbaums als SVG und PNG,
// wahlweise mit oder ohne Testfallmatrix.
//
// Das SVG ist eigenstaendig: Namensraum gesetzt (frueher fehlte xmlns, Datei war kein
// gueltiges Bild), alle Farben und Schriften als Attribute (keine CSS-Klassen), weisser
// Hintergrund. Die Matrix liegt in <g data-part="matrix"> und wird bei Bedarf entfernt.

const SVG_NS = "http://www.w3.org/2000/svg";

export interface ExportOptions {
  withMatrix: boolean;
  /** Hoehe des Baums ohne Matrix (fuer den Export ohne Matrix) */
  treeHeight: number;
}

/** Baut den SVG-Text fuer den Export aus dem dargestellten SVG-Element. */
export function buildExportSvg(svg: SVGSVGElement, options: ExportOptions): string {
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const viewBox = (svg.getAttribute("viewBox") ?? "0 0 0 0").split(/\s+/).map(Number);
  const width = viewBox[2] || 0;
  let height = viewBox[3] || 0;

  // Bedienelemente (Auswahlrahmen, Eingabefelder) gehoeren nicht in den Export
  clone.querySelectorAll("[data-export='skip']").forEach((el) => el.remove());
  if (!options.withMatrix) {
    clone.querySelectorAll("[data-part='matrix']").forEach((el) => el.remove());
    height = options.treeHeight + 16;
  }
  // Namensraum genau einmal: der Serializer setzt ihn fuer SVG-Elemente selbst,
  // ein zusaetzliches xmlns-Attribut ergaebe ein doppeltes Attribut (ungueltiges XML).
  clone.removeAttribute("xmlns");
  if (clone.namespaceURI !== SVG_NS) clone.setAttribute("xmlns", SVG_NS);
  clone.setAttribute("version", "1.1");
  clone.setAttribute("viewBox", `0 0 ${width} ${height}`);
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  clone.removeAttribute("class");
  clone.removeAttribute("style");
  const background = clone.querySelector("[data-part='background']");
  background?.setAttribute("height", String(height));

  const xml = new XMLSerializer().serializeToString(clone);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${xml}`;
}

/** Rendert SVG-Text in ein PNG (doppelte Aufloesung fuer scharfe Ausdrucke). */
export function svgToPng(svgText: string, width: number, height: number, scale = 2): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(new Blob([svgText], { type: "image/svg+xml;charset=utf-8" }));
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(width * scale));
      canvas.height = Math.max(1, Math.round(height * scale));
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error("Canvas nicht verfuegbar"));
        return;
      }
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("PNG-Erzeugung fehlgeschlagen"))), "image/png");
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("SVG konnte nicht gerendert werden"));
    };
    img.src = url;
  });
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
