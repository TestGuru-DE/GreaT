import { describe, it, expect, beforeEach } from 'vitest';
import {
  DEFAULT_MAX_TESTCASES,
  MAX_TESTCASES_STORAGE_KEY,
  parseMaxTestCases,
  readMaxTestCases,
  storeMaxTestCases,
} from '../maxTestCasesSetting';

describe('maxTestCasesSetting', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('parseMaxTestCases', () => {
    it('accepts a valid positive integer', () => {
      expect(parseMaxTestCases('500')).toBe(500);
    });

    it('rejects zero', () => {
      expect(parseMaxTestCases('0')).toBeNull();
    });

    it('rejects negative numbers', () => {
      expect(parseMaxTestCases('-1')).toBeNull();
    });

    it('rejects non-numeric input', () => {
      expect(parseMaxTestCases('abc')).toBeNull();
    });

    it('rejects decimals', () => {
      expect(parseMaxTestCases('10.5')).toBeNull();
    });

    it('rejects values above the sensible upper bound (100000)', () => {
      expect(parseMaxTestCases('100001')).toBeNull();
    });

    it('accepts the upper bound itself', () => {
      expect(parseMaxTestCases('100000')).toBe(100000);
    });
  });

  describe('readMaxTestCases', () => {
    it('returns the default (1000) when nothing is stored', () => {
      expect(readMaxTestCases()).toBe(DEFAULT_MAX_TESTCASES);
    });

    it('returns the stored value when valid', () => {
      localStorage.setItem(MAX_TESTCASES_STORAGE_KEY, '250');
      expect(readMaxTestCases()).toBe(250);
    });

    it('falls back to the default when the stored value is invalid (robust, no silent crash)', () => {
      localStorage.setItem(MAX_TESTCASES_STORAGE_KEY, 'not-a-number');
      expect(readMaxTestCases()).toBe(DEFAULT_MAX_TESTCASES);
    });
  });

  describe('storeMaxTestCases', () => {
    it('persists a valid value and returns it', () => {
      const result = storeMaxTestCases('2500');
      expect(result).toBe(2500);
      expect(localStorage.getItem(MAX_TESTCASES_STORAGE_KEY)).toBe('2500');
    });

    it('throws a descriptive error for invalid values instead of failing silently', () => {
      expect(() => storeMaxTestCases('-5')).toThrow(/zwischen/i);
      expect(localStorage.getItem(MAX_TESTCASES_STORAGE_KEY)).toBeNull();
    });
  });
});
