from datetime import date

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.repositories.prices import SQLitePriceRepository
from app.services.calculator import CalculatorInputs, calculate_decision
from app.services.data_management import (
    get_dataset_summary,
    reseed_historical_data,
    reset_historical_data,
)
from app.services.data_integrity import build_dataset_integrity_report
from app.services.data_repair import build_repair_preview, execute_repair
from app.services.history import get_historical_ratio_overview
from app.services.imports import (
    build_import_preview,
    execute_import_with_audit,
    get_dataset_status,
    get_recent_import_runs,
    record_failed_import_attempt,
)
from app.services.ratio_confidence import evaluate_ratio_confidence

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


def _default_context(request: Request) -> dict:
    return {
        "request": request,
        "result": None,
        "history": None,
        "history_confidence": None,
        "history_error": None,
        "error": None,
        "history_filters": {
            "start_date": "",
            "end_date": "",
            "overlap_only": False,
        },
        "form_data": {
            "gold_purchase_amount": 1000,
            "silver_purchase_amount": 1000,
            "silver_vat_rate_pct": 19,
            "future_price_change_pct": 0,
            "holding_period_years": 0,
            "purchase_premium_pct": 0,
            "sale_discount_pct": 0,
            "gold_price_per_ounce": 3000,
            "silver_price_per_ounce": 30,
        },
    }


def _admin_import_context(request: Request) -> dict:
    return {
        "request": request,
        "title": "CSV Import",
        "error": None,
        "message": None,
        "preview": None,
        "selected_mode": "append",
        "csv_content": "",
        "source_name": "",
        "recent_imports": [],
        "dataset_status": None,
    }


def _admin_data_context(request: Request) -> dict:
    return {
        "request": request,
        "title": "Data Management",
        "error": None,
        "message": None,
        "dataset_summary": None,
        "dataset_status": None,
        "integrity_report": None,
        "ratio_confidence": None,
        "recent_imports": [],
        "confirmation_value": "",
        "repair_preview": None,
        "selected_repairs": [],
    }


def _attach_history(context: dict) -> None:
    start_date = _parse_optional_date(context["history_filters"]["start_date"])
    end_date = _parse_optional_date(context["history_filters"]["end_date"])
    overlap_only = bool(context["history_filters"]["overlap_only"])
    with SessionLocal() as session:
        context["history"] = get_historical_ratio_overview(
            SQLitePriceRepository(session),
            start_date=start_date,
            end_date=end_date,
            overlap_only=overlap_only,
        )
        dataset_status = get_dataset_status(session)
        integrity_report = build_dataset_integrity_report(session, dataset_status=dataset_status)
        context["history_confidence"] = evaluate_ratio_confidence(
            integrity_report=integrity_report,
            dataset_status=dataset_status,
            history_overview=context["history"],
        )


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _attach_import_admin_data(context: dict) -> None:
    with SessionLocal() as session:
        context["recent_imports"] = get_recent_import_runs(session, limit=8)
        context["dataset_status"] = get_dataset_status(session)


def _attach_data_admin_data(context: dict) -> None:
    with SessionLocal() as session:
        context["recent_imports"] = get_recent_import_runs(session, limit=8)
        context["dataset_status"] = get_dataset_status(session)
        context["dataset_summary"] = get_dataset_summary(session)
        context["integrity_report"] = build_dataset_integrity_report(
            session,
            dataset_status=context["dataset_status"],
        )
        context["ratio_confidence"] = evaluate_ratio_confidence(
            integrity_report=context["integrity_report"],
            dataset_status=context["dataset_status"],
        )


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"title": "Home"})


@router.get("/calculator", response_class=HTMLResponse)
def calculator(
    request: Request,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    overlap_only: bool = Query(default=False),
) -> HTMLResponse:
    context = _default_context(request)
    context["title"] = "Calculator"
    context["history_filters"] = {
        "start_date": start_date or "",
        "end_date": end_date or "",
        "overlap_only": overlap_only,
    }
    try:
        _attach_history(context)
    except ValueError as exc:
        context["history_error"] = str(exc)
    return templates.TemplateResponse(request, "calculator.html", context)


@router.post("/calculator", response_class=HTMLResponse)
def calculator_submit(
    request: Request,
    gold_purchase_amount: float = Form(...),
    silver_purchase_amount: float = Form(...),
    silver_vat_rate_pct: float = Form(19),
    future_price_change_pct: float = Form(0),
    holding_period_years: float = Form(0),
    purchase_premium_pct: float = Form(0),
    sale_discount_pct: float = Form(0),
    gold_price_per_ounce: float = Form(...),
    silver_price_per_ounce: float = Form(...),
    history_start_date: str = Form(""),
    history_end_date: str = Form(""),
    history_overlap_only: str | None = Form(default=None),
) -> HTMLResponse:
    context = _default_context(request)
    context["title"] = "Calculator"
    context["history_filters"] = {
        "start_date": history_start_date,
        "end_date": history_end_date,
        "overlap_only": history_overlap_only is not None,
    }
    context["form_data"] = {
        "gold_purchase_amount": gold_purchase_amount,
        "silver_purchase_amount": silver_purchase_amount,
        "silver_vat_rate_pct": silver_vat_rate_pct,
        "future_price_change_pct": future_price_change_pct,
        "holding_period_years": holding_period_years,
        "purchase_premium_pct": purchase_premium_pct,
        "sale_discount_pct": sale_discount_pct,
        "gold_price_per_ounce": gold_price_per_ounce,
        "silver_price_per_ounce": silver_price_per_ounce,
    }
    try:
        calculator_inputs = CalculatorInputs(
            gold_purchase_amount=gold_purchase_amount,
            silver_purchase_amount=silver_purchase_amount,
            silver_vat_rate_pct=silver_vat_rate_pct,
            future_price_change_pct=future_price_change_pct,
            holding_period_years=holding_period_years,
            purchase_premium_pct=purchase_premium_pct,
            sale_discount_pct=sale_discount_pct,
            gold_price_per_ounce=gold_price_per_ounce,
            silver_price_per_ounce=silver_price_per_ounce,
        )
        context["result"] = calculate_decision(calculator_inputs)
    except ValueError as exc:
        context["error"] = str(exc)
    try:
        _attach_history(context)
    except ValueError as exc:
        context["history_error"] = str(exc)

    return templates.TemplateResponse(request, "calculator.html", context)


@router.get("/admin/import", response_class=HTMLResponse)
def admin_import(request: Request) -> HTMLResponse:
    context = _admin_import_context(request)
    _attach_import_admin_data(context)
    return templates.TemplateResponse(request, "admin_import.html", context)


@router.get("/admin/data", response_class=HTMLResponse)
def admin_data(request: Request) -> HTMLResponse:
    context = _admin_data_context(request)
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)


@router.post("/admin/import/preview", response_class=HTMLResponse)
async def admin_import_preview(
    request: Request,
    csv_file: UploadFile = File(...),
    mode: str = Form("append"),
) -> HTMLResponse:
    context = _admin_import_context(request)
    context["selected_mode"] = mode

    try:
        if not csv_file.filename:
            raise ValueError("Please choose a CSV file to upload.")
        context["source_name"] = csv_file.filename
        content = await csv_file.read()
        if not content:
            raise ValueError("Uploaded CSV file is empty.")
        csv_text = content.decode("utf-8")
        preview = build_import_preview(csv_text, mode)
        context["preview"] = preview
        context["csv_content"] = csv_text
    except UnicodeDecodeError:
        context["error"] = "CSV file must be UTF-8 encoded text."
    except ValueError as exc:
        context["error"] = str(exc)
    _attach_import_admin_data(context)

    return templates.TemplateResponse(request, "admin_import.html", context)


@router.post("/admin/import/execute", response_class=HTMLResponse)
async def admin_import_execute(
    request: Request,
    csv_content: str = Form(...),
    mode: str = Form("append"),
    source_name: str = Form("uploaded.csv"),
) -> HTMLResponse:
    context = _admin_import_context(request)
    context["selected_mode"] = mode
    context["source_name"] = source_name

    try:
        preview = build_import_preview(csv_content, mode)
        context["preview"] = preview
        context["csv_content"] = csv_content
        try:
            with SessionLocal() as session:
                result = execute_import_with_audit(
                    session,
                    preview,
                    source_type="web_csv",
                    source_name=source_name or "uploaded.csv",
                )
            context["message"] = (
                f"Imported {result.imported_rows} rows using {result.mode} mode."
            )
        except ValueError as exc:
            context["error"] = str(exc)
    except ValueError as exc:
        with SessionLocal() as session:
            record_failed_import_attempt(
                session,
                source_type="web_csv",
                source_name=source_name or "uploaded.csv",
                import_mode=mode,
                error_summary=str(exc),
                total_rows=context["preview"].total_rows if context["preview"] else 0,
                valid_rows=context["preview"].valid_rows if context["preview"] else 0,
                invalid_rows=context["preview"].invalid_rows if context["preview"] else 0,
            )
        context["error"] = str(exc)
    _attach_import_admin_data(context)

    return templates.TemplateResponse(request, "admin_import.html", context)


@router.post("/admin/data/reset", response_class=HTMLResponse)
def admin_data_reset(
    request: Request,
    confirmation: str = Form(""),
) -> HTMLResponse:
    context = _admin_data_context(request)
    context["confirmation_value"] = confirmation
    if confirmation != "RESET":
        context["error"] = "Type RESET to confirm deletion of historical price rows."
        _attach_data_admin_data(context)
        return templates.TemplateResponse(request, "admin_data.html", context)

    with SessionLocal() as session:
        result = reset_historical_data(
            session,
            source_type="web_reset",
            source_name="admin-data-reset",
        )
    context["message"] = result.message
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)


@router.post("/admin/data/reseed", response_class=HTMLResponse)
def admin_data_reseed(request: Request) -> HTMLResponse:
    context = _admin_data_context(request)
    with SessionLocal() as session:
        result = reseed_historical_data(
            session,
            source_type="web_reseed",
            source_name="admin-data-reseed",
        )
    context["message"] = result.message
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)


@router.get("/admin/data/repair", response_class=HTMLResponse)
def admin_data_repair(request: Request) -> HTMLResponse:
    context = _admin_data_context(request)
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)


@router.post("/admin/data/repair/preview", response_class=HTMLResponse)
def admin_data_repair_preview(
    request: Request,
    repair_actions: list[str] = Form(default=[]),
) -> HTMLResponse:
    context = _admin_data_context(request)
    context["selected_repairs"] = repair_actions
    try:
        with SessionLocal() as session:
            context["repair_preview"] = build_repair_preview(session, repair_actions)
    except ValueError as exc:
        context["error"] = str(exc)
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)


@router.post("/admin/data/repair/execute", response_class=HTMLResponse)
def admin_data_repair_execute(
    request: Request,
    repair_actions: list[str] = Form(default=[]),
    confirmation: str = Form(""),
) -> HTMLResponse:
    context = _admin_data_context(request)
    context["selected_repairs"] = repair_actions
    context["confirmation_value"] = confirmation
    try:
        if confirmation != "REPAIR":
            raise ValueError("Type REPAIR to confirm dataset repair.")
        with SessionLocal() as session:
            preview = build_repair_preview(session, repair_actions)
            context["repair_preview"] = preview
            result = execute_repair(session, preview, source_name="admin-data-repair")
        context["message"] = result.summary
    except ValueError as exc:
        context["error"] = str(exc)
    _attach_data_admin_data(context)
    return templates.TemplateResponse(request, "admin_data.html", context)
