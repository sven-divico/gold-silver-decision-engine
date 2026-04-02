# ADR 0002 — Data Source Strategy for MVP

## Status
Accepted

## Context
The project is a private project and should start with the lowest reasonable operating cost.

The app needs market data for:
- gold prices
- silver prices
- gold/silver ratio history
- later, possibly macro context

At the same time, the first version does not require institutional-grade real-time data or paid vendor commitments.

## Decision
For the MVP:
- prefer free-of-charge data sources
- store imported historical data locally in SQLite
- design the code so that data providers are abstracted behind service modules
- avoid making the first version dependent on any paid API
- allow manually curated research documents to complement the app logic and product assumptions

## Practical interpretation
The first version should support three input modes:

1. Manual input
   - user enters gold and silver prices directly
   - useful for calculator logic and UI development

2. Local historical dataset import
   - CSV or similar file import into SQLite
   - used for charts, ratio analysis, and testing

3. Optional free API integration
   - add one or more free APIs later if useful
   - only if integration remains simple and reliable

## Rationale
This approach is appropriate because:
- it keeps the MVP inexpensive
- it reduces vendor lock-in
- it allows fast progress on product logic and UI
- it supports deterministic local development and testing
- it keeps future migration to paid APIs possible without redesigning the app

## Consequences

### Positive
- no immediate API cost
- faster start
- easier local testing
- less operational dependency
- cleaner architecture if provider abstraction is implemented early

### Negative
- free APIs may have lower reliability or weaker historical depth
- some data may need to be imported manually at first
- data freshness may initially be lower than in a paid setup

## Implementation guidance
- keep provider-specific code in dedicated service modules
- define a simple internal interface for price retrieval and historical series loading
- keep calculation logic independent from the source of the data
- support seeded sample data for development

## Out of scope for MVP
- high-frequency market data
- broker integrations
- paid enterprise-grade market data contracts