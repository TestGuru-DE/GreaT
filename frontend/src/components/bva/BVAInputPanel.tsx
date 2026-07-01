// REQ-3041, REQ-3043: BVAInputPanel – Min/Max-Felder + Radio-Buttons
import type { BVAConfig } from "../../lib/bva-calc";
import { validateBVAConfig } from "../../lib/bva-calc";

interface BVAInputPanelProps {
  config: BVAConfig;
  onChange: (config: BVAConfig) => void;
}

export function BVAInputPanel({ config, onChange }: BVAInputPanelProps) {
  const errors = validateBVAConfig(config);

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

  return (
    <div className="space-y-4">
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
