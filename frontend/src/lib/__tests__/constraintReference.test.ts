// REQ-6001 AK-10 / BUG K-02: Rueckfrage beim Loeschen referenzierter Kategorien/Werte
import { describe, it, expect, vi } from "vitest";
import { ApiError } from "../../api/ApiError";
import { constraintReferenceNames, deleteWithConstraintCheck } from "../constraintReference";

const conflict = () =>
  new ApiError(409, {
    code: "constraint_reference",
    detail: "Constraints verweisen auf diesen Eintrag: Regel A",
    constraints: ["Regel A", "Regel B"],
  });

describe("constraintReferenceNames", () => {
  it("liest die Constraint-Namen aus der 409-Antwort", () => {
    expect(constraintReferenceNames(conflict())).toEqual(["Regel A", "Regel B"]);
  });

  it("ignoriert andere Fehler", () => {
    expect(constraintReferenceNames(new ApiError(409, "Name existiert bereits"))).toBeNull();
    expect(constraintReferenceNames(new ApiError(500, { code: "constraint_reference" }))).toBeNull();
    expect(constraintReferenceNames(new Error("x"))).toBeNull();
  });
});

describe("deleteWithConstraintCheck", () => {
  it("loescht direkt, wenn kein Constraint betroffen ist", async () => {
    const run = vi.fn().mockResolvedValue(undefined);
    const confirmFn = vi.fn();
    await expect(deleteWithConstraintCheck(run, confirmFn)).resolves.toBe(true);
    expect(run).toHaveBeenCalledTimes(1);
    expect(run).toHaveBeenCalledWith(false);
    expect(confirmFn).not.toHaveBeenCalled();
  });

  it("fragt bei betroffenen Constraints nach und loescht nach Bestaetigung mit force", async () => {
    const run = vi.fn().mockRejectedValueOnce(conflict()).mockResolvedValueOnce(undefined);
    const confirmFn = vi.fn().mockReturnValue(true);
    await expect(deleteWithConstraintCheck(run, confirmFn)).resolves.toBe(true);
    expect(confirmFn).toHaveBeenCalledWith(["Regel A", "Regel B"]);
    expect(run).toHaveBeenNthCalledWith(2, true);
  });

  it("bricht ohne Bestaetigung ab und loescht nicht", async () => {
    const run = vi.fn().mockRejectedValueOnce(conflict());
    await expect(deleteWithConstraintCheck(run, () => false)).resolves.toBe(false);
    expect(run).toHaveBeenCalledTimes(1);
  });

  it("reicht andere Fehler weiter", async () => {
    const run = vi.fn().mockRejectedValue(new ApiError(500, "kaputt"));
    await expect(deleteWithConstraintCheck(run, () => true)).rejects.toThrow("kaputt");
  });
});
