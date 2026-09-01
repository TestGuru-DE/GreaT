// REQ-3041, REQ-3043, REQ-3064: BVAInputPanel – Min/Max-Felder + Multi-Range-Eingabe
import type { BVAConfig } from "../../lib/bva-calc";
import { validateBVAConfig, validateMultiRangeBVAConfig } from "../../lib/bva-calc";

interface BVAInputPanelProps {
  config: BVAConfig;
  onChange: (config: BVAConfig) => void;
}

export function BVAInputPanel({ config, onChange }: BVAInputPanelProps) {
  const hasRanges = Array.isArray(config.ranges) && config.ranges.length > 0;
  const errors = hasRanges
    ? validateMultiRangeBVAConfig(config.ranges ?? [])
    : validateBVAConfig(config);

  const handleMinChange = (val: string) => {
    onChange({ ...config, min: val });
  };

  const handleMaxChange = (val: string) => {
    onChange({ ...config, max: val });
  };

  const handlePointsChange = (pts: 2 | 3 | 4) => {
    onChange({ ...config, pointsPerBoundary: pts });
  };

  const handleErrorCaseChange = (isError: boolean) => {
    onChange({ ...config, markAsErrorCase: isError });
  };

  const updateRange = (index: number, patch: Partial<NonNullable<BVAConfig["ranges"]>[number]>) => {
    const ranges = [...(config.ranges ?? [])];
    ranges[index] = { ...ranges[index], ...patch };
    onChange({
      ...config,
      ranges,
      min: ranges[0]?.minVal ?? config.min,
      max: ranges[0]?.maxVal ?? config.max,
      markAsErrorCase: ranges[0] ? !ranges[0].allowed : config.markAsErrorCase,
    });
  };

  const addRange = () => {
    const ranges = [...(config.ranges ?? [])];
    ranges.push({
      id: `range-${Date.now()}-${ranges.length}`,
      minVal: "",
      maxVal: "",
      allowed: true,
    });
    onChange({ ...config, ranges });
  };

  const removeRange = (index: number) => {
    const ranges = [...(config.ranges ?? [])];
    ranges.splice(index, 1);
    onChange({
      ...config,
      ranges: ranges.length > 0 ? ranges : undefined,
      min: ranges[0]?.minVal ?? "",
      max: ranges[0]?.maxVal ?? "",
      markAsErrorCase: ranges[0] ? !ranges[0].allowed : false,
    });
  };

  const rangeSummary = (minVal: string, maxVal: string) => {
    const minText = minVal.trim() ? minVal : "−∞";
    const maxText = maxVal.trim() ? maxVal : "∞";
    return `${minText} … ${maxText}`;
  };

  return (
    <div className="space-y-4">
      {hasRanges ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-slate-700">
              Bereiche
            </label>
            <button
              type="button"
              onClick={addRange}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100"
            >
              Bereich hinzufügen
            </button>
          </div>
          <div className="space-y-3">
            {(config.ranges ?? []).map((range, idx) => (
              <div key={range.id} className="rounded-lg border border-slate-200 p-3 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs text-slate-500">
                    Bereich {idx + 1}: {rangeSummary(range.minVal, range.maxVal)}
                  </div>
                  {(config.ranges ?? []).length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRange(idx)}
                      className="text-xs text-red-600 hover:text-red-700"
                    >
                      Entfernen
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label
                      htmlFor={`bva-range-min-${range.id}`}
                      className="block text-xs font-medium text-slate-600 mb-1"
                    >
                      Minimum
                    </label>
                    <input
                      id={`bva-range-min-${range.id}`}
                      type="text"
                      inputMode="decimal"
                      value={range.minVal}
                      onChange={(e) => updateRange(idx, { minVal: e.target.value })}
                      placeholder="−∞"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                      autoFocus={idx === 0}
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`bva-range-max-${range.id}`}
                      className="block text-xs font-medium text-slate-600 mb-1"
                    >
                      Maximum
                    </label>
                    <input
                      id={`bva-range-max-${range.id}`}
                      type="text"
                      inputMode="decimal"
                      value={range.maxVal}
                      onChange={(e) => updateRange(idx, { maxVal: e.target.value })}
                      placeholder="∞"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm text-slate-700 self-end pb-2">
                    <input
                      type="checkbox"
                      checked={range.allowed}
                      onChange={(e) => updateRange(idx, { allowed: e.target.checked })}
                      className="w-4 h-4 text-sky-600 focus:ring-2 focus:ring-sky-500"
                    />
                    Erlaubt
                  </label>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          {/* Min/Max-Eingabe */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="bva-min" className="block text-sm font-medium text-slate-700 mb-1">
                Minimum
              </label>
              <input
                id="bva-min"
                type="text"
                inputMode="decimal"
                value={config.min}
                onChange={(e) => handleMinChange(e.target.value)}
                placeholder="z.B. 0 oder 0.1"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                autoFocus
              />
            </div>
            <div>
              <label htmlFor="bva-max" className="block text-sm font-medium text-slate-700 mb-1">
                Maximum
              </label>
              <input
                id="bva-max"
                type="text"
                inputMode="decimal"
                value={config.max}
                onChange={(e) => handleMaxChange(e.target.value)}
                placeholder="z.B. 100 oder 99.9"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              />
            </div>
          </div>

          {/* Erlaubt/Fehlerfall */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Werte markieren als
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="errorCase"
                  checked={!config.markAsErrorCase}
                  onChange={() => handleErrorCaseChange(false)}
                  className="w-4 h-4 text-sky-600 focus:ring-2 focus:ring-sky-500"
                />
                <span className="text-sm text-slate-700">Erlaubte Werte</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="errorCase"
                  checked={config.markAsErrorCase === true}
                  onChange={() => handleErrorCaseChange(true)}
                  className="w-4 h-4 text-sky-600 focus:ring-2 focus:ring-sky-500"
                />
                <span className="text-sm text-slate-700">Fehlerfall (ungültig)</span>
              </label>
            </div>
          </div>
        </>
      )}

      {/* Punkte-Auswahl */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Punkte pro Grenze
        </label>
        <div className="flex gap-4">
          {([2, 3, 4] as const).map((pts) => (
            <label key={pts} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="points"
                checked={config.pointsPerBoundary === pts}
                onChange={() => handlePointsChange(pts)}
                className="w-4 h-4 text-sky-600 focus:ring-2 focus:ring-sky-500"
              />
              <span className="text-sm text-slate-700">{pts} Punkte</span>
            </label>
          ))}
        </div>
      </div>

      {/* Validierungsfehler */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          {errors.map((err, idx) => (
            <p key={idx} className="text-sm text-red-700">
              {err}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
