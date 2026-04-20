from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.request_models import TestRequest
from app.models.response_models import HistoryPage, TestResponse
from app.repositories.test_repository import fetch_history, fetch_history_item
from app.services.report_service import build_report
from app.services.test_service import run_test

router = APIRouter()


@router.post("/run-test", response_model=TestResponse)
def run_api_test(request: TestRequest) -> TestResponse:
    return run_test(request)


@router.post("/export-report")
def export_report(data: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=build_report(data))


@router.get("/history", response_model=HistoryPage)
def get_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> HistoryPage:
    return fetch_history(page=page, limit=limit)


@router.get("/history/{item_id}")
def get_history_item(item_id: int):
    result = fetch_history_item(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="History item not found")
    return result
