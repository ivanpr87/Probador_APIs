from typing import List

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException

from app.models.scheduler_models import Schedule, ScheduleCreate
from app.repositories.configs_repository import list_configs
from app.repositories.scheduler_repository import (
    create_schedule,
    delete_schedule,
    list_schedules,
    toggle_schedule,
)
from app.services import scheduler_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=List[Schedule])
def get_schedules():
    return list_schedules()


@router.post("", response_model=Schedule, status_code=201)
def post_schedule(data: ScheduleCreate):
    # Validar expresión cron antes de persistir
    try:
        CronTrigger.from_crontab(data.cron, timezone="UTC")
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Expresión cron inválida: '{data.cron}'",
        )

    # Verificar que la config referenciada existe
    configs = list_configs()
    if not any(c.id == data.config_id for c in configs):
        raise HTTPException(status_code=404, detail="Config no encontrada")

    schedule = create_schedule(data)
    scheduler_service.register_job(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
def del_schedule(schedule_id: int):
    scheduler_service.remove_job(schedule_id)
    if not delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule no encontrado")


@router.patch("/{schedule_id}/toggle", response_model=Schedule)
def patch_toggle(schedule_id: int):
    schedule = toggle_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule no encontrado")

    if schedule.enabled:
        scheduler_service.register_job(schedule)
    else:
        scheduler_service.remove_job(schedule_id)

    return schedule
