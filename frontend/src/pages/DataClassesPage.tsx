// REQ-2003: Datenklassen-Seite – Wiederverwendbare Aequivalenzklassen-Bibliothek
import { useEffect, useRef, useState } from "react";
import { dataclassApi } from "../api/client";
import type { DataClass, DataClassValue } from "../api/client";

const VALUE_TYPES = [
  { value: "text", label: "Text" },
  { value: "number", label: "Numerisch" },
  { value: "date", label: "Datum" },
  { value: "time", label: "Uhrzeit" },
  { value: "boolean", label: "Boolean" },
  { value: "email", label: "E-Mail" },
  { value: "freetext", label: "Freitext (keine Validierung)" },
];

const TYPE_COLORS: Record<string, string> = {
  text: "bg-blue-100 text-blue-800",
  number: "bg-green-100 text-green-800",
  date: "bg-yellow-100 text-yellow-800",
  time: "bg-pink-100 text-pink-800",
  boolean: "bg-purple-100 text-purple-800",
  email: "bg-orange-100 text-orange-800",
  freetext: "bg-slate-100 text-slate-600",
};

const TYPE_HINTS: Record<string, string> = {
  text: "Beliebiger nicht-leerer Text",
  number: "Ganze Zahlen oder Dezimalzahlen (z.B. 42, -3.14)",
  date: "Datum: YYYY-MM-DD oder DD.MM.YYYY",
  time: "Uhrzeit: HH:MM oder HH:MM:SS",
  boolean: "true / false / 1 / 0 / ja / nein",
  email: "Gueltige E-Mail-Adresse",
  freetext: "Beliebiger Text, keine Validierung",
};

function DataClassCard({ dc, onDeleted }: { dc: DataClass; onDeleted: () => void }) {
  const [values, setValues] = useState<DataClassValue[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [newVal, setNewVal] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const loadValues = async () => {
    const vals = await dataclassApi.listValues(dc.id);
    setValues(vals);
  };

  const handleExpand = () => {
    if (!expanded) loadValues();
    setExpanded(!expanded);
  };

  const handleAddValue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVal.trim()) return;
    setAdding(true);
    setAddError("");
    try {
      await dataclassApi.addValue(dc.id, newVal.trim());
      setNewVal("");
      await loadValues();
      // Fokus bleibt im Eingabefeld fuer schnelle Mehrfach-Eingabe (UX)
      setTimeout(() => inputRef.current?.focus(), 50);
    } catch (err: unknown) {
      setAddError(String(err));
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteValue = async (vid: number) => {
    await dataclassApi.deleteValue(vid);
    setValues((prev) => prev.filter((v) => v.id !== vid));
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-slate-800">{dc.name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[dc.value_type] ?? "bg-slate-100 text-slate-600"}`}>
              {dc.value_type}
            </span>
          </div>
          {dc.description && <p className="text-xs text-slate-500 mb-2">{dc.description}</p>}
          <p className="text-xs text-slate-400 italic">{TYPE_HINTS[dc.value_type]}</p>
        </div>
        <button
          onClick={() => { if (window.confirm("Datenklasse löschen?")) onDeleted(); }}
          className="text-red-400 hover:text-red-600 text-xs border border-red-200 rounded-lg px-2 py-1">
          Löschen
        </button>
      </div>

      <button onClick={handleExpand}
        className="mt-3 text-sm text-sky-600 hover:underline flex items-center gap-1">
        {expanded ? "▲" : "▼"} {values.length > 0 ? `${values.length} Wert(e)` : "Werte anzeigen/bearbeiten"}
      </button>

      {expanded && (
        <div className="mt-3">
          {values.length > 0 ? (
            <div className="flex flex-wrap gap-1 mb-3">
              {values.map((v) => (
                <span key={v.id}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-sm">
                  {v.value}
                  <button onClick={() => handleDeleteValue(v.id)}
                    className="text-slate-300 hover:text-red-500 ml-1 text-xs">✕</button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 mb-2">Noch keine Werte.</p>
          )}
          <form onSubmit={handleAddValue} className="flex gap-2">
            <input
              ref={inputRef}
              value={newVal}
              onChange={(e) => setNewVal(e.target.value)}
              placeholder={`Neuer Wert (${dc.value_type})...`}
              className="flex-1 px-2 py-1 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <button type="submit" disabled={adding || !newVal.trim()}
              className="px-3 py-1 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50">
              +
            </button>
          </form>
          {addError && <p className="text-xs text-red-600 mt-1">{addError}</p>}
        </div>
      )}
    </div>
  );
}

export default function DataClassesPage() {
  const [dataclasses, setDataclasses] = useState<DataClass[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("text");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setDataclasses(await dataclassApi.list());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setCreateError("");
    try {
      await dataclassApi.create({ name: newName.trim(), value_type: newType, description: newDesc.trim() || undefined });
      setNewName("");
      setNewDesc("");
      await load();
    } catch (err: unknown) {
      setCreateError(String(err));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    await dataclassApi.delete(id);
    setDataclasses((prev) => prev.filter((dc) => dc.id !== id));
    setSelected((prev) => { const s = new Set(prev); s.delete(id); return s; });
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id); else s.add(id);
      return s;
    });
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    setBulkDeleting(true);
    try {
      await dataclassApi.bulkDelete([...selected]);
      setSelected(new Set());
      await load();
    } finally {
      setBulkDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800">G.R.E.A.T. – Datenklassen</h1>
        <div className="flex gap-2">
          <a href="/app" className="text-sm text-slate-500 hover:text-sky-600 border border-slate-200 rounded-lg px-3 py-1">
            Projekte
          </a>
          <a href="/ui/dataclasses" className="text-sm text-slate-500 hover:text-sky-600 border border-slate-200 rounded-lg px-3 py-1">
            Klassische Ansicht
          </a>
          <a href="/docs" target="_blank" className="text-sm text-slate-500 hover:text-sky-600 border border-slate-200 rounded-lg px-3 py-1">
            API-Docs
          </a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Neue Datenklasse anlegen */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Neue Datenklasse anlegen</h2>
          <p className="text-sm text-slate-500 mb-4">
            Datenklassen sind wiederverwendbare Äquivalenzklassen – z.B. "Statuswerte" mit den Werten "Aktiv", "Inaktiv", "Gesperrt".
            Du kannst sie direkt in Kategorien eines Projekts einfügen.
          </p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-[2fr_1fr_2fr_auto] gap-3 items-end">
            <div>
              <label className="block text-xs text-slate-500 mb-1 font-medium">Name</label>
              <input value={newName} onChange={(e) => setNewName(e.target.value)}
                placeholder="z.B. Statuswerte, Gewichtsklassen..." required
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1 font-medium">Typ</label>
              <select value={newType} onChange={(e) => setNewType(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400">
                {VALUE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1 font-medium">Beschreibung (optional)</label>
              <input value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Wofür wird diese Klasse genutzt?"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400" />
            </div>
            <button type="submit" disabled={creating || !newName.trim()}
              className="px-4 py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50 font-medium">
              {creating ? "..." : "Anlegen"}
            </button>
          </form>
          {createError && <p className="text-sm text-red-600 mt-2">{createError}</p>}
          <p className="text-xs text-slate-400 mt-2">Tipp: {TYPE_HINTS[newType]}</p>
        </div>

        {/* Datenklassen-Liste */}
        <h2 className="text-base font-semibold text-slate-700 mb-3">Vorhandene Datenklassen ({dataclasses.length})</h2>
        {loading ? (
          <p className="text-slate-400 text-sm">Lade...</p>
        ) : dataclasses.length === 0 ? (
          <div className="text-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl">
            <p className="text-lg mb-1">📚</p>
            <p className="font-medium">Noch keine Datenklassen</p>
            <p className="text-sm mt-1">Lege deine erste wiederverwendbare Äquivalenzklasse an</p>
          </div>
        ) : (
          <>
            {/* Auswahl-Toolbar: immer sichtbar wenn Datenklassen vorhanden */}
            {dataclasses.length > 0 && (
              <div className="flex items-center gap-2 mb-2 px-1">
                <button
                  onClick={() => {
                    const deletable = dataclasses.filter((dc) => !dc.is_system);
                    setSelected(selected.size === deletable.length ? new Set() : new Set(deletable.map((dc) => dc.id)));
                  }}
                  className="text-xs px-2 py-1 border border-slate-300 rounded hover:bg-slate-50"
                >
                  {selected.size === dataclasses.filter((dc) => !dc.is_system).length && selected.size > 0
                    ? "Keinen markieren"
                    : "Alle markieren"}
                </button>
                <button
                  onClick={() => setSelected(new Set(dataclasses.filter((dc) => !dc.is_system && !selected.has(dc.id)).map((dc) => dc.id)))}
                  className="text-xs px-2 py-1 border border-slate-300 rounded hover:bg-slate-50"
                >
                  Markierung umkehren
                </button>
              </div>
            )}

            {selected.size > 0 && (
              <div className="flex items-center gap-3 mb-3 px-1">
                <span className="text-sm text-slate-600">{selected.size} ausgewählt</span>
                <button
                  onClick={handleBulkDelete}
                  disabled={bulkDeleting}
                  className="px-3 py-1 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
                >
                  {bulkDeleting ? "Löschen..." : "Auswahl löschen"}
                </button>
                <button
                  onClick={() => setSelected(new Set())}
                  className="px-3 py-1 text-sm border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                  Abbrechen
                </button>
              </div>
            )}
            {/* REQ-3010: System-Datenklassen Sektion */}
            {dataclasses.some((dc) => dc.is_system) && (
              <div className="mb-6">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-1">
                  System-Datenklassen (schreibgeschützt)
                </h3>
                <div className="grid grid-cols-1 gap-3">
                  {dataclasses.filter((dc) => dc.is_system).map((dc) => (
                    <div key={dc.id} className="flex items-start gap-2">
                      <div className="w-4 mt-3" />
                      <div className="flex-1">
                        <DataClassCard dc={dc} onDeleted={() => handleDelete(dc.id)} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* REQ-3010: User-Datenklassen Sektion */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-1">
                Meine Datenklassen
              </h3>
              {dataclasses.filter((dc) => !dc.is_system).length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">Noch keine eigenen Datenklassen angelegt.</p>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {dataclasses.filter((dc) => !dc.is_system).map((dc) => (
                    <div key={dc.id} className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={selected.has(dc.id)}
                        onChange={() => toggleSelect(dc.id)}
                        className="mt-3 h-4 w-4 rounded border-slate-300 text-blue-600"
                      />
                      <div className="flex-1">
                        <DataClassCard dc={dc} onDeleted={() => handleDelete(dc.id)} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}