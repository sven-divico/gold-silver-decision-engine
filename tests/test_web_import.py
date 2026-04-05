from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_import_page_loads() -> None:
    response = client.get("/admin/import")

    assert response.status_code == 200
    assert "Import historical prices from CSV" in response.text
    assert "Recent imports" in response.text


def test_calculator_page_shows_ratio_confidence() -> None:
    response = client.get("/calculator")

    assert response.status_code == 200
    assert "Historical ratio confidence" in response.text


def test_calculator_page_shows_decision_engine_section() -> None:
    response = client.get("/calculator")

    assert response.status_code == 200
    assert "Current recommendation from hypothesis leaderboard" in response.text
    assert "Decision Engine" in response.text


def test_calculator_page_persists_history_filters() -> None:
    response = client.get("/calculator?start_date=2025-01-01&end_date=2025-01-10&overlap_only=true")

    assert response.status_code == 200
    assert 'value="2025-01-01"' in response.text
    assert 'value="2025-01-10"' in response.text
    assert "Use overlapping clean subset only" in response.text


def test_calculator_page_handles_invalid_history_range() -> None:
    response = client.get("/calculator?start_date=2025-02-01&end_date=2025-01-01")

    assert response.status_code == 200
    assert "Start date cannot be after end date." in response.text


def test_admin_import_preview_shows_summary() -> None:
    response = client.post(
        "/admin/import/preview",
        data={"mode": "append"},
        files={"csv_file": ("prices.csv", b"date,metal,price\n2025-01-01,gold,2500\n", "text/csv")},
    )

    assert response.status_code == 200
    assert "Preview" in response.text
    assert "Total rows" in response.text
    assert "Confirm import" in response.text


def test_admin_import_preview_handles_invalid_rows() -> None:
    response = client.post(
        "/admin/import/preview",
        data={"mode": "append"},
        files={"csv_file": ("prices.csv", b"date,metal,price\n2025-01-01,platinum,2500\n", "text/csv")},
    )

    assert response.status_code == 200
    assert "Validation errors" in response.text
    assert "Unsupported metal" in response.text


def test_admin_import_execute_imports_rows() -> None:
    csv_text = "date,metal,price\n2025-01-01,gold,2500\n2025-01-01,silver,30.5\n"

    response = client.post(
        "/admin/import/execute",
        data={"mode": "replace", "csv_content": csv_text, "source_name": "upload.csv"},
    )

    assert response.status_code == 200
    assert "Imported 2 rows using replace mode." in response.text
    assert "upload.csv" in response.text


def test_admin_data_page_loads() -> None:
    response = client.get("/admin/data")

    assert response.status_code == 200
    assert "Historical data management" in response.text
    assert "Dataset summary" in response.text
    assert "Dataset integrity" in response.text
    assert "Repair workflow" in response.text


def test_admin_data_reset_requires_confirmation() -> None:
    response = client.post("/admin/data/reset", data={"confirmation": "WRONG"})

    assert response.status_code == 200
    assert "Type RESET to confirm" in response.text


def test_admin_data_reseed_and_reset_routes_work() -> None:
    reseed_response = client.post("/admin/data/reseed")
    reset_response = client.post("/admin/data/reset", data={"confirmation": "RESET"})

    assert reseed_response.status_code == 200
    assert "deterministic sample rows" in reseed_response.text
    assert reset_response.status_code == 200
    assert "Deleted" in reset_response.text


def test_admin_data_repair_requires_confirmation() -> None:
    preview_response = client.post(
        "/admin/data/repair/preview",
        data={"repair_actions": ["deduplicate"]},
    )
    execute_response = client.post(
        "/admin/data/repair/execute",
        data={"repair_actions": ["deduplicate"], "confirmation": "WRONG"},
    )

    assert preview_response.status_code == 200
    assert "Repair preview" in preview_response.text
    assert execute_response.status_code == 200
    assert "Type REPAIR to confirm" in execute_response.text
