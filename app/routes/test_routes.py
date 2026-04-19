from fastapi import APIRouter
from app.services.test_service import run_test

router = APIRouter()

@router.post("/run-test")
def run_api_test(data: dict):
    return run_test(data)