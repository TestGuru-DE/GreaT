---
name: great-combinatorics-validation
description: Use this skill in the G.R.E.A.T. project for combinatorics algorithms, pairwise/IPOG, all-combinations, each-choice, linear expansion, risk-based ordering, orthogonal arrays, boundary value analysis, ISTQB terminology, mathematical correctness, coverage metrics, or test-case generation strategy decisions.
argument-hint: "<strategy, REQ-ID, algorithm, or failing test>"
---

# GREAT Combinatorics Validation

Use this skill for any test-case generation algorithm or combinatorial testing decision.

## Required context

Inspect:

1. `Agenten und basisinfos/requirements_v1.1.md` for REQ-080x and related test-design REQs.
2. `src/combinatorics/` for existing algorithms.
3. `src/core/rules/` for rule handling.
4. `tests/` for existing algorithm and rule tests.
5. `documentation/decision-log.md` for ADR constraints.

## Canonical algorithm contract

All generation strategies must preserve a clear contract equivalent to:

```python
def generate(categories: list[dict], rules: list[dict] | None = None) -> list[dict]:
    ...
```

Output must be deterministic unless a documented seed is part of the contract.

## Validation dimensions

### Functional correctness

- Each Choice: each value appears at least once if not blocked by rules.
- Linear Expansion: one baseline plus one deviation per non-default value.
- All Combinations: complete Cartesian product subject to valid constraints.
- Pairwise/IPOG: each valid pair across category pairs appears at least once.
- Risk-based ordering: highest calculated risk appears first without losing required coverage.
- Orthogonal arrays: coverage strength and fallback are explicit.
- Boundary value analysis: min, min+1, nominal, max-1, max are generated where types allow.

### Constraint correctness

Rules must be handled consistently:

- Exclude/forbidden combinations are never returned.
- Dependency rules are satisfied.
- Combine rules are enforced without producing duplicates.
- Invalid rule definitions fail clearly.

### Mathematical evidence

For non-trivial algorithms, require:

- Invariant explanation in docstring or documentation.
- Complexity estimate.
- Determinism statement.
- Coverage proof or verification function in tests.

## TDD requirements

Before implementation, create tests for:

1. Minimal categories.
2. Unequal category sizes.
3. Empty or single-value categories.
4. Rules/constraints.
5. Deterministic order.
6. Known small expected output.
7. Coverage property verification.

## Output format

```markdown
# Kombinatorik-Review

## Strategie
...

## Betroffene REQs
REQ-...

## Korrektheitskriterien
- ...

## Testplan RED zuerst
- tests/test_...

## Mathematische Pruefung
- Invariante: ...
- Komplexitaet: ...
- Determinismus: ...
- Coverage-Nachweis: ...

## Ergebnis
freigeben | nacharbeiten | blockiert
```

