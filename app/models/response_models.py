from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RunSource(BaseModel):
    type: str
    config_id: Optional[int] = None
    schedule_id: Optional[int] = None


class OAuth2ClientCredentialsConfig(BaseModel):
    type: str = "oauth2_client_credentials"
    token_url: str
    client_id: str
    client_secret: str
    scope: Optional[str] = None
    audience: Optional[str] = None


class LatencyStats(BaseModel):
    sample_size: int
    metric: str
    unit: str = "ms"
    p50: Optional[float] = None
    p95: Optional[float] = None
    p99: Optional[float] = None


class TestResult(BaseModel):
    test_name: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    expected_status: Optional[int] = None


class TestSummary(BaseModel):
    total_tests: int
    passed: int
    failed: int
    fail_rate: float


class TestResponse(BaseModel):
    total_tests: int
    results: List[TestResult]
    issues_detected: List[str]
    severity: str
    quality_score: int
    ai_insights: List[str]
    summary: Optional[TestSummary] = None
    source: Optional[RunSource] = None
    latency_stats: Optional[LatencyStats] = None


class HistoryItem(BaseModel):
    id: int
    url: str
    method: str
    quality_score: Optional[int] = None
    severity: Optional[str] = None
    total_tests: Optional[int] = None
    created_at: str
    previous_score: Optional[int] = None
    delta_score: Optional[int] = None
    delta_direction: Optional[str] = None
    source: Optional[RunSource] = None


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
    auth_config: Optional[OAuth2ClientCredentialsConfig] = None


class SavedConfig(SavedConfigCreate):
    id: int
    created_at: str


class OpenAPIImportSummary(BaseModel):
    created: int
    skipped: int
    errors: List[str]
    configs: List[SavedConfig]
