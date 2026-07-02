// REQ-1203: TypeScript-Interfaces fuer alle Pydantic-Schemas

export interface Project {
  id: number;
  name: string;
}

export interface ProjectCreate {
  name: string;
}

export interface Category {
  id: number;
  name: string;
  order_index: number;
}

export interface CategoryCreate {
  name: string;
  order_index?: number;
}

export interface Value {
  id: number;
  value: string;
  risk_weight: number;
  vtype: string;       // REQ-3007
  allowed: boolean;    // REQ-3007 (Fehlerwert = !allowed)
  is_default: boolean; // REQ-3008
}

export interface ValueCreate {
  value: string;
  risk_weight?: number;
}

export interface GenerateRequest {
  strategy: "each" | "linear" | "all" | "pairwise" | "risk_based" | "t_wise" | "mcdc";
  limit?: number;
  apply_rules?: boolean;  // REQ-3005
  t_strength?: number;     // BUG-3: T-Wise Stärke (default 2)
}

export interface GenerateResponse {
  generation_id: number;
  count: number;
}

export interface TestCaseOut {
  name: string;
  assignments: Record<string, string>;
  _has_error_value?: boolean; // REQ-3063: Flag für Fehlerwert-Markierung
  risk_coverage?: number;      // REQ-3050: Risikoabdeckung (Summe risk_weight)
}

// REQ-3051: Risikoabdeckungs-Zusammenfassung
export interface RiskSummary {
  total_risk: number;
  max_possible_risk: number;
  risk_coverage_percent: number;
  testcase_count: number;
}

export type Strategy = "each" | "linear" | "all" | "pairwise" | "risk_based" | "t_wise" | "mcdc";
