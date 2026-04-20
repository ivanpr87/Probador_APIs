from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TestResult(BaseModel):
    test_name: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


class TestResponse(BaseModel):
    total_tests: int
    results: List[TestResult]
    issues_detected: List[str]
    severity: str
    quality_score: int
    ai_insights: List[str]


class HistoryItem(BaseModel):
    id: int
    url: str
    method: str
    quality_score: Optional[int] = None
    severity: Optional[str] = None
    total_tests: Optional[int] = None
    created_at: str


class HistoryPage(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    limit: int
    total_pages: int


class SavedConfigCreate(BaseModel):
    name: str
    url: str
    method: str = "GET"
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    base_url: Optional[str] = None


class SavedConfig(SavedConfigCreate):
    id: int
    created_at: str
