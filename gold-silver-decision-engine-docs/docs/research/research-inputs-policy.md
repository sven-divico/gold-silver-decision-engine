# Research Inputs Policy

## Purpose
Research documents in this repository are intended to inform:
- product assumptions
- ratio interpretation logic
- explanatory UI copy
- future feature ideas
- data provider evaluation

## Rules
- Research documents are reference inputs, not executable logic
- Calculation formulas must remain explicit in code
- Heuristic thresholds used in the app should be traceable to either:
  - a documented product decision
  - a research note
  - a clearly marked internal heuristic

## MVP usage
In the MVP, research documents may be used to:
- define ratio status labels
- document Germany-specific silver VAT assumptions
- compare free API options
- summarize historical gold/silver cycle patterns

## Constraint
Do not hard-code ambiguous market claims into the application without documenting the assumption in `docs/`.