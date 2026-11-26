// REQ-4028: Tests fuer ChangePasswordPage
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ChangePasswordPage from "../ChangePasswordPage";
import { useAuthStore } from "../../store/authStore";
import { ApiError } from "../../api/ApiError";

// REQ-6005: i18n mock for ChangePasswordPage tests
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const tr: Record<string, string> = {
        "changePassword.title": "Passwort ändern",
        "changePassword.success": "Passwort wurde geändert. Sie werden weitergeleitet...",
        "changePassword.currentPassword": "Aktuelles Passwort",
        "changePassword.newPassword": "Neues Passwort",
        "changePassword.confirmPassword": "Neues Passwort wiederholen",
        "changePassword.minLength": "Mindestens {{count}} Zeichen",
        "changePassword.changeBtn": "Ändern",
        "changePassword.errors.tooShort": "Das neue Passwort muss mindestens {{count}} Zeichen lang sein.",
        "changePassword.errors.mismatch": "Die neuen Passwörter stimmen nicht überein.",
        "changePassword.errors.currentInvalid": "Das aktuelle Passwort ist falsch.",
        "changePassword.errors.isDefault": "Dieses Passwort ist ein bekanntes Standardpasswort und nicht erlaubt.",
        "changePassword.errors.tooLong": "Das neue Passwort ist zu lang.",
        "changePassword.errors.tooManyAttempts": "Zu viele Versuche. Bitte warte einen Moment.",
        "changePassword.errors.tooCommon": "Dieses Passwort ist zu verbreitet.",
        "changePassword.errors.lowVariety": "Mindestens {{count}} verschiedene Zeichen.",
        "changePassword.errors.generic": "Das Passwort konnte nicht geändert werden.",
      };
      let v = tr[key] ?? key;
      if (params) v = v.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
      return v;
    },
    i18n: { language: "de" },
  }),
}));

vi.mock("../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...(actual as object),
    useNavigate: () => vi.fn(),
  };
});

beforeEach(() => {
  vi.restoreAllMocks();
});

// Helper: get new-password input by id (avoids getByLabelText ambiguity with "Neues Passwort wiederholen")
function getNewPasswordInput() {
  return screen.getByTestId("new-password-input") as HTMLInputElement;
}

describe("ChangePasswordPage - REQ-4028", () => {
  const mockChangePassword = vi.fn();
  const mockSetPasswordChangeRequired = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockChangePassword.mockReset();
    mockSetPasswordChangeRequired.mockReset();

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: true,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: mockSetPasswordChangeRequired,
        changePassword: mockChangePassword,
      };
      // @ts-expect-error - selector returns the right value
      return selector(state);
    });
  });

  it("zeigt drei Passwort-Felder", () => {
    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Aktuelles Passwort/i)).toBeInTheDocument();
    expect(getNewPasswordInput()).toBeInTheDocument();
    expect(screen.getByLabelText(/Neues Passwort wiederholen/i)).toBeInTheDocument();
  });

  it("zeigt Fehler bei zu kurzem neuen Passwort (<12 Zeichen)", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "short");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "short");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/mindestens 12 Zeichen/i);
    });
  });

  it("zeigt Fehler bei nicht uebereinstimmenden Passworten", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "newpass123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "different123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByText(/Passwörter.*stimmen nicht überein/i)).toBeInTheDocument();
    });
  });

  it("ruft changePassword bei gueltiger Eingabe auf", async () => {
    mockChangePassword.mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "newpass123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "newpass123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith("oldpass123!", "newpass123!abc");
    });
  });

  it("zeigt Erfolgsmeldung nach erfolgreichem Wechsel", async () => {
    mockChangePassword.mockResolvedValue(undefined);
    const user = userEvent.setup();

    vi.mocked(useAuthStore).mockImplementation((selector) => {
      const state = {
        user: { id: 1, username: "admin", role: "admin", is_active: true },
        isLoading: false,
        error: null,
        passwordChangeRequired: true,
        login: vi.fn(),
        logout: vi.fn(),
        loadUser: vi.fn(),
        clearError: vi.fn(),
        refresh: vi.fn(),
        setPasswordChangeRequired: mockSetPasswordChangeRequired,
        changePassword: async () => {
          await mockChangePassword();
          mockSetPasswordChangeRequired(false);
        },
      };
      // @ts-expect-error
      return selector(state);
    });

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "newpass123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "newpass123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByText(/Passwort.*geändert/i)).toBeInTheDocument();
    });
  });

  it("zeigt Fehlermeldung 'current_password_invalid' als deutsche Meldung", async () => {
    mockChangePassword.mockRejectedValue(new Error("current_password_invalid"));
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "wrong");
    await user.type(getNewPasswordInput(), "newpass123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "newpass123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByText("Das aktuelle Passwort ist falsch.")).toBeInTheDocument();
    });
  });

  it("zeigt Fehlermeldung 'password_is_default' als deutsche Meldung", async () => {
    mockChangePassword.mockRejectedValue(new Error("password_is_default"));
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "changeme123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "changeme123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Dieses Passwort ist ein bekanntes Standardpasswort und nicht erlaubt.")
      ).toBeInTheDocument();
    });
  });

  it("zeigt Fehlermeldung 'password_too_long' als deutsche Meldung", async () => {
    mockChangePassword.mockRejectedValue(new Error("password_too_long"));
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    // Einfuegen statt 2 x 129 Tastendruecke (Test lief sonst nahe am 5-s-Limit)
    await user.click(getNewPasswordInput());
    await user.paste("a".repeat(129));
    await user.click(screen.getByLabelText(/Neues Passwort wiederholen/i));
    await user.paste("a".repeat(129));
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByText("Das neue Passwort ist zu lang.")).toBeInTheDocument();
    });
  });

  it("zeigt Fehlermeldung 'too_many_attempts' als deutsche Meldung", async () => {
    mockChangePassword.mockRejectedValue(new Error("too_many_attempts"));
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "newpass123!abc");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "newpass123!abc");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));

    await waitFor(() => {
      expect(screen.getByText("Zu viele Versuche. Bitte warte einen Moment.")).toBeInTheDocument();
    });
  });

  // N-01: echte Fehlerform des Clients (ApiError mit Server-Code), alle Policy-Codes uebersetzt
  async function submitWithError(error: unknown) {
    mockChangePassword.mockRejectedValue(error);
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>
    );
    await user.type(screen.getByLabelText(/Aktuelles Passwort/i), "oldpass123!");
    await user.type(getNewPasswordInput(), "password1234");
    await user.type(screen.getByLabelText(/Neues Passwort wiederholen/i), "password1234");
    await user.click(screen.getByRole("button", { name: /Ändern/i }));
  }

  it("N-01: 'password_too_common' wird als verstaendliche Meldung gezeigt", async () => {
    await submitWithError(new ApiError(400, "password_too_common"));
    await waitFor(() => {
      expect(screen.getByText("Dieses Passwort ist zu verbreitet.")).toBeInTheDocument();
    });
    expect(screen.queryByText(/Request failed/)).not.toBeInTheDocument();
  });

  it("N-01: 'password_low_variety' wird als verstaendliche Meldung gezeigt", async () => {
    await submitWithError(new ApiError(400, "password_low_variety"));
    await waitFor(() => {
      expect(screen.getByText("Mindestens 4 verschiedene Zeichen.")).toBeInTheDocument();
    });
  });

  it("N-01: unbekannter Code fuehrt zu allgemeiner Meldung statt Rohtext", async () => {
    await submitWithError(new ApiError(400, "some_future_code"));
    await waitFor(() => {
      expect(screen.getByText("Das Passwort konnte nicht geändert werden.")).toBeInTheDocument();
    });
    expect(screen.queryByText("some_future_code")).not.toBeInTheDocument();
  });

  it("N-01: Netzwerkfehler zeigt die Meldung des Clients", async () => {
    await submitWithError(new ApiError(0, "Network Error"));
    await waitFor(() => {
      expect(screen.getByText("Server nicht erreichbar")).toBeInTheDocument();
    });
  });
});