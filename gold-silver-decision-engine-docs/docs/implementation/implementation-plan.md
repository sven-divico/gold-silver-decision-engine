# Implementation Plan

## Goal
Scaffold and implement the MVP in small, reviewable steps.

## Milestone 1 — Project Scaffold
Create:
- `app/`
- `app/routes/`
- `app/services/`
- `app/templates/`
- `app/static/`
- `tests/`
- `scripts/`

Add:
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `README.md`

## Milestone 2 — FastAPI App Bootstrapping
Implement:
- `app/main.py`
- root route
- calculator route
- base template
- homepage template
- calculator template placeholder

Definition of done:
- application starts locally
- routes render HTML

## Milestone 3 — Settings and Database
Implement:
- config object
- database session
- initial models for price history
- database initialization script

Definition of done:
- SQLite database can be created locally
- app can access database session

## Milestone 4 — Core Domain Logic
Implement service functions for:
- silver VAT calculation
- break-even appreciation calculation
- gold/silver ratio calculation
- ratio status classification

Definition of done:
- domain functions are testable in isolation
- tests exist and pass

## Milestone 5 — Calculator UI
Implement:
- HTML form for scenario inputs
- result rendering
- assumption text
- validation feedback

Definition of done:
- user can enter values and receive results in browser

## Milestone 6 — Historical Data Support
Implement:
- price history model
- sample CSV or seed loader
- ratio computation over historical data
- simple chart rendering

Definition of done:
- app shows a historical ratio chart from stored data

## Milestone 7 — Cleanup and Hardening
Add:
- error handling
- clearer formatting
- readme improvements
- basic CI

Definition of done:
- repository is usable by a new developer with minimal setup friction

## Commit strategy
Use one commit per milestone or one commit per coherent sub-step inside a milestone.
