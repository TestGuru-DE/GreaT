// REQ-4023: Unit-Tests fuer Sharing-API-Client
import { describe, it, expect, vi, beforeEach } from "vitest";
import { getProjectMembers, addProjectMember, removeProjectMember } from "../sharingApi";

vi.mock("../client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from "../client";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("sharingApi.getProjectMembers", () => {
  it("sendet GET /sharing/project/:id/members und gibt Member[] zurueck", async () => {
    const mockMembers = [
      { user_id: 1, username: "admin", role: "editor" },
      { user_id: 2, username: "user1", role: "viewer" },
    ];

    (api.get as any).mockResolvedValue({
      data: mockMembers,
    });

    const result = await getProjectMembers(5);

    expect(api.get).toHaveBeenCalledWith("/sharing/project/5/members");
    expect(result).toEqual(mockMembers);
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    (api.get as any).mockRejectedValue(new Error("Unauthorized"));

    await expect(getProjectMembers(5)).rejects.toThrow("Unauthorized");
  });
});

describe("sharingApi.addProjectMember", () => {
  it("sendet POST /sharing/project/:id/members mit user_id und role", async () => {
    (api.post as any).mockResolvedValue({ data: undefined });

    await addProjectMember(5, 42, "viewer");

    expect(api.post).toHaveBeenCalledWith(
      "/sharing/project/5/members",
      { user_id: 42, role: "viewer" }
    );
  });

  it("verwendet 'viewer' als Default-Role", async () => {
    (api.post as any).mockResolvedValue({ data: undefined });

    await addProjectMember(5, 99);

    expect(api.post).toHaveBeenCalledWith(
      "/sharing/project/5/members",
      { user_id: 99, role: "viewer" }
    );
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    (api.post as any).mockRejectedValue(new Error("Bad request"));

    await expect(addProjectMember(5, 42)).rejects.toThrow("Bad request");
  });
});

describe("sharingApi.removeProjectMember", () => {
  it("sendet DELETE /sharing/project/:id/members/:userId", async () => {
    (api.delete as any).mockResolvedValue({ data: undefined });

    await removeProjectMember(5, 42);

    expect(api.delete).toHaveBeenCalledWith("/sharing/project/5/members/42");
  });

  it("wirft Error bei nicht-ok Antwort", async () => {
    (api.delete as any).mockRejectedValue(new Error("Not found"));

    await expect(removeProjectMember(5, 42)).rejects.toThrow("Not found");
  });
});