from typing import Optional

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    name: str
    config_id: int
    cron: str  # formato estándar 5 campos: "*/30 * * * *"


class Schedule(BaseModel):
    id: int
    name: str
    config_id: int
    config_name: Optional[str] = None
    cron: str
    enabled: bool
    last_run: Optional[str] = None
    last_status: Optional[str] = None  # 'success' | 'error' | None
    last_error: Optional[str] = None   # mensaje del último error
    created_at: str
