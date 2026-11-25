// BUG A-01: Admin legt API-Tokens fuer technische Nutzer (Rolle api_user) an

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "de" } }),
}));

vi.mock("../../api/apiTokensApi", () => ({ createToken: vi.fn() }));
vi.mock("../../api/usersApi", () => ({ usersApi: { list: vi.fn() } }));

let currentRole = "admin";
vi.mock("../../store/authStore", () => ({
  useAuthStore: (selector: (s: unknown) => unknown) => selector({ user: { role: currentRole } }),
}));

import ApiTokenCreateDialog from "../ApiTokenCreateDialog";
import { createToken } from "../../api/apiTokensApi";
import { usersApi } from "../../api/usersApi";

const USERS = [
  { id: 1, username: "admin", role: "admin", is_active: true },
  { id: 7, username: "jenkins", role: "api_user", is_active: true },
  { id: 8, username: "alt-ci", role: "api_user", is_active: false },
  { id: 9, username: "anna", role: "editor", is_active: true },
];

describe("ApiTokenCreateDialog - Besitzer (A-01)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentRole = "admin";
    (usersApi.list as ReturnType<typeof vi.fn>).mockResolvedValue(USERS);
    (createToken as ReturnType<typeof vi.fn>).mockResolvedValue({ token: "great_pat_x" });
  });

  it("Admin sieht nur aktive technische Nutzer als moegliche Besitzer", async () => {
    render(<ApiTokenCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    const select = await screen.findByLabelText("settings.apiTokens.owner");
    const options = Array.from((select as HTMLSelectElement).options).map((o) => o.textContent);
    expect(options).toEqual(["settings.apiTokens.ownerSelf", "jenkins"]);
  });

  it("sendet user_id des gewaehlten technischen Nutzers", async () => {
    render(<ApiTokenCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    const select = await screen.findByLabelText("settings.apiTokens.owner");
    fireEvent.change(select, { target: { value: "7" } });
    fireEvent.change(screen.getByPlaceholderText("settings.apiTokens.namePlaceholder"), { target: { value: "CI" } });
    fireEvent.click(screen.getByText("settings.apiTokens.createButton"));
    await waitFor(() => expect(createToken).toHaveBeenCalledWith(expect.objectContaining({ user_id: 7, name: "CI" })));
  });

  it("ohne Auswahl wird kein user_id gesendet (eigenes Token)", async () => {
    render(<ApiTokenCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    await screen.findByLabelText("settings.apiTokens.owner");
    fireEvent.change(screen.getByPlaceholderText("settings.apiTokens.namePlaceholder"), { target: { value: "Eigen" } });
    fireEvent.click(screen.getByText("settings.apiTokens.createButton"));
    await waitFor(() => expect(createToken).toHaveBeenCalled());
    expect((createToken as ReturnType<typeof vi.fn>).mock.calls[0][0]).not.toHaveProperty("user_id");
  });

  it("Nicht-Admins sehen keine Besitzer-Auswahl und laden keine Nutzerliste", () => {
    currentRole = "editor";
    render(<ApiTokenCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    expect(screen.queryByLabelText("settings.apiTokens.owner")).toBeNull();
    expect(usersApi.list).not.toHaveBeenCalled();
  });
});
