// REQ-3041: API-Wrapper fuer BVA-Endpoint
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
};
