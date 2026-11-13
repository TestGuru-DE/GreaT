// REQ-4023: Tests fuer ProjectMembers-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ProjectMembers from "../ProjectMembers";

// Mock fetch
beforeEach(() => {
  vi.restoreAllMocks();
});

function mockMembersResponse(members: any[]) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(members),
  });
}

function mockOkResponse() {
  return vi.fn().mockResolvedValue({
    ok: true,
  });
}

function mockErrorResponse(status: number, text: string) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    text: () => Promise.resolve(text),
    json: () => Promise.resolve({ detail: text }),
  });
}

describe("ProjectMembers - REQ-4023", () => {
  it("laedt und zeigt Mitglieder-Liste beim Mount", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
      { user_id: 2, username: "user1", role: "viewer" },
    ];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
      expect(screen.getByText("user1")).toBeInTheDocument();
    });

    // Sollte GET-Anfrage gesendet haben
    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/sharing/project/5/members",
      { credentials: "include" }
    );
  });

  it("zeigt Mitglieder ohne username als User #:id", async () => {
    const members = [
      { user_id: 99, role: "viewer" },
    ];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("User #99")).toBeInTheDocument();
    });
  });

  it("zeigt Rolle neben Username", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("(editor)")).toBeInTheDocument();
    });
  });

  it("sendet POST beim Hinzufuegen eines Mitglieds", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    let callCount = 0;
    const mockedFetch = vi.fn().mockImplementation((url: string, opts?: any) => {
      callCount++;
      if (opts?.method === "POST") {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(members),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    // Warte bis Mitglieder geladen
    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Fuelle User-ID Input
    const input = screen.getByPlaceholderText("User-ID");
    fireEvent.change(input, { target: { value: "42" } });

    // Klicke Hinzufuegen
    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    // Sollte POST-Anfrage gesendet haben
    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        "/api/sharing/project/5/members",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: 42, role: "viewer" }),
          credentials: "include",
        })
      );
    });
  });

  it("sendet DELETE beim Entfernen eines Mitglieds", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    const mockedFetch = vi.fn().mockImplementation((url: string, opts?: any) => {
      if (opts?.method === "DELETE") {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(members),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Klicke Entfernen
    const removeBtn = screen.getByRole("button", { name: /Entfernen/i });
    fireEvent.click(removeBtn);

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        "/api/sharing/project/5/members/1",
        expect.objectContaining({
          method: "DELETE",
          credentials: "include",
        })
      );
    });
  });

  it("zeigt Error-Nachricht bei fehlgeschlagenem Hinzufuegen", async () => {
    const members: any[] = [];

    const mockedFetch = vi.fn().mockImplementation((url: string, opts?: any) => {
      if (opts?.method === "POST") {
        return Promise.resolve({
          ok: false,
          text: () => Promise.resolve("User nicht gefunden"),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(members),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    // Fuelle User-ID Input
    const input = screen.getByPlaceholderText("User-ID");
    fireEvent.change(input, { target: { value: "999" } });

    // Klicke Hinzufuegen
    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText("User nicht gefunden")).toBeInTheDocument();
    });
  });

  it("Hinzufuegen-Button ist disabled wenn Input leer", async () => {
    const members: any[] = [];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });
    vi.stubGlobal("fetch", mockedFetch);

    render(<ProjectMembers projectId={5} />);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    expect(addBtn).toBeDisabled();
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(members),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const { container } = render(<ProjectMembers projectId={5} />);

    // Sollte theme-tokens verwenden
    const themed = container.querySelector(".bg-theme-bg");
    expect(themed).not.toBeNull();
  });
});