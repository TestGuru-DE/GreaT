// REQ-6009: Unit-Tests fuer seedStore (Zustand)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSeedStore } from "../seedStore";
import * as clientModule from "../../api/client";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<ReturnType<typeof import("../../api/client")>>();
  return {
    ...actual,
    seedApi: {
      list: vi.fn(),
      create: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      importCsv: vi.fn(),
      gapFill: vi.fn(),
    },
  };
});

const seedApi = clientModule.seedApi as {
  list: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  importCsv: ReturnType<typeof vi.fn>;
  gapFill: ReturnType<typeof vi.fn>;
};

describe("REQ-6009: seedStore", () => {
  const mockSeedSetList = [
    { id: 1, name: "Set A", seed_count: 3, created_at: "2026-01-01T00:00:00Z" },
    { id: 2, name: "Set B", seed_count: 5, created_at: "2026-02-01T00:00:00Z" },
  ];

  const mockSeedSet = {
    id: 1,
    project_id: 1,
    name: "Set A",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    seed_count: 2,
    seed_cases: [
      { id: 1, assignment: { Browser: "Chrome", OS: "Windows" }, order_index: 0 },
      { id: 2, assignment: { Browser: "Firefox", OS: "Linux" }, order_index: 1 },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset store state
    useSeedStore.setState({
      seedSets: [],
      currentSet: null,
      loading: false,
      error: null,
      msg: null,
    });

    // Default API responses
    seedApi.list.mockResolvedValue(mockSeedSetList);
    seedApi.get.mockResolvedValue(mockSeedSet);
    seedApi.create.mockResolvedValue({ id: 3, name: "New Set", seed_count: 0, warnings: [] });
    seedApi.update.mockResolvedValue({ id: 1, name: "Set A", seed_count: 2, warnings: [] });
    seedApi.delete.mockResolvedValue(undefined);
    seedApi.importCsv.mockResolvedValue({ id: 4, name: "Imported", seed_count: 5, warnings: [] });
    seedApi.gapFill.mockResolvedValue({
      new_generation_id: 10,
      old_generation_id: 9,
      seed_count: 5,
      supplemented_count: 3,
      total_testcases: 20,
      coverage_before: 75,
      coverage_after: 95,
      impossible_tuples: [],
      warnings: [],
    });
  });

  describe("fetchSeedSets", () => {
    it("laedt Seed-Saetze und setzt loading=false", async () => {
      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.fetchSeedSets(1);
      });

      expect(seedApi.list).toHaveBeenCalledWith(1);
      expect(result.current.seedSets).toEqual(mockSeedSetList);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("setzt error bei API-Fehler", async () => {
      seedApi.list.mockRejectedValueOnce(new Error("Network Error"));

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.fetchSeedSets(1);
      });

      // String(error) gives "Error: Network Error"
      expect(result.current.error).toContain("Network Error");
      expect(result.current.loading).toBe(false);
    });

    it("setzt loading=true waehrend des Ladens", async () => {
      let resolvePromise: (value: unknown) => void;
      seedApi.list.mockImplementationOnce(() =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useSeedStore());

      let fetchPromise: Promise<void>;
      act(() => {
        fetchPromise = result.current.fetchSeedSets(1);
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise!(mockSeedSetList);
        await fetchPromise;
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe("createSeedSet", () => {
    it("erstellt neuen Seed-Satz und aktualisiert Liste", async () => {
      const { result } = renderHook(() => useSeedStore());

      const res = await act(async () => {
        return await result.current.createSeedSet(1, { name: "New Set", seeds: [] });
      }) as any;

      expect(seedApi.create).toHaveBeenCalledWith(1, { name: "New Set", seeds: [] });
      expect(result.current.loading).toBe(false);
      expect(result.current.msg).toEqual({ text: "Seed-Satz erstellt", type: "ok" });
      expect(res).not.toBeNull();
      expect(res?.name).toBe("New Set");
    });

    it("zeigt Warnung bei create mit warnings", async () => {
      seedApi.create.mockResolvedValueOnce({
        id: 3,
        name: "New Set",
        seed_count: 0,
        warnings: ["Duplicate name"],
      });

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.createSeedSet(1, { name: "New Set", seeds: [] });
      });

      expect(result.current.msg).toEqual({ text: "Duplicate name", type: "warn" });
    });

    it("gibt null zurueck bei Fehler", async () => {
      seedApi.create.mockRejectedValueOnce(new Error("Server Error"));

      const { result } = renderHook(() => useSeedStore());

      let res: any;
      await act(async () => {
        res = await result.current.createSeedSet(1, { name: "New Set", seeds: [] });
      });

      expect(res).toBeNull();
      expect(result.current.error).toContain("Server Error");
    });
  });

  describe("loadSeedSet", () => {
    it("laedt Seed-Satz und setzt currentSet", async () => {
      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.loadSeedSet(1, 1);
      });

      expect(seedApi.get).toHaveBeenCalledWith(1, 1);
      expect(result.current.currentSet).toEqual(mockSeedSet);
      expect(result.current.loading).toBe(false);
    });

    it("setzt error bei API-Fehler", async () => {
      seedApi.get.mockRejectedValueOnce(new Error("Not found"));

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.loadSeedSet(1, 999);
      });

      expect(result.current.error).toContain("Not found");
      expect(result.current.loading).toBe(false);
    });
  });

  describe("updateSeedSet", () => {
    it("aktualisiert Seed-Satz und aktualisiert Detail + Liste", async () => {
      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.updateSeedSet(1, 1, { seeds: [{ Browser: "Safari" }] });
      });

      expect(seedApi.update).toHaveBeenCalledWith(1, 1, { seeds: [{ Browser: "Safari" }] });
      expect(result.current.loading).toBe(false);
      expect(result.current.msg).toEqual({ text: "Seed-Satz aktualisiert", type: "ok" });
    });

    it("setzt error bei API-Fehler", async () => {
      seedApi.update.mockRejectedValueOnce(new Error("Conflict"));

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.updateSeedSet(1, 1, { seeds: [] });
      });

      expect(result.current.error).toContain("Conflict");
      expect(result.current.loading).toBe(false);
    });
  });

  describe("deleteSeedSet", () => {
    it("loescht Seed-Satz und entfernt ihn aus der Liste", async () => {
      useSeedStore.setState({ seedSets: mockSeedSetList });

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.deleteSeedSet(1, 1);
      });

      expect(seedApi.delete).toHaveBeenCalledWith(1, 1);
      expect(result.current.seedSets).toHaveLength(1);
      expect(result.current.seedSets[0].id).toBe(2);
      expect(result.current.msg).toEqual({ text: "Seed-Satz geloescht", type: "ok" });
    });

    it("setzt currentSet auf null wenn geloeschter Satz aktiv war", async () => {
      useSeedStore.setState({
        seedSets: mockSeedSetList,
        currentSet: mockSeedSet,
      });

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.deleteSeedSet(1, 1);
      });

      expect(result.current.currentSet).toBeNull();
    });

    it("behaelt currentSet wenn anderer Satz geloescht wird", async () => {
      useSeedStore.setState({
        seedSets: mockSeedSetList,
        currentSet: mockSeedSet,
      });

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.deleteSeedSet(1, 2);
      });

      expect(result.current.currentSet).toEqual(mockSeedSet);
    });

    it("setzt error bei API-Fehler", async () => {
      seedApi.delete.mockRejectedValueOnce(new Error("Delete failed"));

      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.deleteSeedSet(1, 1);
      });

      expect(result.current.error).toContain("Delete failed");
    });
  });

  describe("importCsv", () => {
    it("importiert CSV und aktualisiert Liste", async () => {
      const testFile = new File(["col1,col2\nval1,val2"], "test.csv", { type: "text/csv" });

      const { result } = renderHook(() => useSeedStore());

      let res: any;
      await act(async () => {
        res = await result.current.importCsv(1, "Imported", testFile);
      });

      expect(seedApi.importCsv).toHaveBeenCalledWith(1, "Imported", testFile);
      expect(result.current.loading).toBe(false);
      expect(result.current.msg).toEqual({ text: "5 Seeds importiert", type: "ok" });
      expect(res).not.toBeNull();
      expect(res?.seed_count).toBe(5);
    });

    it("gibt null zurueck bei Fehler", async () => {
      seedApi.importCsv.mockRejectedValueOnce(new Error("Invalid CSV"));

      const { result } = renderHook(() => useSeedStore());

      const testFile = new File(["bad"], "test.csv", { type: "text/csv" });
      let res: any;
      await act(async () => {
        res = await result.current.importCsv(1, "Bad", testFile);
      });

      expect(res).toBeNull();
      expect(result.current.error).toContain("Invalid CSV");
    });
  });

  describe("gapFill", () => {
    it("fuehrt Lueckenschluss durch", async () => {
      const { result } = renderHook(() => useSeedStore());

      let res: any;
      await act(async () => {
        res = await result.current.gapFill(9);
      });

      expect(seedApi.gapFill).toHaveBeenCalledWith(9, "pairwise", 2);
      expect(result.current.loading).toBe(false);
      expect(result.current.msg).toEqual({ text: "Lueckenschluss: 3 ergaenzt", type: "ok" });
      expect(res).not.toBeNull();
      expect(res?.supplemented_count).toBe(3);
    });

    it("uebergibt custom strategy und tStrength", async () => {
      const { result } = renderHook(() => useSeedStore());

      await act(async () => {
        await result.current.gapFill(9, "all", 3);
      });

      expect(seedApi.gapFill).toHaveBeenCalledWith(9, "all", 3);
    });

    it("setzt error bei API-Fehler", async () => {
      seedApi.gapFill.mockRejectedValueOnce(new Error("No gaps found"));

      const { result } = renderHook(() => useSeedStore());

      let res: any;
      await act(async () => {
        res = await result.current.gapFill(9);
      });

      expect(res).toBeNull();
      expect(result.current.error).toContain("No gaps found");
    });
  });

  describe("addSeed", () => {
    it("fuegt Seed zu currentSet hinzu", () => {
      useSeedStore.setState({ currentSet: mockSeedSet });

      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.addSeed({ Browser: "Safari", OS: "macOS" });
      });

      expect(result.current.currentSet?.seed_cases.length).toBe(3);
      expect(result.current.currentSet?.seed_count).toBe(3);
      const lastSeed = result.current.currentSet?.seed_cases?.[2];
      expect(lastSeed?.assignment).toEqual({ Browser: "Safari", OS: "macOS" });
      expect(lastSeed?.order_index).toBe(2);
      expect(lastSeed?.id).toBeLessThan(0); // temporary negative ID
    });

    it("tut nichts wenn keine currentSet gesetzt ist", () => {
      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.addSeed({ Browser: "Safari" });
      });

      expect(result.current.currentSet).toBeNull();
    });
  });

  describe("removeSeed", () => {
    it("entfernt Seed an Index", () => {
      useSeedStore.setState({ currentSet: mockSeedSet });

      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.removeSeed(0);
      });

      expect(result.current.currentSet?.seed_cases.length).toBe(1);
      expect(result.current.currentSet?.seed_count).toBe(1);
      expect(result.current.currentSet?.seed_cases?.[0].id).toBe(2);
    });

    it("tut nichts wenn keine currentSet gesetzt ist", () => {
      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.removeSeed(0);
      });

      expect(result.current.currentSet).toBeNull();
    });
  });

  describe("updateSeed", () => {
    it("aendert Assignment eines Seeds", () => {
      useSeedStore.setState({ currentSet: mockSeedSet });

      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.updateSeed(0, { Browser: "Safari", OS: "macOS" });
      });

      expect(result.current.currentSet?.seed_cases?.[0].assignment).toEqual({
        Browser: "Safari",
        OS: "macOS",
      });
      // Other seeds unchanged
      expect(result.current.currentSet?.seed_cases?.[1].assignment).toEqual({
        Browser: "Firefox",
        OS: "Linux",
      });
    });

    it("tut nichts wenn keine currentSet gesetzt ist", () => {
      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.updateSeed(0, { Browser: "Safari" });
      });

      expect(result.current.currentSet).toBeNull();
    });
  });

  describe("clearMsg", () => {
    it("setzt msg auf null", () => {
      useSeedStore.setState({
        msg: { text: "Test message", type: "ok" },
      });

      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.clearMsg();
      });

      expect(result.current.msg).toBeNull();
    });
  });

  describe("setSelectedSet", () => {
    it("setzt currentSet auf uebergebenen SeedSet", () => {
      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.setSelectedSet(mockSeedSet);
      });

      expect(result.current.currentSet).toEqual(mockSeedSet);
    });

    it("setzt currentSet auf null", () => {
      useSeedStore.setState({ currentSet: mockSeedSet });

      const { result } = renderHook(() => useSeedStore());

      act(() => {
        result.current.setSelectedSet(null);
      });

      expect(result.current.currentSet).toBeNull();
    });
  });
});