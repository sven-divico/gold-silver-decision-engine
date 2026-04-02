# Repository Structure

```text
gold-silver-decision-engine/
├─ README.md
├─ README_Codex_Start_Here.md
├─ .gitignore
├─ .env.example
├─ pyproject.toml
├─ docs/
│  ├─ strategy/
│  │  └─ thesis.md
│  ├─ product/
│  │  └─ calculator-spec.md
│  ├─ decisions/
│  │  └─ 0001-initial-stack.md
│  └─ implementation/
│     ├─ implementation-plan.md
│     └─ repo-structure.md
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ models.py
│  ├─ routes/
│  │  ├─ __init__.py
│  │  ├─ web.py
│  │  └─ api.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ pricing.py
│  │  ├─ ratio.py
│  │  └─ signals.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ index.html
│  │  └─ calculator.html
│  └─ static/
│     ├─ css/
│     └─ js/
├─ scripts/
│  ├─ init_db.py
│  └─ seed_sample_data.py
└─ tests/
   ├─ test_ratio.py
   └─ test_pricing.py
```

## Notes
- Keep the first version intentionally narrow.
- Avoid adding a separate frontend framework until there is a clear need.
- Keep business logic inside `app/services/`.
- Keep routes thin.
