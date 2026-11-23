// REQ-6006: Layout-Berechnung fuer Klassifikationsbaum (SVG)

export interface TreeNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  type: "root" | "category" | "value";
  categoryId?: number;
  value?: string;
  isError?: boolean;
  isDefault?: boolean;
  isResult?: boolean;
}

export interface LayoutResult {
  nodes: TreeNode[];
  totalWidth: number;
  totalHeight: number;
}

interface LayoutCategory {
  id: number;
  name: string;
  isResult?: boolean;
  values: LayoutValue[];
}

interface LayoutValue {
  name: string;
  isError?: boolean;
  isDefault?: boolean;
}

const ROOT_HEIGHT = 40;
const CATEGORY_HEIGHT = 36;
const VALUE_HEIGHT = 28;
const NODE_WIDTH = 120;
const H_GAP = 20;
const V_GAP = 12;
const ROOT_TO_CATS_GAP = 24;
const CAT_TO_VALUES_GAP = 16;

export function computeTreeLayout(
  projectName: string,
  categories: LayoutCategory[],
  cellWidth?: number,
  cellHeight?: number,
): LayoutResult {
  const cw = cellWidth ?? NODE_WIDTH;
  const ch = cellHeight ?? VALUE_HEIGHT;

  const nodes: TreeNode[] = [];
  let curX = 0;

  // 1. Root node (project name) - position first, center later
  const rootWidth = Math.max(cw, Math.min(300, projectName.length * 9 + 40));
  nodes.push({
    id: "root",
    x: 0,
    y: 0,
    width: rootWidth,
    height: ROOT_HEIGHT,
    label: projectName,
    type: "root",
  });

  // 2. Compute category column widths
  const catWidths: number[] = [];
  for (const cat of categories) {
    const maxValLen = cat.values.reduce((m, v) => Math.max(m, v.name.length), cat.name.length);
    const w = Math.max(cw, Math.min(200, maxValLen * 9 + 40));
    catWidths.push(w);
  }

  // 3. Place categories and values
  for (let ci = 0; ci < categories.length; ci++) {
    const cat = categories[ci];
    const w = catWidths[ci];

    // Category node
    nodes.push({
      id: `cat-${cat.id}`,
      x: curX,
      y: ROOT_HEIGHT + ROOT_TO_CATS_GAP,
      width: w,
      height: CATEGORY_HEIGHT,
      label: cat.name,
      type: "category",
      categoryId: cat.id,
      isResult: cat.isResult,
    });

    // Value nodes
    for (let vi = 0; vi < cat.values.length; vi++) {
      const val = cat.values[vi];
      nodes.push({
        id: `val-${cat.id}-${vi}`,
        x: curX,
        y: ROOT_HEIGHT + ROOT_TO_CATS_GAP + CATEGORY_HEIGHT + CAT_TO_VALUES_GAP + vi * (ch + V_GAP),
        width: w,
        height: ch,
        label: val.name,
        type: "value",
        categoryId: cat.id,
        value: val.name,
        isError: val.isError,
        isDefault: val.isDefault,
      });
    }

    curX += w + H_GAP;
  }

  // 4. Center root node
  const totalWidth = curX;
  nodes[0].x = (totalWidth - rootWidth) / 2;

  // 5. Compute total height
  const maxValCount = categories.reduce((m, c) => Math.max(m, c.values.length), 0);
  const totalHeight =
    ROOT_HEIGHT +
    ROOT_TO_CATS_GAP +
    CATEGORY_HEIGHT +
    CAT_TO_VALUES_GAP +
    maxValCount * (ch + V_GAP) -
    V_GAP;

  return { nodes, totalWidth, totalHeight };
}