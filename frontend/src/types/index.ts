// REQ-1203: TypeScript-Interfaces fuer alle Pydantic-Schemas

export interface Project {
  id: number;
  name: string;
  version?: number; // REQ-4021
}

export interface ProjectCreate {
  name: string;
}

// REQ-5002: Kategorie-Typ (standard, cause = Ursache, effect = Wirkung)
export type CategoryType = "standard" | "cause" | "effect";

export interface Category {
  id: number;
  name: string;
  order_index: number;
  is_result?: boolean;  // REQ-4016: Ergebnis-Kategorie (Expected Result)
  category_type?: CategoryType; // REQ-5002
}

export interface CategoryCreate {
  name: string;
  order_index?: number;
  is_result?: boolean;  // REQ-4016
  category_type?: CategoryType; // REQ-5002
}

// REQ-5003/5005: Entscheidungstabelle (Antwort von POST /api/decision-table/generate)
export interface DecisionTableCause {
  id: number;
  name: string;
  values?: string[];
}

export interface DecisionTableEffect {
  id: number;
  name: string;
  values?: string[];
}

export interface DecisionTableRow {
  id: number;
  causes: Record<string, string>;
  effects: Record<string, string | null>;
}

export interface DecisionTableGenerateResponse {
  causes: DecisionTableCause[];
  effects: DecisionTableEffect[];
  rules: DecisionTableRow[];
  total_rules: number;
  rules_after_constraints?: number;
}

export interface Value {
  id: number;
  value: string;
  risk_weight: number;
  vtype: string;       // REQ-3007
  allowed: boolean;    // REQ-3007 (Fehlerwert = !allowed)
  is_default: boolean; // REQ-3008
  parent_value_id?: number | null; // REQ-6016
}

export interface ValueCreate {
  value: string;
  risk_weight?: number;
  parent_value_id?: number | null; // REQ-6016
}

export interface GenerateRequest {
  strategy: "each" | "linear" | "all" | "pairwise" | "risk_based" | "t_wise" | "mcdc";
  limit?: number;
  apply_rules?: boolean;  // REQ-3005
  t_strength?: number;     // BUG-3: T-Wise Stärke (default 2)
  seed_set_id?: number;    // REQ-6009 / BUG K-09: Seed-Satz als Startpunkt
}

export interface GenerateResponse {
  generation_id: number;
  count: number;
  warnings?: string[];     // BUG R-05: z. B. nicht angewendete Constraints
  seeds_count?: number;
  supplemented_count?: number;
}

export interface TestCaseOut {
  id: number;
  name: string;
  assignments: Record<string, string>;
  has_error_value?: boolean; // REQ-3063: Flag für Fehlerwert-Markierung
  risk_coverage?: number;      // REQ-3050: Risikoabdeckung (Summe risk_weight)
  origin?: string | null;      // REQ-6009: "seed" | "supplemented" | "generated"
  filled_categories?: string[]; // Restbefund 9c: von der Generierung aufgefuellte Seed-Felder
}

export interface ResultCategoryValue {
  id: number;
  value: string;
}

export interface ResultCategory {
  id: number;
  name: string;
  editable: boolean;
  values: ResultCategoryValue[];
}

// REQ-3051: Risikoabdeckungs-Zusammenfassung
export interface RiskSummary {
  total_risk: number;
  max_possible_risk: number;
  risk_coverage_percent: number;
  testcase_count: number;
}

export type Strategy = "each" | "linear" | "all" | "pairwise" | "risk_based" | "t_wise" | "mcdc";

// REQ-4018: Hierarchische Datenklassen
export interface DataNodeValue {
  id: number;
  node_id: number;
  value: string;
  sort_order: number;
}

export interface DataNode {
  id: number;
  name: string;
  parent_id: number | null;
  is_system: boolean;
  source: string | null;
  sort_order: number;
  values: DataNodeValue[];
  children: DataNode[];
}

// REQ-6001: Logische Constraints (ADR-020 AST-Format)
export type ConstraintKind = "forbid" | "implies";
export type ConstraintOp = "eq" | "ne" | "in" | "not_in" | "and" | "or" | "not";

export interface ConstraintAtom {
  op: "eq" | "ne" | "in" | "not_in";
  category_id: number;
  value_id: number;
  value_ids?: number[]; // for in / not_in
}

export interface ConstraintGroup {
  op: "and" | "or";
  args: (ConstraintAtom | ConstraintGroup | ConstraintNot)[];
}

export interface ConstraintNot {
  op: "not";
  arg: ConstraintNode;
}

export type ConstraintNode = ConstraintAtom | ConstraintGroup | ConstraintNot;

export interface LogicalConstraint {
  id: number;
  project_id: number;
  name: string;
  kind: ConstraintKind;
  expression: ConstraintNode;
  consequence?: ConstraintNode; // only for "implies"
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// REQ-6008: Coverage Types
// ============================================================================

export interface CoverageStat {
  t: number;
  covered: number;
  possible: number;
  percentage: number;
  excluded_by_rules: number;
}

export interface HeatmapPair {
  cat_a: string;
  cat_b: string;
  coverage_pct: number;
  covered: number;
  possible: number;
}

export interface HeatmapOverview {
  categories: string[];
  pairs: HeatmapPair[];
}

export interface UncoveredTuple {
  categories: string[];
  values: string[];
}

export interface CoverageResponse {
  generation_id: number;
  coverage_1wise: CoverageStat;
  coverage_2wise: CoverageStat;
  coverage_3wise?: CoverageStat | null;
  heatmap: HeatmapOverview;
  uncovered_tuples_2wise: UncoveredTuple[];
  cached: boolean;
}

export interface HeatmapCellData {
  count: number;
  status: "covered" | "uncovered" | "excluded";
  testcase_ids: number[];
}

export interface HeatmapResponse {
  cat_a: string;
  cat_b: string;
  rows: string[];
  cols: string[];
  cells: Record<string, HeatmapCellData>;
}

// ============================================================================
// REQ-6009: Seed Types
// ============================================================================

/** Einzelner Seed-Testfall (Assignment als JSON, null = "any") */
export interface SeedCase {
  id: number;
  assignment: Record<string, string | null>;
  order_index: number;
}

/** Seed-Satz zum Erstellen */
export interface SeedSetCreate {
  name: string;
  seeds: Record<string, string | null>[];
}

/** Seed-Satz zum Aktualisieren (teilweise) */
export interface SeedSetUpdate {
  name?: string;
  seeds?: Record<string, string | null>[];
}

/** Seed-Satz (vollstaendig mit SeedCases) */
export interface SeedSet {
  id: number;
  project_id: number;
  name: string;
  created_at: string;
  updated_at: string;
  seed_count: number;
  seed_cases: SeedCase[];
}

/** Kurzinfo fuer Uebersicht */
export interface SeedSetList {
  id: number;
  name: string;
  seed_count: number;
  created_at: string;
}

/** Antwort nach CSV-Import */
export interface SeedCSVImportResponse {
  id: number;
  name: string;
  seed_count: number;
  warnings: string[];
}

/** Antwort nach Seed-Generierung */
export interface SeedGenerateResponse {
  generation_id: number;
  count: number;
  seeds_count: number;
  supplemented_count: number;
  coverage_before: number;
  coverage_after: number;
  warnings: string[];
  report: Record<string, unknown>;
}

/** Lueckenschluss-Request */
export interface GapFillRequest {
  strategy: string;
  t_strength?: number;
  apply_rules?: boolean;
}

/** Antwort nach Lueckenschluss */
export interface GapFillResponse {
  new_generation_id: number;
  old_generation_id: number;
  seed_count: number;
  supplemented_count: number;
  total_testcases: number;
  coverage_before: number;
  coverage_after: number;
  impossible_tuples: unknown[][];
  warnings: string[];
}

// ============================================================================
// REQ-6016: Hierarchische Klassen (Verfeinerung)
// ============================================================================

export interface HierarchyNode {
  id: number;
  value: string;
  children: HierarchyNode[];
}

export interface CategoryHierarchyResponse {
  category_id: number;
  category_name: string;
  roots: HierarchyNode[];
}
