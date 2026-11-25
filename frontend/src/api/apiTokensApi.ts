// REQ-6012: API-Token-Verwaltung - API-Client

import client from './client';
export { expiresAtToDays } from '../lib/tokenExpiry';

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
  /** BUG A-04: Backend erwartet die Laufzeit in Tagen (1..365), kein Datum */
  expires_in_days: number;
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
  return client.get('/v1/api-tokens').then(r => r.data);
}

export function createToken(request: CreateTokenRequest): Promise<CreateTokenResponse> {
  return client.post('/v1/api-tokens', request).then(r => r.data);
}

export function revokeToken(id: number): Promise<void> {
  return client.delete(`/v1/api-tokens/${id}`).then(() => undefined);
}