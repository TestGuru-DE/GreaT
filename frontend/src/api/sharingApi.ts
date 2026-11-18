// REQ-4023: Sharing-API-Calls fuer Projekt-Mitgliederverwaltung
// Teil von EPIC-18 (Multi-User) / Sprint 13
import api from "./client";

export interface Member {
  user_id: number;
  username?: string;
  role: "editor" | "viewer";
}

export const sharingApi = {
  getProjectMembers: async (projectId: number): Promise<Member[]> => {
    const { data } = await api.get<Member[]>(`/sharing/project/${projectId}/members`);
    return data;
  },

  addProjectMember: async (
    projectId: number,
    userId: number,
    role: string = "viewer"
  ): Promise<void> => {
    await api.post(`/sharing/project/${projectId}/members`, { user_id: userId, role });
  },

  removeProjectMember: async (
    projectId: number,
    userId: number
  ): Promise<void> => {
    await api.delete(`/sharing/project/${projectId}/members/${userId}`);
  },
};

// Legacy exports for backwards compatibility during migration
export const getProjectMembers = sharingApi.getProjectMembers;
export const addProjectMember = sharingApi.addProjectMember;
export const removeProjectMember = sharingApi.removeProjectMember;