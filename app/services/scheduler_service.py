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
    """Ejecuta el test de una config guardada, persiste el resultado y actualiza el estado."""
    from app.repositories.configs_repository import list_configs
    from app.repositories.scheduler_repository import get_schedule, mark_last_run, mark_last_error
    from app.repositories.test_repository import fetch_previous_comparable_result, save_result
    from app.models.request_models import TestRequest
    from app.services.notification_service import (
        send_severity_escalation_notification,
        should_notify_severity_transition,
    )
    from app.services.test_service import run_test

    config = None
    schedule = None
    try:
        configs = list_configs()
        config = next((c for c in configs if c.id == config_id), None)
        schedule = get_schedule(schedule_id)
        if not config:
            logger.warning("Test programado: config %d no encontrada — se omite", config_id)
            mark_last_error(schedule_id, f"Config {config_id} no encontrada")
            return

        req = TestRequest(
            url=config.url,
            method=config.method,
            payload=config.payload,
            headers=config.headers,
            auth_config=config.auth_config,
        )
        source = {
            "type": "schedule",
            "config_id": config.id,
            "schedule_id": schedule_id,
        }
        previous_result = fetch_previous_comparable_result(
            url=config.url,
            method=config.method,
            source=source,
        )
        result = run_test(req, source=source)
        mark_last_run(schedule_id)
        previous_severity = previous_result.get("severity") if previous_result else None
        if should_notify_severity_transition(previous_severity, result.severity):
            send_severity_escalation_notification(
                schedule_name=schedule.name if schedule else f"Schedule #{schedule_id}",
                url=config.url,
                method=config.method,
                current_severity=result.severity,
                quality_score=result.quality_score,
                previous_severity=previous_severity,
            )
        logger.info("Test programado para config '%s' completado", config.name)

    except Exception as exc:
        logger.error("Test programado para config %d falló: %s", config_id, exc)
        try:
            mark_last_error(schedule_id, str(exc))
        except Exception as inner_exc:
            logger.error("No se pudo registrar el error del schedule %d: %s", schedule_id, inner_exc)
        try:
            url = config.url if config else f"(config_id={config_id})"
            method = config.method if config else "UNKNOWN"
            save_result(url, method, {
                "error": str(exc),
                "severity": "CRITICAL",
                "quality_score": 0,
                "total_tests": 0,
                "issues_detected": [f"Test programado falló: {exc}"],
                "results": [],
                "ai_insights": [],
            }, source={
                "type": "schedule",
                "config_id": config_id if config else None,
                "schedule_id": schedule_id,
            })
        except Exception as save_exc:
            logger.error("No se pudo guardar resultado de error en historial: %s", save_exc)
