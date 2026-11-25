// REQ-3041, REQ-6007: API-Wrapper fuer BVA-Endpunkte
import api from "./client";

export interface BVARequest {
  min_val: number;
  max_val: number;
  points: 2 | 3 | 4;
  allowed?: boolean;
}

export interface BVARangeRequest {
  id: string;
  minVal: string;
  maxVal: string;
  allowed: boolean;
}

export interface BVAMultiRangeRequest {
  ranges: BVARangeRequest[];
  points: 2 | 3 | 4;
}

export interface BVAResponse {
  values: string[];
  category_id: number;
}

// REQ-6007: Erweiterte BVA-Typen
export type BVADataType = "number" | "date" | "time" | "datetime" | "strlen";

export interface BVAExtendedRange {
  min_val: string;
  max_val: string;
  allowed: boolean;
}

export interface BVAExtendedOptions {
  format?: string;       // "iso" | "de" fuer date; "HH:MM" | "HH:MM:SS" fuer time
  step?: string;         // "minute" | "second" fuer time/datetime
  charset?: string;      // "alpha" | "alnum" | "alpha_de" | "special" | "unicode" fuer strlen
  extras?: Record<string, boolean>;  // Typspezifische Zusatzwerte
}

export interface BVAExtendedRequest {
  type: BVADataType;
  ranges: BVAExtendedRange[];
  points: 2 | 3 | 4;
  options?: BVAExtendedOptions;
}

export interface BVAExtendedResult {
  value: string;
  is_error: boolean;
  vtype: string;
  label: string;
}

export interface BVAExtendedResponse {
  // BUG C-03: Backend liefert "values" (schemas.BVAExtendedResponse)
  values: BVAExtendedResult[];
  category_id: number;
}

export const bvaApi = {
  /**
   * Ruft Backend-Endpoint POST /api/categories/{cid}/bva auf.
   * Erzeugt Grenzwerte fuer eine Kategorie.
   */
  generate: async (
    categoryId: number,
    params: BVARequest
  ): Promise<BVAResponse> => {
    const response = await api.post<BVAResponse>(
      `/categories/${categoryId}/bva`,
      params
    );
    return response.data;
  },
  generateMultiRange: async (
    categoryId: number,
    params: BVAMultiRangeRequest
  ): Promise<BVAResponse> => {
    const payload = {
      points: params.points,
      // BUG R-02/C-01: Backend erwartet snake_case (min_val/max_val)
      ranges: params.ranges.map((range) => ({
        min_val: range.minVal,
        max_val: range.maxVal,
        allowed: range.allowed,
      })),
    };
    const response = await api.post<BVAResponse>(
      `/categories/${categoryId}/bva/ranges`,
      payload
    );
    return response.data;
  },

  // REQ-6007: Erweiterte BVA mit Datentypen
  generateExtended: async (
    categoryId: number,
    params: BVAExtendedRequest
  ): Promise<BVAExtendedResponse> => {
    const payload = {
      type: params.type,
      points: params.points,
      ranges: params.ranges.map((range) => ({
        min_val: range.min_val,
        max_val: range.max_val,
        allowed: range.allowed,
      })),
      options: params.options,
    };
    const response = await api.post<BVAExtendedResponse>(
      `/categories/${categoryId}/bva/extended`,
      payload
    );
    return response.data;
  },
};
