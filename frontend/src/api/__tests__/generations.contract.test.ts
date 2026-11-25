// BUG R-03: GET /projects/{id}/generations liefert eine Liste.
import { describe, it, expect, vi } from 'vitest';

const get = vi.fn();
vi.mock('axios', () => {
  const instance = {
    get: (...a: unknown[]) => get(...a),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    defaults: { headers: { common: {} } },
  };
  return { default: { create: () => instance, isAxiosError: () => false }, create: () => instance };
});

import { generateApi } from '../client';

describe('Generierungshistorie (R-03)', () => {
  it('liest die Liste direkt', async () => {
    get.mockResolvedValueOnce({ data: [{ id: 1 }] });
    expect(await generateApi.listGenerations(3)).toEqual([{ id: 1 }]);
    expect(get).toHaveBeenCalledWith('/projects/3/generations');
  });

  it('toleriert das alte Objektformat', async () => {
    get.mockResolvedValueOnce({ data: { generations: [{ id: 2 }] } });
    expect(await generateApi.listGenerations(3)).toEqual([{ id: 2 }]);
  });
});
