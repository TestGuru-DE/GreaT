// REQ-1212: Toast-Benachrichtigungen
import { create } from "zustand";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastStore {
  toasts: Toast[];
  add: (message: string, type?: ToastType, duration?: number) => void;
  remove: (id: number) => void;
}

let nextId = 0;

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  add: (message, type = "success", duration = 3000) => {
    const id = ++nextId;
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, type === "error" ? 5000 : duration);
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function ToastContainer() {
  const { toasts, remove } = useToastStore();
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          onClick={() => remove(t.id)}
          className={
            "flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg cursor-pointer text-sm font-medium " +
            (t.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
              : t.type === "error"
              ? "bg-red-50 border border-red-200 text-red-800"
              : "bg-sky-50 border border-sky-200 text-sky-800")
          }
        >
          <span>{t.type === "success" ? "OK" : t.type === "error" ? "!" : "i"}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}