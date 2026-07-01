// REQ-1204 + REQ-2002: Zustand Store fuer Projektliste mit Bulk-Delete
import { create } from "zustand";
import { projectsApi } from "../api/client";
import type { Project } from "../types";

interface BulkDeleteResult { deleted: number; blocked: number[]; }

interface ProjectStore {
  projects: Project[];
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  createProject: (name: string) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  bulkDelete: (ids: number[]) => Promise<BulkDeleteResult>;
  bulkDeleteForce: (ids: number[]) => Promise<BulkDeleteResult>;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const projects = await projectsApi.list();
      set({ projects, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  createProject: async (name: string) => {
    const project = await projectsApi.create({ name });
    set((s) => ({ projects: [...s.projects, project] }));
  },

  deleteProject: async (id: number) => {
    await projectsApi.forceDelete(id);
    set((s) => ({ projects: s.projects.filter((p) => p.id !== id) }));
  },

  bulkDelete: async (ids: number[]) => {
    const res = await projectsApi.bulkDelete(ids);
    set((s) => ({ projects: s.projects.filter((p) => !ids.includes(p.id) || (res.blocked ?? []).includes(p.id)) }));
    return res;
  },

  bulkDeleteForce: async (ids: number[]) => {
    const res = await projectsApi.bulkDeleteForce(ids);
    set((s) => ({ projects: s.projects.filter((p) => !ids.includes(p.id)) }));
    return res;
  },
}));
