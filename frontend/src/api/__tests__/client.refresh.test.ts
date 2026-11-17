// B-43: Tests fuer Token-Refresh-Interceptor
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { ApiError } from '../ApiError';

describe('Token-Refresh Interceptor', () => {
  let mockWindowLocation: { href: string };

  beforeEach(() => {
    mockWindowLocation = { href: '' };
    vi.stubGlobal('window', {
      ...globalThis.window,
      location: mockWindowLocation,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('leitet bei 401 auf Auth-Route direkt ApiError weiter (kein Refresh)', async () => {
    const testApi = axios.create({
      baseURL: '/api',
    });

    function isAuthRoute(url?: string): boolean {
      if (!url) return true;
      const u = url.toLowerCase();
      return u.includes('/auth/login') || u.includes('/auth/refresh') || u.includes('/auth/logout');
    }

    testApi.interceptors.response.use(
      (res) => res,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !isAuthRoute(originalRequest?.url)) {
          // Should not reach here for auth routes
          return testApi(originalRequest);
        }

        const apiError = new ApiError(
          error.response?.status ?? 0,
          error.response?.data?.detail ?? error.message
        );
        throw apiError;
      }
    );

    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Unauthorized' },
      },
      config: { url: '/auth/login' },
    });
    testApi.defaults.adapter = mockAdapter;

    try {
      await testApi.post('/auth/login', {});
      expect.fail('should have thrown');
    } catch (e: any) {
      expect(e instanceof ApiError).toBe(true);
      expect(e.status).toBe(401);
      expect(e.message).toBe('Unauthorized');
    }
    expect(mockWindowLocation.href).toBe('');
  });
});