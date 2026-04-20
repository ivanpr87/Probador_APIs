from typing import List, Optional
from pydantic import BaseModel


class TestResult(BaseModel):
    test_name: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
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
