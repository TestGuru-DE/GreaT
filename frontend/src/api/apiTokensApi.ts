// REQ-6012: API-Token-Verwaltung - API-Client

import client from './client';

export interface ApiToken {
  id: number;
  name: string;
  prefix: string;
  scopes: string[];
  created_at: string;
  expires_at: string;
  last_used_at?: string;
  last_used_ip?: string;
  revoked_at?: string;
}

export interface CreateTokenRequest {
  name: string;
  expires_at: string;
  scopes: string[];
}

export interface CreateTokenResponse {
  token: string;
  id: number;
  name: string;
  prefix: string;
  scopes: string[];
  expires_at: string;
}

export function listTokens(): Promise<ApiToken[]> {
  return client.get('/api/v1/api-tokens').then(r => r.data);
}

export function createToken(request: CreateTokenRequest): Promise<CreateTokenResponse> {
  return client.post('/api/v1/api-tokens', request).then(r => r.data);
}

export function revokeToken(id: number): Promise<void> {
  return client.delete(`/api/v1/api-tokens/${id}`).then(() => undefined);
}