// REQ-4022: Tests fuer 409-Conflict-Handler
import { describe, it, expect, vi, beforeEach } from "vitest";
import { extractConflict, handleConflictResponse, type ConflictInfo } from "./handlers";

describe("Conflict Handlers - REQ-4022", () => {
  describe("extractConflict", () => {
    it("gibt null zurueck wenn Status nicht 409", async () => {
      const response = new Response("OK", { status: 200 });
      const result = await extractConflict(response);
      expect(result).toBeNull();
    });

    it("gibt ConflictInfo zurueck bei Status 409", async () => {
      const conflictData: ConflictInfo = {
        type: "version_conflict",
        message: "Version mismatch",
        clientVersion: 1,
        serverVersion: 2,
      };

      const response = new Response(JSON.stringify(conflictData), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      });

      const result = await extractConflict(response);
      expect(result).not.toBeNull();
      expect(result!.type).toBe("version_conflict");
      expect(result!.clientVersion).toBe(1);
      expect(result!.serverVersion).toBe(2);
    });
  });

  describe("handleConflictResponse", () => {
    let onConflict: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      onConflict = vi.fn();
    });

    it("ruft onConflict nicht auf bei 200 Response", async () => {
      const response = new Response("OK", { status: 200 });
      const result = await handleConflictResponse(response, onConflict);
      expect(result).toBe(false);
      expect(onConflict).not.toHaveBeenCalled();
    });

    it("ruft onConflict auf bei 409 Response", async () => {
      const conflictData: ConflictInfo = {
        type: "version_conflict",
        message: "Version mismatch",
        clientVersion: 1,
        serverVersion: 2,
      };

      const response = new Response(JSON.stringify(conflictData), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      });

      const result = await handleConflictResponse(response, onConflict);
      expect(result).toBe(true);
      expect(onConflict).toHaveBeenCalledWith(conflictData);
    });
  });
});