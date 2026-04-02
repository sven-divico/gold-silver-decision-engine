# ADR 0001 — Initial Stack

## Status
Accepted

## Context
The product needs a very small first implementation that can be built quickly, understood easily, and extended later with market data ingestion and richer analytics.

## Decision
Use:
- FastAPI for backend application structure
- Jinja2 templates for server-rendered UI
- SQLite for local persistence
- SQLAlchemy for ORM and schema management
- Pydantic settings for configuration
- pytest for tests

## Rationale
This stack is appropriate because:
- FastAPI is lightweight and productive
- server-rendered templates reduce frontend complexity
- SQLite is enough for MVP data volume
- the app can later evolve into a richer API + JS frontend if needed
- the stack is simple for local coding agents to scaffold reliably

## Consequences
### Positive
- fast setup
- low complexity
- easy local development
- easy deployment to simple environments
- straightforward testing

### Negative
- limited frontend interactivity out of the box
- may later require refactoring if product grows significantly
- SQLite is not intended for concurrent multi-user heavy workloads

## Follow-up decisions likely needed
- data vendor choice
- charting library choice
- ORM conventions
- deployment target
