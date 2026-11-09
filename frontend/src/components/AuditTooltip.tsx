// REQ-4024: Audit-Trail-Tooltip (wer hat zuletzt geaendert)
// Teil von EPIC-18 (Multi-User) / Sprint 13
//
// Zeigt dezent ein Tooltip mit "Zuletzt geaendert von X am Y"
// wenn der Mauszeiger ueber dem Element schwebt.

interface AuditTooltipProps {
  /** Username des letzten Aenderers (optional) */
  lastModifiedBy?: string;
  /** ISO-Datum der letzten Aenderung (optional) */
  lastModifiedAt?: string;
  /** Art der Entitaet (z.B. "Kategorie", "Testfall", "Wert") */
  entityType: string;
}

export default function AuditTooltip({
  lastModifiedBy,
  lastModifiedAt,
  entityType,
}: AuditTooltipProps) {
  if (!lastModifiedBy && !lastModifiedAt) return null;

  const formattedDate = lastModifiedAt
    ? new Date(lastModifiedAt).toLocaleString("de-DE")
    : null;

  const tooltipText = [
    lastModifiedBy ? `Geaendert von: ${lastModifiedBy}` : null,
    formattedDate ? `Am: ${formattedDate}` : null,
  ]
    .filter(Boolean)
    .join(" | ");

  return (
    <div className="relative group inline-block">
      <span className="text-xs text-theme-text-secondary cursor-help border-b border-dotted border-theme-text-secondary">
        {entityType}
      </span>
      <div className="invisible group-hover:visible absolute z-10 bottom-full left-0 mb-2 px-3 py-2 text-xs text-white bg-gray-800 rounded shadow-lg whitespace-nowrap">
        {tooltipText}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
      </div>
    </div>
  );
}