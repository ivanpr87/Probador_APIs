from typing import Any, Dict, Optional
from pydantic import BaseModel, field_validator


class TestRequest(BaseModel):
    url: str
    method: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Method must be one of: {allowed}")
        return upper
