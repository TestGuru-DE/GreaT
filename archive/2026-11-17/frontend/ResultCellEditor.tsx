// REQ-4016: Editor für Ergebnis-Felder (Expected Result)
import { useState } from "react";

interface Props {
  value: string;
  options: string[];
  categoryId: number;
  testCaseId: number | string;
  onSave: (categoryId: number, testCaseId: number | string, newValue: string) => Promise<void>;
}

export default function ResultCellEditor({ value, options, categoryId, testCaseId, onSave }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState(value);

  const handleSave = async () => {
    if (inputValue === value) {
      setIsEditing(false);
      return;
    }
    try {
      // TODO: Später mit echtem API-Call ersetzen
      await onSave(categoryId, testCaseId, inputValue);
      setIsEditing(false);
    } catch {
      // Error handling später
    }
  };

  if (!isEditing && !value) {
    // Leeres Feld – orange markiert
    return (
      <div
        onClick={() => setIsEditing(true)}
        className="px-2 py-1 bg-orange-50 border border-orange-200 rounded cursor-pointer hover:bg-orange-100 text-slate-400 italic min-h-6 flex items-center"
      >
        -
      </div>
    );
  }

  if (!isEditing) {
    // Angezeigter Wert
    const isNewValue = !options.includes(value) && value;
    return (
      <div
        onClick={() => setIsEditing(true)}
        className={`px-2 py-1 rounded cursor-pointer min-h-6 flex items-center justify-between gap-2 ${
          isNewValue
            ? "bg-blue-50 border border-blue-200 hover:bg-blue-100"
            : "bg-white border border-slate-200 hover:bg-slate-50"
        }`}
      >
        <span className="text-slate-700">{value}</span>
        {isNewValue && <span className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded whitespace-nowrap">NEU</span>}
      </div>
    );
  }

  // Edit-Modus
  return (
    <div className="flex gap-1">
      <select
        value={value.includes(inputValue) ? inputValue : ""}
        onChange={(e) => {
          setInputValue(e.target.value);
        }}
        onBlur={handleSave}
        autoFocus
        className="px-2 py-1 text-sm border border-sky-400 rounded focus:outline-none focus:ring-2 focus:ring-sky-400 flex-1"
      >
        <option value="">-- Auswählen --</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => {
          setInputValue(e.target.value);
        }}
        onBlur={handleSave}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSave();
          if (e.key === "Escape") setIsEditing(false);
        }}
        placeholder="Freitext oder Dropdown"
        className="px-2 py-1 text-sm border border-sky-400 rounded focus:outline-none focus:ring-2 focus:ring-sky-400 flex-1 ml-1"
      />
    </div>
  );
}
