// B-42: Tests fuer ApiError-Klasse
import { describe, it, expect } from 'vitest';
import { ApiError } from '../ApiError';

describe('ApiError', () => {
  it('string detail', () => {
    const e = new ApiError(404, 'Nicht gefunden');
    expect(e.message).toBe('Nicht gefunden');
    expect(e.status).toBe(404);
  });

  it('array detail (422)', () => {
    const e = new ApiError(422, [{ msg: 'Field required' }]);
    expect(e.message).toBe('Field required');
  });

  it('array detail multiple', () => {
    const e = new ApiError(422, [{ msg: 'A' }, { msg: 'B' }]);
    expect(e.message).toBe('A; B');
  });

  it('object detail with .detail', () => {
    const e = new ApiError(500, { detail: 'Internal error' });
    expect(e.message).toBe('Internal error');
  });

  it('object detail with .message', () => {
    const e = new ApiError(500, { message: 'Internal' });
    expect(e.message).toBe('Internal');
  });

  it('network error (status 0)', () => {
    const e = new ApiError(0, 'network error');
    expect(e.message).toBe('Server nicht erreichbar');
  });

  it('unknown status', () => {
    const e = new ApiError(503, {});
    expect(e.message).toBe('Fehler (503)');
  });
});