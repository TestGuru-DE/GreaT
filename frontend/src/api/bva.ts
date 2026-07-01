// REQ-3041: API-Wrapper fuer BVA-Endpoint
import api from "./client";

export interface BVARequest {
  min_val: number;
  max_val: number;
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
};
