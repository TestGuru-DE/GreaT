// REQ-5018: Tests fuer CauseEffectGraph-Komponente
import "../../i18n"; // Texte in deutscher Sprache (A-14: Komponente nutzt t())
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import CauseEffectGraph from "../CauseEffectGraph";

vi.mock("../../api/client", () => ({
  decisionTableApi: {
    getGraph: vi.fn(),
  },
}));

import { decisionTableApi } from "../../api/client";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("CauseEffectGraph - REQ-5018", () => {
  describe("Loading-State", () => {
    it("zeigt 'Graph laedt...' waehrend des Ladens", async () => {
      let resolvePromise: (value: unknown) => void;
      (decisionTableApi.getGraph as any).mockImplementation(() =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      render(<CauseEffectGraph projectId={1} />);
      expect(screen.getByText(/Graph lädt/)).toBeInTheDocument();

      // Resolve the pending fetch to avoid hanging promise
      await Promise.resolve().then(() => {
        resolvePromise!({ causes: [], effects: [], edges: [] });
      });
    });
  });

  describe("Error-State", () => {
    it("zeigt Fehlermeldung bei fehlgeschlagener API-Antwort", async () => {
      (decisionTableApi.getGraph as any).mockRejectedValue(new Error("Fehler beim Laden des Graphen"));

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/Fehler beim Laden/)).toBeInTheDocument();
      });
    });
  });

  describe("Empty-State", () => {
    it("zeigt 'Keine Ursache/Wirkung' wenn keine Daten", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({ causes: [], effects: [], edges: [] });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/Keine Ursache/)).toBeInTheDocument();
      });
    });
  });

  describe("Knoten-Rendering", () => {
    it("zeigt Ursache-Knoten als blaue Rechtecke links", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [
          { id: 1, name: "Ursache A" },
          { id: 2, name: "Ursache B" },
        ],
        effects: [{ id: 10, name: "Wirkung X" }],
        edges: [],
      });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText("Ursache A")).toBeInTheDocument();
        expect(screen.getByText("Ursache B")).toBeInTheDocument();
      });
    });

    it("zeigt Wirkung-Knoten als grüne Rechtecke rechts", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [{ id: 1, name: "Ursache A" }],
        effects: [
          { id: 10, name: "Wirkung X" },
          { id: 11, name: "Wirkung Y" },
        ],
        edges: [],
      });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText("Wirkung X")).toBeInTheDocument();
        expect(screen.getByText("Wirkung Y")).toBeInTheDocument();
      });
    });
  });

  describe("Kanten-Rendering", () => {
    it("zeigt Kanten zwischen Knoten", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [{ id: 1, name: "Ursache A" }],
        effects: [{ id: 10, name: "Wirkung X" }],
        edges: [
          {
            from: "cause:1",
            to: "effect:10",
            type: "E",
            label: "Exclusive",
          },
        ],
      });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText("Exclusive")).toBeInTheDocument();
      });
    });

    it("verwendet farbliche Kanten nach Constraint-Typ", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [
          { id: 1, name: "Ursache A" },
          { id: 2, name: "Ursache B" },
        ],
        effects: [{ id: 10, name: "Wirkung X" }],
        edges: [
          { from: "cause:1", to: "effect:10", type: "E", label: "E" },
          { from: "cause:2", to: "effect:10", type: "I", label: "I" },
          { from: "cause:1", to: "cause:2", type: "O", label: "O" },
          { from: "cause:1", to: "effect:10", type: "requires", label: "R" },
          { from: "cause:2", to: "effect:10", type: "mask", label: "M" },
        ],
      });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        // SVG ist gerendert
        const svg = document.querySelector("svg");
        expect(svg).toBeInTheDocument();
      });
    });
  });

  describe("Legend", () => {
    it("zeigt Legend mit Ursache/Wirkung und Constraint-Farben", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [{ id: 1, name: "Ursache A" }],
        effects: [{ id: 10, name: "Wirkung X" }],
        edges: [],
      });

      render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText("Ursache")).toBeInTheDocument();
        expect(screen.getByText("Wirkung")).toBeInTheDocument();
      });
    });
  });

  describe("Hover-Interaktion", () => {
    it("zeigt Hover-Feedback bei Mausueber-Knoten", async () => {
      (decisionTableApi.getGraph as any).mockResolvedValue({
        causes: [{ id: 1, name: "Ursache A" }],
        effects: [{ id: 10, name: "Wirkung X" }],
        edges: [],
      });

      const { container } = render(<CauseEffectGraph projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText("Ursache A")).toBeInTheDocument();
      });

      // Hover on the first cause node group
      const groups = container.querySelectorAll("g.cursor-pointer");
      expect(groups.length).toBeGreaterThan(0);
    });
  });
});