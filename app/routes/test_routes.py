from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.test_service import run_test
from app.services.history_service import get_tests

router = APIRouter()


@router.post("/run-test")
def run_api_test(data: dict):
    return run_test(data)


@router.post("/export-report")
def export_report(data: dict):
    return JSONResponse(content=data)


@router.get("/history")
def get_history():
    return get_tests()