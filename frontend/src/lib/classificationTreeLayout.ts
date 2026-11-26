// REQ-6006: Layout-Berechnung fuer Klassifikationsbaum (SVG)
// REQ-6016: Hierarchische Klassen (Verfeinerung)
//
// BUG C-16: Klassische Notation – Klassen stehen NEBENEINANDER unter ihrer
// Klassifikation. Jede Klasse ist eine Spalte; die Testfallmatrix unter dem Baum
// nutzt dieselben Spalten (x/width), dadurch stehen die Punkte exakt unter den Klassen.

export interface TreeNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  type: "root" | "category" | "value";
  categoryId?: number;
  valueId?: number;
  value?: string;
  isError?: boolean;
  isDefault?: boolean;
  isResult?: boolean;
  // REQ-6016: Parent value ID for hierarchical refinement
  parentId?: number | null;
}

export interface TreeEdge {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Eine Klasse = eine Spalte (fuer Baum und Matrix). */
export interface TreeColumn {
  categoryId: number;
  categoryName: string;
  valueId?: number;
  value: string;
  x: number;
  width: number;
}

export interface LayoutResult {
  nodes: TreeNode[];
  edges: TreeEdge[];
  columns: TreeColumn[];
  totalWidth: number;
  /** Hoehe des Baums (ohne Matrix) */
  totalHeight: number;
}

export interface LayoutCategory {
  id: number;
  name: string;
  isResult?: boolean;
  values: LayoutValue[];
}

export interface LayoutValue {
  id?: number;
  name: string;
  isError?: boolean;
  isDefault?: boolean;
  // REQ-6016: Parent value ID for hierarchical refinement
  parentId?: number | null;
}

export const ROOT_HEIGHT = 40;
export const CATEGORY_HEIGHT = 44;
export const VALUE_HEIGHT = 44;
export const ROW_HEIGHT = 24;
const MIN_CLASS_WIDTH = 72;
const MAX_CLASS_WIDTH = 160;
const CHAR_WIDTH = 7;
const CLASS_GAP = 8;
const CATEGORY_GAP = 28;
const LEVEL_GAP = 32;
export const LEFT_MARGIN = 96; // Platz fuer Testfallnamen in der Matrix

function textWidth(label: string, min: number, max: number): number {
  return Math.max(min, Math.min(max, label.length * CHAR_WIDTH + 24));
}

export function computeTreeLayout(projectName: string, categories: LayoutCategory[]): LayoutResult {
  const nodes: TreeNode[] = [];
  const edges: TreeEdge[] = [];
  const columns: TreeColumn[] = [];

  const catY = ROOT_HEIGHT + LEVEL_GAP;
  const valY = catY + CATEGORY_HEIGHT + LEVEL_GAP;

  nodes.push({ id: "root", x: 0, y: 0, width: 0, height: ROOT_HEIGHT, label: projectName, type: "root" });

  let curX = categories.length ? LEFT_MARGIN : 0;
  for (const cat of categories) {
    const classWidths = cat.values.map((v) => textWidth(v.name, MIN_CLASS_WIDTH, MAX_CLASS_WIDTH));
    const classesWidth = classWidths.reduce((a, b) => a + b, 0) + CLASS_GAP * Math.max(0, classWidths.length - 1);
    const catWidth = Math.max(textWidth(cat.name, MIN_CLASS_WIDTH, 2 * MAX_CLASS_WIDTH), classesWidth);
    const catNode: TreeNode = {
      id: `cat-${cat.id}`, x: curX, y: catY, width: catWidth, height: CATEGORY_HEIGHT,
      label: cat.name, type: "category", categoryId: cat.id, isResult: cat.isResult,
    };
    nodes.push(catNode);

    // Klassen unter der Klassifikation zentrieren
    let classX = curX + (catWidth - classesWidth) / 2;
    cat.values.forEach((val, vi) => {
      const w = classWidths[vi];
      nodes.push({
        id: `val-${cat.id}-${val.id ?? vi}`, x: classX, y: valY, width: w, height: VALUE_HEIGHT,
        label: val.name, type: "value", categoryId: cat.id, valueId: val.id, value: val.name,
        isError: val.isError, isDefault: val.isDefault, parentId: val.parentId ?? null,
      });
      columns.push({ categoryId: cat.id, categoryName: cat.name, valueId: val.id, value: val.name, x: classX, width: w });
      edges.push({ x1: curX + catWidth / 2, y1: catY + CATEGORY_HEIGHT, x2: classX + w / 2, y2: valY });
      classX += w + CLASS_GAP;
    });
    curX += catWidth + CATEGORY_GAP;
  }

  const totalWidth = categories.length ? curX - CATEGORY_GAP + 16 : 0;
  const rootWidth = textWidth(projectName, 120, 320);
  const root = nodes[0];
  root.width = rootWidth;
  root.x = Math.max(0, (Math.max(totalWidth, rootWidth) - rootWidth) / 2);
  for (const n of nodes) {
    if (n.type === "category") {
      edges.push({ x1: root.x + rootWidth / 2, y1: ROOT_HEIGHT, x2: n.x + n.width / 2, y2: catY });
    }
  }

  const hasValues = categories.some((c) => c.values.length > 0);
  const totalHeight = categories.length === 0 ? ROOT_HEIGHT : hasValues ? valY + VALUE_HEIGHT : catY + CATEGORY_HEIGHT;
  return { nodes, edges, columns, totalWidth: Math.max(totalWidth, categories.length ? rootWidth : 0), totalHeight };
}
