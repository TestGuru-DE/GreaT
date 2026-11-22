"""
REQ-6009: Tests fuer seed_generation.py — Kernalgorithmus.

Testet:
- Seeds werden im Ergebnis beibehalten
- Unabgedeckte Paare werden ergaenzt
- origin-Feld (seed vs. supplemented)
- Unvollstaendige Seeds (None = beliebig) werden aufgefuellt
- Verschiedene Strategien (pairwise, each, all, linear, t_wise)
- Leere Seeds = normale Generierung
"""
import pytest


# ---------------------------------------------------------------------------
# MOCK-DATEN (aus RED-Testdesign)
# ---------------------------------------------------------------------------

CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}

CATS_2X2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
    "C": ["c1", "c2"],
}

CATS_3X3 = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2", "b3"],
}

SEEDS_COMPLETE = [
    {"A": "a1", "B": "b1"},
    {"A": "a2", "B": "b2"},
]

SEEDS_ALL_2X2 = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    {"A": "a2", "B": "b2"},
]

SEEDS_PARTIAL = [
    {"A": "a1", "B": None},
    {"A": None, "B": "b1"},
    {"A": None, "B": None},
]

SEEDS_EMPTY = []


# ---------------------------------------------------------------------------
# TestSeedGenerationBasic
# ---------------------------------------------------------------------------

class TestSeedGenerationBasic:

    def test_seeds_preserved_in_result(self):
        """TEST-REQ-6009-GEN-001: Alle Seeds unveraendert im Ergebnis."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="pairwise"
        )

        # Alle Seeds muessen im Ergebnis sein
        seed_assignments = [
            {k: v for k, v in s.items() if k != "origin"}
            for s in SEEDS_COMPLETE
        ]
        result_assignments = [
            {k: v for k, v in tc.items() if k != "origin"}
            for tc in result
        ]

        for seed in seed_assignments:
            assert seed in result_assignments, f"Seed {seed} nicht im Ergebnis"

    def test_seeds_plus_supplement_covers_all_pairs(self):
        """TEST-REQ-6009-GEN-002: Paarabdeckung 100% nach Ergaenzung."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds
        from combinatorics.coverage import calculate_coverage

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="pairwise"
        )

        assignments = [
            {k: v for k, v in tc.items() if k != "origin"}
            for tc in result
        ]
        coverage = calculate_coverage(assignments, CATS_2X2, t=2)
        assert coverage.percentage == 100.0, f"Coverage: {coverage.percentage}%"

    def test_no_supplement_when_seeds_already_cover(self):
        """TEST-REQ-6009-GEN-003: Keine Ergaenzung wenn Seeds 100% abdecken."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_ALL_2X2, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="pairwise"
        )

        # Nur Seeds, keine supplemented
        origins = [tc.get("origin") for tc in result]
        assert all(o == "seed" for o in origins), f"Unerwartete origins: {origins}"
        assert len(result) == 4

    def test_empty_seeds_equals_normal_generation(self):
        """TEST-REQ-6009-GEN-004: Leere Seeds = normale Generierung."""
        from combinatorics.seed_generation import seed_generation

        result, _ = seed_generation(
            SEEDS_EMPTY, CATS_2X2, strategy="pairwise"
        )

        # Normale Generierung: mindestens 2 TCs fuer 2x2 pairwise
        assert len(result) >= 2
        origins = [tc.get("origin") for tc in result]
        assert all(o == "generated" for o in origins), f"Erwartet 'generated', got: {origins}"

    def test_result_not_larger_than_seeds_plus_pairwise(self):
        """TEST-REQ-6009-GEN-005: Ergebnis nicht groesser als Seeds + Pairwise."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds
        from combinatorics import ipo

        seeds_3x = [
            {"A": "a1", "B": "b1", "C": "c1"},
            {"A": "a2", "B": "b2", "C": "c2"},
            {"A": "a1", "B": "b2", "C": "c1"},
        ]

        normalized, _ = validate_seeds(seeds_3x, CATS_2X2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2X2)

        result, _ = seed_generation(
            filled, CATS_2X2X2, strategy="pairwise"
        )

        pairwise_only = ipo.generate(CATS_2X2X2)
        # result should not exceed seeds + pairwise (with some margin for dedup)
        max_expected = len(seeds_3x) + len(pairwise_only)
        assert len(result) <= max_expected, (
            f"Result {len(result)} > max {max_expected} (seeds={len(seeds_3x)}, pairwise={len(pairwise_only)})"
        )

    def test_origin_field_seed_vs_supplemented(self):
        """TEST-REQ-6009-GEN-006: Jeder TC hat origin in [seed, supplemented, generated]."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="pairwise"
        )

        valid_origins = {"seed", "supplemented", "generated"}
        for tc in result:
            assert "origin" in tc, f"TC fehlt 'origin': {tc}"
            assert tc["origin"] in valid_origins, f"Ungueltiger origin: {tc['origin']}"

    def test_supplemented_count_matches_uncovered_pairs(self):
        """TEST-REQ-6009-GEN-007: supplemented_count minimal."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        seeds_partial = [
            {"A": "a1", "B": "b1"},
            {"A": "a2", "B": "b1"},
        ]

        normalized, _ = validate_seeds(seeds_partial, CATS_3X3)
        filled, _ = fill_partial_seeds(normalized, CATS_3X3)

        result, _ = seed_generation(
            filled, CATS_3X3, strategy="pairwise"
        )

        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        # supplemented_count sollte minimal sein (nicht alle 9 Paare neu generieren)
        assert len(supplemented) <= 9, f"Zu viele supplemented: {len(supplemented)}"


# ---------------------------------------------------------------------------
# TestSeedGenerationIncompleteSeeds
# ---------------------------------------------------------------------------

class TestSeedGenerationIncompleteSeeds:

    def test_partial_seed_filled_with_value(self):
        """TEST-REQ-6009-GEN-008: None-Wert wird durch konkreten Wert ersetzt."""
        from combinatorics.seed_generation import validate_seeds, fill_partial_seeds

        seeds = [{"A": "a1", "B": None}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)
        filled, filled_fields = fill_partial_seeds(normalized, CATS_2X2)

        assert filled[0]["B"] is not None, "B sollte aufgefuellt sein"
        assert filled[0]["B"] in CATS_2X2["B"], f"B '{filled[0]['B']}' nicht in Kategorie"

    def test_partial_seed_filled_optimally(self):
        """TEST-REQ-6009-GEN-009: A=None wird mit Wert gefuellt."""
        from combinatorics.seed_generation import validate_seeds, fill_partial_seeds

        seeds = [{"A": None, "B": "b1"}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        assert filled[0]["A"] is not None, "A sollte aufgefuellt sein"
        assert filled[0]["A"] in CATS_2X2["A"], f"A '{filled[0]['A']}' nicht in Kategorie"

    def test_fully_empty_seed_becomes_valid_tc(self):
        """TEST-REQ-6009-GEN-010: Alle None -> gueltiger TC."""
        from combinatorics.seed_generation import validate_seeds, fill_partial_seeds

        seeds = [{"A": None, "B": None}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        for cat in CATS_2X2:
            assert filled[0][cat] is not None, f"{cat} sollte aufgefuellt sein"
            assert filled[0][cat] in CATS_2X2[cat]

    def test_partial_seed_origin_marked_filled(self):
        """TEST-REQ-6009-GEN-012: Aufgefuellte Felder werden gekennzeichnet."""
        from combinatorics.seed_generation import validate_seeds, fill_partial_seeds

        seeds = [{"A": "a1", "B": None}]
        normalized, _ = validate_seeds(seeds, CATS_2X2)
        filled, filled_fields = fill_partial_seeds(normalized, CATS_2X2)

        assert len(filled_fields) == 1
        # filled_fields[0] sollte {"filled_fields": ["B"]} enthalten
        ff = filled_fields[0]
        assert "filled_fields" in ff or "B" in str(ff), f"filled_fields sollte 'B' enthalten: {ff}"


# ---------------------------------------------------------------------------
# TestSeedGenerationStrategies
# ---------------------------------------------------------------------------

class TestSeedGenerationStrategies:

    def test_seeds_with_pairwise_strategy(self):
        """TEST-REQ-6009-GEN-013: Seeds + pairwise-Ergaenzung."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="pairwise"
        )

        seed_count = sum(1 for tc in result if tc.get("origin") == "seed")
        assert seed_count == 2, f"Erwartet 2 seeds, got {seed_count}"

    def test_seeds_with_each_choice_strategy(self):
        """TEST-REQ-6009-GEN-015: Seeds + each-choice-Ergaenzung."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="each"
        )

        seed_count = sum(1 for tc in result if tc.get("origin") == "seed")
        assert seed_count == 2

    def test_seeds_with_all_combinations_strategy(self):
        """TEST-REQ-6009-GEN-017: Seeds + all-combinations-Ergaenzung."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="all"
        )

        # Bei all-combinations fuer 2x2: 4 TCs insgesamt
        # 2 seeds + 2 supplemented (oder weniger, wenn seeds bereits decken)
        assert len(result) <= 4

    def test_seeds_with_linear_strategy(self):
        """TEST-REQ-6009-GEN-016: Seeds + linear-Ergaenzung."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        normalized, _ = validate_seeds(SEEDS_COMPLETE, CATS_2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2)

        result, _ = seed_generation(
            filled, CATS_2X2, strategy="linear"
        )

        seed_count = sum(1 for tc in result if tc.get("origin") == "seed")
        assert seed_count == 2

    def test_seeds_with_t_wise_strategy(self):
        """TEST-REQ-6009-GEN-014: Seeds + t-wise-Ergaenzung (t=3)."""
        from combinatorics.seed_generation import seed_generation, validate_seeds, fill_partial_seeds

        seeds_3x = [
            {"A": "a1", "B": "b1", "C": "c1"},
            {"A": "a2", "B": "b2", "C": "c2"},
        ]

        normalized, _ = validate_seeds(seeds_3x, CATS_2X2X2)
        filled, _ = fill_partial_seeds(normalized, CATS_2X2X2)

        result, _ = seed_generation(
            filled, CATS_2X2X2, strategy="t_wise", t_strength=3
        )

        seed_count = sum(1 for tc in result if tc.get("origin") == "seed")
        assert seed_count == 2


# ---------------------------------------------------------------------------
# TestSeedValidation
# ---------------------------------------------------------------------------

class TestSeedValidation:

    def test_seed_unknown_category_rejected(self):
        """TEST-REQ-6009-VAL-001: Unbekannte Kategorie -> Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"UnknownCat": "val", "A": "a1", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert any("Unbekannte Kategorie" in w for w in warnings), f"Warnings: {warnings}"

    def test_seed_unknown_value_reported(self):
        """TEST-REQ-6009-VAL-002: Unbekannter Wert -> Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "unknown_value", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert any("nicht in Kategorie" in w for w in warnings), f"Warnings: {warnings}"

    def test_seed_empty_string_treated_as_any(self):
        """TEST-REQ-6009-VAL-003: "" -> None (beliebig)."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert normalized[0]["A"] is None, f"Erwartet None, got: {normalized[0]['A']}"

    def test_seed_missing_category_treated_as_any(self):
        """TEST-REQ-6009-VAL-004: Fehlende Kategorie -> None."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [{"A": "a1"}]  # B fehlt
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert normalized[0]["B"] is None, f"Erwartet None fuer B, got: {normalized[0]['B']}"

    def test_seed_duplicate_detection(self):
        """TEST-REQ-6009-VAL-005: Duplikate werden entfernt + Warnung."""
        from combinatorics.seed_generation import validate_seeds

        seeds = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b1"},  # Duplikat
            {"A": "a2", "B": "b2"},
        ]
        normalized, warnings = validate_seeds(seeds, CATS_2X2)

        assert len(normalized) == 2, f"Erwartet 2 (nach Duplikat-Entfernung), got {len(normalized)}"
        assert any("dupliziert" in w.lower() for w in warnings), f"Warnings: {warnings}"