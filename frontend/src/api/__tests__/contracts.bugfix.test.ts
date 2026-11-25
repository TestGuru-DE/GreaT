// BUG R-02/C-01, C-03, A-04: Vertraege zwischen Frontend-API-Clients und Backend.
// Diese Fehler entstanden, weil Feldnamen und Pfade zwischen Frontend und Backend
// auseinanderliefen (Unit-Tests mit Mocks hatten das nicht bemerkt).
import { describe, it, expect, vi, beforeEach } from 'vitest';

const post = vi.fn();
const get = vi.fn();
const del = vi.fn();

vi.mock('../client', () => ({
  default: { post: (...a: unknown[]) => post(...a), get: (...a: unknown[]) => get(...a), delete: (...a: unknown[]) => del(...a) },
}));

import { bvaApi } from '../bva';
import { createToken, listTokens, revokeToken } from '../apiTokensApi';
import { expiresAtToDays } from '../../lib/tokenExpiry';

beforeEach(() => {
  post.mockReset(); get.mockReset(); del.mockReset();
});

describe('BVA-Vertrag (R-02/C-01)', () => {
  it('Zahlen-BVA sendet min_val/max_val in snake_case an /bva/ranges', async () => {
    post.mockResolvedValue({ data: { values: ['0', '1'] } });
    await bvaApi.generateMultiRange(7, {
      points: 2,
      ranges: [{ minVal: '1', maxVal: '100', allowed: true }],
    });
    expect(post).toHaveBeenCalledWith('/categories/7/bva/ranges', {
      points: 2,
      ranges: [{ min_val: '1', max_val: '100', allowed: true }],
    });
  });

  it('Erweiterte BVA liest das Feld "values" der Backend-Antwort (C-03)', async () => {
    post.mockResolvedValue({ data: { category_id: 7, values: [{ value: 'a', is_error: false, vtype: 'string', label: '' }] } });
    const res = await bvaApi.generateExtended(7, {
      type: 'strlen',
      points: 2,
      ranges: [{ min_val: '1', max_val: '3', allowed: true }],
    });
    expect(res.values.map((v) => v.value)).toEqual(['a']);
  });
});

describe('API-Token-Vertrag (A-04)', () => {
  it('Pfade ohne doppeltes /api (Client hat baseURL /api)', async () => {
    get.mockResolvedValue({ data: [] });
    post.mockResolvedValue({ data: {} });
    del.mockResolvedValue({});
    await listTokens();
    await createToken({ name: 'x', expires_in_days: 30, scopes: ['projects:read'] });
    await revokeToken(5);
    expect(get).toHaveBeenCalledWith('/v1/api-tokens');
    expect(post.mock.calls[0][0]).toBe('/v1/api-tokens');
    expect(del).toHaveBeenCalledWith('/v1/api-tokens/5');
  });

  it('sendet expires_in_days statt expires_at', async () => {
    post.mockResolvedValue({ data: {} });
    await createToken({ name: 'x', expires_in_days: 30, scopes: [] });
    expect(post.mock.calls[0][1]).toEqual({ name: 'x', expires_in_days: 30, scopes: [] });
  });

  it('expiresAtToDays rechnet ein Datum in Tage um (1..365)', () => {
    const today = new Date('2026-11-25T10:00:00');
    expect(expiresAtToDays('2026-12-25', today)).toBe(30);
    expect(expiresAtToDays('2026-11-25', today)).toBe(1);
    expect(expiresAtToDays('2030-01-01', today)).toBe(365);
  });
});
