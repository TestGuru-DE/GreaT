// BUG C-02: Dialog fuer Datum/Uhrzeit/Stringlaenge war unbrauchbar
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "de" } }),
}));

const generateExtended = vi.fn();
vi.mock("../../../api/bva", () => ({
  bvaApi: {
    generateMultiRange: vi.fn(),
    generateExtended: (...a: unknown[]) => generateExtended(...a),
  },
}));

import { BVADialog } from "../BVADialog";

const props = { isOpen: true, categoryId: 5, categoryName: "Termin", projectId: 1, onClose: vi.fn(), onApply: vi.fn() };

function choose(type: string) {
  fireEvent.change(screen.getByLabelText("bvaDialog.dataType.label"), { target: { value: type } });
}
function setRange(min: string, max: string) {
  const inputs = screen.getAllByRole("textbox");
  fireEvent.change(inputs[0], { target: { value: min } });
  fireEvent.change(inputs[1], { target: { value: max } });
}
const applyButton = () => screen.getByText("bvaDialog.apply").closest("button")!;

describe("BVADialog erweiterte Datentypen (C-02)", () => {
  beforeEach(() => {
    generateExtended.mockReset();
    generateExtended.mockResolvedValue({ category_id: 5, values: [{ value: "2024-01-01", is_error: false, vtype: "date", label: "" }] });
  });

  it("gueltiges Datum wird nicht als ungueltige Zahl blockiert", async () => {
    render(<BVADialog {...props} />);
    choose("date");
    setRange("2024-01-01", "2024-12-31");
    expect(screen.queryByText(/numerischer Wert/)).toBeNull();
    expect(applyButton()).not.toBeDisabled();
    fireEvent.click(applyButton());
    await waitFor(() => expect(generateExtended).toHaveBeenCalledTimes(1));
    const [cid, req] = generateExtended.mock.calls[0];
    expect(cid).toBe(5);
    expect(req.type).toBe("date");
    expect(req.ranges).toEqual([{ min_val: "2024-01-01", max_val: "2024-12-31", allowed: true }]);
    expect(req.options.format).toBe("iso");
    expect(props.onApply).toHaveBeenCalledWith(["2024-01-01"]);
  });

  it("Format und Zusatzwerte werden mit Backend-Schluesseln gesendet", async () => {
    render(<BVADialog {...props} />);
    choose("date");
    setRange("2024-01-01", "2024-12-31");
    fireEvent.change(screen.getByLabelText("bvaDialog.options.format"), { target: { value: "de" } });
    fireEvent.click(screen.getByLabelText("bvaDialog.options.extraLabels.leap_year"));
    fireEvent.click(screen.getByLabelText("bvaDialog.options.extraLabels.month_ends"));
    fireEvent.click(applyButton());
    await waitFor(() => expect(generateExtended).toHaveBeenCalled());
    const opts = generateExtended.mock.calls[0][1].options;
    expect(opts.format).toBe("de");
    expect(opts.extras).toMatchObject({ leap_year: true, month_ends: true, invalid_date: false });
    expect(Object.keys(opts.extras).some((k) => /[A-Z]/.test(k))).toBe(false);
  });

  it("ungueltiges Datum zeigt Formathinweis und sperrt Anwenden", () => {
    render(<BVADialog {...props} />);
    choose("date");
    setRange("2023-02-29", "2023-12-31");
    expect(screen.getByText(/JJJJ-MM-TT erwartet/)).toBeInTheDocument();
    expect(applyButton()).toBeDisabled();
  });

  it("Uhrzeit: Format und Schrittweite waehlbar, Bereich ueber Mitternacht erlaubt", async () => {
    render(<BVADialog {...props} />);
    choose("time");
    setRange("22:00", "06:00");
    fireEvent.change(screen.getByLabelText("bvaDialog.options.format"), { target: { value: "HH:MM:SS" } });
    fireEvent.change(screen.getByLabelText("bvaDialog.options.step"), { target: { value: "second" } });
    fireEvent.click(applyButton());
    await waitFor(() => expect(generateExtended).toHaveBeenCalled());
    expect(generateExtended.mock.calls[0][1].options).toMatchObject({ format: "HH:MM:SS", step: "second" });
  });

  it("Stringlaenge: Zeichenvorrat waehlbar", async () => {
    render(<BVADialog {...props} />);
    choose("strlen");
    setRange("1", "20");
    fireEvent.change(screen.getByLabelText("bvaDialog.options.charset"), { target: { value: "unicode" } });
    fireEvent.click(applyButton());
    await waitFor(() => expect(generateExtended).toHaveBeenCalled());
    expect(generateExtended.mock.calls[0][1].options.charset).toBe("unicode");
  });

  it("Doppelklick auf Anwenden sendet nur einmal", async () => {
    let resolve!: (v: unknown) => void;
    generateExtended.mockReturnValue(new Promise((r) => { resolve = r; }));
    render(<BVADialog {...props} />);
    choose("strlen");
    setRange("1", "5");
    const button = applyButton();
    fireEvent.click(button);
    fireEvent.click(button);
    resolve({ category_id: 5, values: [] });
    await waitFor(() => expect(generateExtended).toHaveBeenCalledTimes(1));
  });
});
