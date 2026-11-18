// REQ-4023: Tests fuer ProjectMembers-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ProjectMembers from "../ProjectMembers";

vi.mock("../../api/sharingApi", () => ({
  getProjectMembers: vi.fn(),
  addProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
}));

import { getProjectMembers, addProjectMember, removeProjectMember } from "../../api/sharingApi";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("ProjectMembers - REQ-4023", () => {
  it("laedt und zeigt Mitglieder-Liste beim Mount", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
      { user_id: 2, username: "user1", role: "viewer" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
      expect(screen.getByText("user1")).toBeInTheDocument();
    });

    // Sollte GET-Anfrage gesendet haben
    expect(getProjectMembers).toHaveBeenCalledWith(5);
  });

  it("zeigt Mitglieder ohne username als User #:id", async () => {
    const members = [
      { user_id: 99, role: "viewer" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("User #99")).toBeInTheDocument();
    });
  });

  it("zeigt Rolle neben Username", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("(editor)")).toBeInTheDocument();
    });
  });

  it("sendet POST beim Hinzufuegen eines Mitglieds", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);
    (addProjectMember as any).mockResolvedValue(undefined);

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
      expect(addProjectMember).toHaveBeenCalledWith(5, 42, "viewer");
    });
  });

  it("sendet DELETE beim Entfernen eines Mitglieds", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);
    (removeProjectMember as any).mockResolvedValue(undefined);

    render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Klicke Entfernen
    const removeBtn = screen.getByRole("button", { name: /Entfernen/i });
    fireEvent.click(removeBtn);

    await waitFor(() => {
      expect(removeProjectMember).toHaveBeenCalledWith(5, 1);
    });
  });

  it("zeigt Error-Nachricht bei fehlgeschlagenem Hinzufuegen", async () => {
    const members: any[] = [];

    (getProjectMembers as any).mockResolvedValue(members);
    (addProjectMember as any).mockRejectedValue(new Error("User nicht gefunden"));

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

    (getProjectMembers as any).mockResolvedValue(members);

    render(<ProjectMembers projectId={5} />);

    const addBtn = screen.getByRole("button", { name: /Hinzufuegen/i });
    expect(addBtn).toBeDisabled();
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", async () => {
    const members = [
      { user_id: 1, username: "admin", role: "editor" },
    ];

    (getProjectMembers as any).mockResolvedValue(members);

    const { container } = render(<ProjectMembers projectId={5} />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Sollte theme-tokens verwenden
    const themed = container.querySelector(".bg-theme-bg");
    expect(themed).not.toBeNull();
  });
});