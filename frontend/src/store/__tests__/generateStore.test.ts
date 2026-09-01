// REQ-4018: Der GenerateStore soll die konfigurierte Obergrenze fuer Testfaelle
// respektieren, indem sie als 'limit' an das Backend mitgeschickt wird.
import { renderHook, act } from '@testing-library/react';
import { useGenerateStore } from '../generateStore';
import { generateApi } from '../../api/client';

vi.mock('../../api/client', () => ({
  generateApi: {
    run: vi.fn(),
    getTestcases: vi.fn(),
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    updateAssignment: vi.fn(),
  },
}));

describe('generateStore respects the max-testcases setting (REQ-4018)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.mocked(generateApi.run).mockResolvedValue({ generation_id: 1, count: 1 });
    vi.mocked(generateApi.getTestcases).mockResolvedValue({
      testcases: [],
      risk_summary: { total_risk: 0, max_possible_risk: 0, risk_coverage_percent: 0, testcase_count: 0 },
      result_categories: [],
    });
    vi.mocked(generateApi.listGenerations).mockResolvedValue([]);
  });

  it('sends the default limit (1000) when no custom setting is stored', async () => {
    const { result } = renderHook(() => useGenerateStore());

    await act(async () => {
      await result.current.generate(1);
    });

    expect(generateApi.run).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ limit: 1000 })
    );
  });

  it('sends a custom limit from the Settings-Tab value', async () => {
    localStorage.setItem('great-max-testcases', '250');
    const { result } = renderHook(() => useGenerateStore());

    await act(async () => {
      await result.current.generate(1);
    });

    expect(generateApi.run).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ limit: 250 })
    );
  });
});

describe('generateStore uebernimmt riskSummary aus der API (REQ-3051)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.mocked(generateApi.run).mockResolvedValue({ generation_id: 42, count: 2 });
    vi.mocked(generateApi.listGenerations).mockResolvedValue([]);
  });

  it('setzt riskSummary nach generate() auf den Gesamtprozentsatz aus der API-Antwort', async () => {
    const apiRiskSummary = {
      total_risk: 8.0,
      max_possible_risk: 10.0,
      risk_coverage_percent: 80.0,
      testcase_count: 2,
    };
    vi.mocked(generateApi.getTestcases).mockResolvedValue({
      testcases: [],
      risk_summary: apiRiskSummary,
      result_categories: [],
    });

    const { result } = renderHook(() => useGenerateStore());

    await act(async () => {
      await result.current.generate(1);
    });

    expect(result.current.riskSummary).toEqual(apiRiskSummary);
  });

  it('setzt riskSummary nach loadGeneration() auf den Gesamtprozentsatz aus der API-Antwort', async () => {
    const apiRiskSummary = {
      total_risk: 3.0,
      max_possible_risk: 10.0,
      risk_coverage_percent: 30.0,
      testcase_count: 1,
    };
    vi.mocked(generateApi.getTestcases).mockResolvedValue({
      testcases: [],
      risk_summary: apiRiskSummary,
      result_categories: [],
    });

    const { result } = renderHook(() => useGenerateStore());

    await act(async () => {
      await result.current.loadGeneration(7);
    });

    expect(result.current.riskSummary).toEqual(apiRiskSummary);
  });

  it('setzt riskSummary bei einem neuen generate()-Aufruf zunaechst zurueck auf null', async () => {
    vi.mocked(generateApi.getTestcases).mockResolvedValue({
      testcases: [],
      risk_summary: { total_risk: 5, max_possible_risk: 10, risk_coverage_percent: 50, testcase_count: 1 },
      result_categories: [],
    });

    const { result } = renderHook(() => useGenerateStore());

    await act(async () => {
      await result.current.generate(1);
    });
    expect(result.current.riskSummary).not.toBeNull();

    // Zweiter Aufruf blockiert vor Abschluss des Promise noch beim Reset auf null.
    let pendingResolve!: (value: unknown) => void;
    vi.mocked(generateApi.getTestcases).mockReturnValue(
      new Promise((resolve) => {
        pendingResolve = resolve;
      }) as ReturnType<typeof generateApi.getTestcases>
    );

    let generatePromise!: Promise<void>;
    act(() => {
      generatePromise = result.current.generate(1);
    });

    expect(result.current.riskSummary).toBeNull();

    await act(async () => {
      pendingResolve({
        testcases: [],
        risk_summary: { total_risk: 1, max_possible_risk: 10, risk_coverage_percent: 10, testcase_count: 1 },
        result_categories: [],
      });
      await generatePromise;
    });
  });
});
