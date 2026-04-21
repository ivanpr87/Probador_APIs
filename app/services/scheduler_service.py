import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.models.scheduler_models import Schedule

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler() -> None:
    """Carga todos los schedules habilitados desde la DB y arranca el scheduler."""
    from app.repositories.scheduler_repository import list_enabled_schedules

    schedules = list_enabled_schedules()
    for schedule in schedules:
        _register_job(schedule)

    _scheduler.start()
    logger.info("Scheduler iniciado — %d jobs cargados", len(schedules))


def stop_scheduler() -> None:
    """Detiene el scheduler limpiamente al apagar el servidor."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler detenido")


def register_job(schedule: Schedule) -> None:
    """Registra un nuevo job si el schedule está habilitado."""
    if schedule.enabled:
        _register_job(schedule)


def remove_job(schedule_id: int) -> None:
    """Elimina el job del scheduler si existe."""
    job_id = f"schedule_{schedule_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)


def _register_job(schedule: Schedule) -> None:
    try:
        trigger = CronTrigger.from_crontab(schedule.cron, timezone="UTC")
        _scheduler.add_job(
            _run_scheduled_test,
            trigger,
            args=[schedule.config_id, schedule.id],
            id=f"schedule_{schedule.id}",
            replace_existing=True,
        )
        logger.info("Job registrado: schedule '%s' (id=%d)", schedule.name, schedule.id)
    except Exception as exc:
        logger.error("No se pudo registrar el job para schedule %d: %s", schedule.id, exc)


def _run_scheduled_test(config_id: int, schedule_id: int) -> None:
    """Ejecuta el test de una config guardada y actualiza last_run."""
    from app.repositories.configs_repository import list_configs
    from app.repositories.scheduler_repository import mark_last_run
    from app.models.request_models import TestRequest
    from app.services.test_service import run_test

    try:
        configs = list_configs()
        config = next((c for c in configs if c.id == config_id), None)
        if not config:
            logger.warning("Test programado: config %d no encontrada — se omite", config_id)
            return

        req = TestRequest(
            url=config.url,
            method=config.method,
            payload=config.payload,
            headers=config.headers,
        )
        run_test(req)
        mark_last_run(schedule_id)
        logger.info("Test programado para config '%s' completado", config.name)
    except Exception as exc:
        logger.error("Test programado para config %d falló: %s", config_id, exc)
