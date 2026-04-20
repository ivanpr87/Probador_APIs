from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.request_models import TestRequest
from app.models.response_models import HistoryItem, TestResponse
from app.repositories.test_repository import fetch_history
from app.services.report_service import build_report
from app.services.test_service import run_test

router = APIRouter()


@router.post("/run-test", response_model=TestResponse)
def run_api_test(request: TestRequest) -> TestResponse:
    return run_test(request)


@router.post("/export-report")
def export_report(data: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=build_report(data))


@router.get("/history", response_model=List[HistoryItem])
def get_history() -> List[HistoryItem]:
    return fetch_history()
