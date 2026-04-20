from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator


class CustomTestCase(BaseModel):
    name: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    expected_status: Optional[int] = None


class TestRequest(BaseModel):
    url: str
    method: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    expected_schema: Optional[Dict[str, str]] = None
    custom_cases: Optional[List[CustomTestCase]] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Method must be one of: {allowed}")
        return upper
