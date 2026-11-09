// REQ-4023: Projekt-Mitgliederverwaltung
// Teil von EPIC-18 (Multi-User) / Sprint 13
//
// Ermoglicht dem Projekt-Owner/Admin, Team-Mitglieder
// mit Zugriff auf das Projekt hinzuzufuegen und zu entfernen.
import { useState, useEffect } from "react";
import {
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
  type Member,
} from "../api/sharingApi";

interface ProjectMembersProps {
  projectId: number;
}

export default function ProjectMembers({ projectId }: ProjectMembersProps) {
  const [members, setMembers] = useState<Member[]>([]);
  const [newUserId, setNewUserId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMembers();
  }, [projectId]);

  async function loadMembers() {
    try {
      const data = await getProjectMembers(projectId);
      setMembers(data);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  async function addMember() {
    const id = parseInt(newUserId, 10);
    if (isNaN(id)) return;

    setLoading(true);
    setError(null);
    try {
      await addProjectMember(projectId, id, "viewer");
      setNewUserId("");
      await loadMembers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function removeMember(userId: number) {
    try {
      await removeProjectMember(projectId, userId);
      await loadMembers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  return (
    <div className="bg-theme-bg rounded-lg border border-theme-border p-4">
      <h3 className="text-lg font-semibold text-theme-text mb-4">
        Projekt-Mitglieder
      </h3>

      {/* Mitglieder-Liste */}
      <ul className="space-y-2">
        {members.map((member) => (
          <li
            key={member.user_id}
            className="flex items-center justify-between py-2 border-b border-theme-border"
          >
            <div>
              <span className="text-theme-text font-medium">
                {member.username || `User #${member.user_id}`}
              </span>
              <span className="ml-2 text-sm text-theme-text-secondary">
                ({member.role})
              </span>
            </div>
            <button
              onClick={() => removeMember(member.user_id)}
              className="text-sm text-theme-danger hover:underline"
            >
              Entfernen
            </button>
          </li>
        ))}
      </ul>

      {/* Neues Mitglied hinzufuegen */}
      <div className="mt-4 flex gap-2">
        <input
          type="number"
          value={newUserId}
          onChange={(e) => setNewUserId(e.target.value)}
          placeholder="User-ID"
          className="flex-1 rounded-md border border-theme-border px-3 py-2 text-theme-text bg-theme-bg-input"
        />
        <button
          onClick={addMember}
          disabled={loading || !newUserId}
          className="px-4 py-2 text-sm font-medium text-white bg-theme-primary rounded-md hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "..." : "Hinzufuegen"}
        </button>
      </div>

      {error && (
        <p className="mt-2 text-sm text-theme-danger">{error}</p>
      )}
    </div>
  );
}