# Codex Start Here

This repository is intended to be used by a local coding agent to scaffold and implement a Python web app for gold and silver analysis.

## Primary objective
Build a lean first version of a **Gold & Silver Decision Engine** with:
- a Python backend
- a simple web UI
- local persistence
- calculator logic for gold vs silver
- support for later data ingestion from market data APIs

## Working rules for the coding agent
1. Read the files under `docs/` before making implementation decisions.
2. Treat `docs/decisions/` as the architecture source of truth.
3. Implement the smallest working version first.
4. Prefer clarity and maintainability over framework complexity.
5. Keep the first UI server-rendered unless a document explicitly says otherwise.
6. Avoid speculative features not listed in the product spec.
7. Make incremental commits aligned to milestones in `docs/implementation/implementation-plan.md`.

## Target MVP
The MVP should provide:
- homepage
- calculator page
- manual input fields for gold and silver purchase scenarios
- Germany-specific silver VAT logic
- gold/silver ratio display
- SQLite storage for historical price series
- a placeholder structure for later API-based price ingestion

## Recommended stack
- FastAPI
- Jinja2 templates
- SQLite
- SQLAlchemy or SQLModel
- simple CSS or minimal utility styling
- Chart.js or Plotly for a basic ratio chart

## Suggested first execution order
1. Scaffold repository structure.
2. Create FastAPI app and base templates.
3. Create database schema and configuration.
4. Implement calculator domain logic.
5. Build calculator UI.
6. Add sample data loading.
7. Add first historical ratio chart.
8. Add tests for core formulas.

## Definition of done for initial scaffold
- app starts locally
- homepage loads
- calculator page loads
- form submission works
- a result is rendered
- tests pass for core calculation logic
