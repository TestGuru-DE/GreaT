// REQ-4025: Tests fuer UserManagement-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import UserManagement from "../UserManagement";
import { useAuthStore } from "../../store/authStore";

// Mock useAuthStore
vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

// Typen fuer Mock-Daten
interface MockUser {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
}

describe("UserManagement - REQ-4025", () => {
  const mockUsers: MockUser[] = [
    { id: 1, username: "admin", role: "admin", is_active: true },
    { id: 2, username: "editor1", role: "editor", is_active: true },
    { id: 3, username: "viewer1", role: "viewer", is_active: false },
  ];

  const mockCurrentUser: MockUser = {
    id: 1,
    username: "admin",
    role: "admin",
    is_active: true,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  function mockFetchForUsers(users: MockUser[]) {
    return vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || opts.method === "GET" || !opts.method)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(users),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "PUT" && !urlStr.includes("/password")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "DELETE") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "PUT" && urlStr.includes("/password")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      if (urlStr === "/api/users" && opts?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 99, username: "newuser", role: "viewer", is_active: true }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });
  }

  function setupAuth(user: MockUser) {
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = {
        user,
        isLoading: false,
        error: null,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });
  }

  it("zeigt nichts fuer nicht-Admin-User", () => {
    setupAuth({ ...mockCurrentUser, role: "editor" });
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    const { container } = render(<UserManagement />);
    expect(container.textContent).toBe("");
  });

  it("zeigt die Komponente fuer Admin-User", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("Benutzerverwaltung")).toBeInTheDocument();
    });
  });

  it("zeigt alle Nutzer in der Tabelle", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
      expect(screen.getByText("editor1")).toBeInTheDocument();
      expect(screen.getByText("viewer1")).toBeInTheDocument();
    });
  });

  it("zeigt Rollen und Status in der Tabelle", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    render(<UserManagement />);

    await waitFor(() => {
      // Die Rolle-Spalte zeigt die selected Option des <select>
      // Die Optionen sind "Admin", "Editor", "Viewer" (kapitalisiert)
      // Der erste User (admin) hat Rolle "admin" -> zeigt "Admin"
      // Der zweite User (editor1) hat Rolle "editor" -> zeigt "Editor"
      // Der dritte User (viewer1) hat Rolle "viewer" -> zeigt "Viewer"
      // Wir pruefen, dass die select-Elemente die korrekten Rollen als selected haben
      const selects = screen.getAllByRole("combobox");
      expect(selects.length).toBe(3);
      expect(selects[0].value).toBe("admin");
      expect(selects[1].value).toBe("editor");
      expect(selects[2].value).toBe("viewer");

      // Status-Toggles sollten sichtbar sein
      const activeBtns = screen.getAllByText("aktiv");
      expect(activeBtns.length).toBe(2); // admin und editor1 sind aktiv
    });
  });

  it("zeigt 'Neuen Nutzer anlegen' Button", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Neuen Nutzer anlegen/i })).toBeInTheDocument();
    });
  });

  it("oeffnet den 'Neuen Nutzer' Dialog beim Klick", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    render(<UserManagement />);

    await waitFor(async () => {
      const btn = screen.getByRole("button", { name: /Neuen Nutzer anlegen/i });
      fireEvent.click(btn);

      // Nach dem Klick sollte der Dialog sichtbar sein
      expect(screen.getByPlaceholderText(/Benutzername/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Passwort/i)).toBeInTheDocument();
    });
  });

  it("sendet POST /api/users beim Erstellen eines neuen Nutzers", async () => {
    let capturedBody: any = null;
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr === "/api/users" && opts?.method === "POST") {
        capturedBody = JSON.parse(opts.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([...mockUsers, { id: 99, username: "newuser", role: "viewer", is_active: true }]),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(async () => {
      const btn = screen.getByRole("button", { name: /Neuen Nutzer anlegen/i });
      fireEvent.click(btn);

      const usernameInput = screen.getByPlaceholderText(/Benutzername/i);
      fireEvent.change(usernameInput, { target: { value: "newuser" } });

      const passwordInput = screen.getByPlaceholderText(/Passwort/i);
      fireEvent.change(passwordInput, { target: { value: "secret123" } });

      const roleSelect = screen.getByRole("combobox");
      fireEvent.change(roleSelect, { target: { value: "editor" } });

      const createBtn = screen.getByRole("button", { name: /Erstellen/i });
      fireEvent.click(createBtn);
    });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        "/api/users",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: "newuser", password: "secret123", role: "editor" }),
          credentials: "include",
        })
      );
    });
  });

  it("sendet PUT /api/users/{id} beim Aendern der Rolle", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "PUT" && !urlStr.includes("/password")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("editor1")).toBeInTheDocument();
    });

    // Finde den Rolle-Dropdown und aendere ihn
    const roleSelects = screen.getAllByRole("combobox");
    if (roleSelects.length > 0) {
      const targetSelect = roleSelects[1] || roleSelects[0];
      fireEvent.change(targetSelect, { target: { value: "admin" } });
    }

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/users/"),
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        })
      );
    });
  });

  it("zeigt Bestaetigungsdialog beim Loeschen eines Nutzers", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: "OK" }),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("editor1")).toBeInTheDocument();
    });

    // Klicke Loesch-Button
    const deleteButtons = screen.getAllByRole("button", { name: /Loeschen/i });
    if (deleteButtons.length > 0) {
      fireEvent.click(deleteButtons[0]);
    }

    await waitFor(() => {
      expect(screen.getByText(/wirklich loeschen/i)).toBeInTheDocument();
    });
  });

  it("sendet DELETE /api/users/{id} beim Bestaetigen des Loeschens", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "DELETE") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("editor1")).toBeInTheDocument();
    });

    // Klicke Loesch-Button und bestaetige
    const deleteButtons = screen.getAllByRole("button", { name: /Loeschen/i });
    if (deleteButtons.length > 0) {
      fireEvent.click(deleteButtons[0]);
    }

    await waitFor(() => {
      const confirmBtn = screen.getByRole("button", { name: /Ja.*loeschen/i });
      fireEvent.click(confirmBtn);
    });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/users/"),
        expect.objectContaining({
          method: "DELETE",
          credentials: "include",
        })
      );
    });
  });

  it("versteckt Loesch-Button fuer den eigenen Account", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: "OK" }),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    // Der Admin (id=1) sollte keinen Loesch-Button haben
    // Nur 2 Loesch-Buttons (fuer editor1 und viewer1), nicht 3
    const deleteButtons = screen.getAllByRole("button", { name: /Loeschen/i });
    expect(deleteButtons.length).toBe(2);
  });

  it("oeffnet den Passwort-Dialog beim Klick auf 'Passwort aendern'", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: "OK" }),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("editor1")).toBeInTheDocument();
    });

    // Klicke Passwort-aendern Button
    const passwordButtons = screen.getAllByRole("button", { name: /Passwort aendern/i });
    if (passwordButtons.length > 0) {
      fireEvent.click(passwordButtons[0]);
    }

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Neues Passwort/i)).toBeInTheDocument();
    });
  });

  it("sendet PUT /api/users/{id}/password beim Aendern des Passworts", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr.includes("/password") && opts?.method === "PUT") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(async () => {
      expect(screen.getByText("editor1")).toBeInTheDocument();

      // Oeffne Passwort-Dialog und aendere Passwort
      const passwordButtons = screen.getAllByRole("button", { name: /Passwort aendern/i });
      if (passwordButtons.length > 0) {
        fireEvent.click(passwordButtons[0]);
      }

      const passwordInput = screen.getByPlaceholderText(/Neues Passwort/i);
      fireEvent.change(passwordInput, { target: { value: "newpass123" } });

      // Der Button im Dialog hat den Text "Aendern" (oder "Aendern" mit Umlaut)
      const buttons = screen.getAllByRole("button");
      const changeBtn = buttons.find(b => /Aendern/.test(b.textContent || ""));
      if (changeBtn) {
        fireEvent.click(changeBtn);
      }
    });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining("/password"),
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: "newpass123" }),
          credentials: "include",
        })
      );
    });
  });

  it("zeigt Fehlermeldung bei fehlgeschlagenem API-Aufruf", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr === "/api/users" && opts?.method === "POST") {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ detail: "Benutzername existiert bereits" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(async () => {
      const btn = screen.getByRole("button", { name: /Neuen Nutzer anlegen/i });
      fireEvent.click(btn);

      const usernameInput = screen.getByPlaceholderText(/Benutzername/i);
      fireEvent.change(usernameInput, { target: { value: "admin" } });

      const passwordInput = screen.getByPlaceholderText(/Passwort/i);
      fireEvent.change(passwordInput, { target: { value: "secret" } });

      const createBtn = screen.getByRole("button", { name: /Erstellen/i });
      fireEvent.click(createBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("Benutzername existiert bereits")).toBeInTheDocument();
    });
  });

  it("schaltet Nutzer aktiv/inaktiv mit Toggle", async () => {
    const mockedFetch = vi.fn().mockImplementation((url: string | URL | Request, opts?: any) => {
      const urlStr = url.toString();
      if (urlStr === "/api/users" && (!opts || !opts.method || opts.method === "GET")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUsers),
        });
      }
      if (urlStr.startsWith("/api/users/") && opts?.method === "PUT" && !urlStr.includes("/password")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: "OK" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });
    });
    vi.stubGlobal("fetch", mockedFetch);

    setupAuth(mockCurrentUser);

    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("viewer1")).toBeInTheDocument();
    });

    // Finde und klicke den Aktiv/Toggle-Button fuer viewer1 (is_active: false)
    const toggleButtons = screen.getAllByRole("button", { name: /aktiv/i });
    if (toggleButtons.length > 0) {
      fireEvent.click(toggleButtons[0]);
    }

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/users/"),
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        })
      );
    });
  });

  it("nutzt Theme-Tokens statt hartkodierter Farben", async () => {
    setupAuth(mockCurrentUser);
    vi.stubGlobal("fetch", mockFetchForUsers(mockUsers));

    const { container } = render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("Benutzerverwaltung")).toBeInTheDocument();
    });

    // Sollte theme-tokens verwenden
    const themed = container.querySelector(".bg-theme-surface");
    expect(themed).not.toBeNull();
  });
});