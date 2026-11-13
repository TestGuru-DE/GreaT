// REQ-4023: Unit-Tests fuer Sharing-API-Client
import { describe, it, expect, vi, beforeEach } from "vitest";
import { getProjectMembers, addProjectMember, removeProjectMember } from "../sharingApi";

// Mock fetch globally
beforeEach(() => {
  vi.restoreAllMocks();
});

describe("sharingApi.getProjectMembers", () => {
  it("sendet GET /api/sharing/project/:id/members und gibt Member[] zurueck", async () => {
    const mockMembers = [
      { user_id: 1, username: "admin", role: "editor" },
      { user_id: 2, username: "user1", role: "viewer" },
    ];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockMembers),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await getProjectMembers(5);

    expect(mockedFetch).toHaveBeenCalledWith("/api/sharing/project/5/members", {
      credentials: "include",
    });
    expect(result).toEqual(mockMembers);
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Unauthorized"),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(getProjectMembers(5)).rejects.toThrow("Unauthorized");
  });
});

describe("sharingApi.addProjectMember", () => {
  it("sendet POST /api/sharing/project/:id/members mit user_id und role", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await addProjectMember(5, 42, "viewer");

    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/sharing/project/5/members",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: 42, role: "viewer" }),
        credentials: "include",
      }
    );
  });

  it("verwendet 'viewer' als Default-Role", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await addProjectMember(5, 99);

    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/sharing/project/5/members",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: 99, role: "viewer" }),
        credentials: "include",
      }
    );
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Bad request"),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(addProjectMember(5, 42)).rejects.toThrow("Bad request");
  });
});

describe("sharingApi.removeProjectMember", () => {
  it("sendet DELETE /api/sharing/project/:id/members/:userId", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await removeProjectMember(5, 42);

    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/sharing/project/5/members/42",
      {
        method: "DELETE",
        credentials: "include",
      }
    );
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Not found"),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(removeProjectMember(5, 42)).rejects.toThrow("Not found");
  });
});