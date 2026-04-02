# Codex Task

Use this file as the direct implementation brief.

## Objective
Scaffold the initial version of the Gold & Silver Decision Engine as a Python web application.

## Build requirements
Create a working local application using:
- FastAPI
- Jinja2 templates
- SQLite
- SQLAlchemy
- pytest

## The application must include
1. A homepage
2. A calculator page
3. A form that accepts:
   - gold amount in EUR
   - silver net amount in EUR
   - silver VAT rate
   - optional future price change in percent
4. Calculation logic for:
   - silver VAT amount
   - silver total acquisition cost
   - required appreciation to offset silver VAT
   - gold/silver ratio
   - ratio status
5. A simple result display in HTML
6. Unit tests for the core calculation functions

## Implementation constraints
- Keep the UI simple and clean
- Use server-rendered HTML
- No authentication
- No external API integration in the first pass
- Create seed/sample data support for later charting
- Organize domain logic in testable service modules

## Suggested first files to create
- `pyproject.toml`
- `app/main.py`
- `app/config.py`
- `app/db.py`
- `app/models.py`
- `app/routes/web.py`
- `app/services/pricing.py`
- `app/services/ratio.py`
- `app/templates/base.html`
- `app/templates/index.html`
- `app/templates/calculator.html`
- `tests/test_pricing.py`
- `tests/test_ratio.py`

## Acceptance criteria
- Running the app locally should show the homepage and calculator page
- Form submission should render calculation results
- Tests should pass
- The codebase should match the structure defined in `docs/implementation/repo-structure.md`
