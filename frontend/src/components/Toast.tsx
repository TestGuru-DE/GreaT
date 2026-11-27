// REQ-1212: Toast-Benachrichtigungen
import { create } from "zustand";
import { CircleAlert, CircleCheck, Info } from "lucide-react";

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
          // Redesign: Toast als Karte mit Rand und farbigem Statussymbol (wie im Beispiel)
          className="card flex items-start gap-3 px-4 py-3 cursor-pointer text-sm font-medium text-theme-text shadow-[var(--shadow-pop)]"
          role={t.type === "error" ? "alert" : "status"}
        >
          {t.type === "success" ? (
            <CircleCheck className="w-5 h-5 shrink-0 text-theme-success" aria-label="OK" />
          ) : t.type === "error" ? (
            <CircleAlert className="w-5 h-5 shrink-0 text-theme-danger" aria-label="!" />
          ) : (
            <Info className="w-5 h-5 shrink-0 text-theme-link" aria-label="i" />
          )}
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}