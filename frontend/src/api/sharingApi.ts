// REQ-4023: Sharing-API-Calls fuer Projekt-Mitgliederverwaltung
// Teil von EPIC-18 (Multi-User) / Sprint 13

export interface Member {
  user_id: number;
  username?: string;
  role: "editor" | "viewer";
}

export async function getProjectMembers(projectId: number): Promise<Member[]> {
  const response = await fetch(`/api/sharing/project/${projectId}/members`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function addProjectMember(
  projectId: number,
  userId: number,
  role: string = "viewer"
): Promise<void> {
  const response = await fetch(`/api/sharing/project/${projectId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, role }),
    credentials: "include",
  });
  if (!response.ok) throw new Error(await response.text());
}

export async function removeProjectMember(
  projectId: number,
  userId: number
): Promise<void> {
  const response = await fetch(`/api/sharing/project/${projectId}/members/${userId}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) throw new Error(await response.text());
}