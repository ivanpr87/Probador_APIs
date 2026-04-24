from typing import List, Optional

from app.core.database import get_connection
from app.models.scheduler_models import Schedule, ScheduleCreate

_SELECT = """
    SELECT s.id, s.name, s.config_id, s.cron, s.enabled, s.last_run,
           s.last_status, s.last_error, s.created_at,
           c.name AS config_name
    FROM scheduled_tests s
    LEFT JOIN saved_configs c ON c.id = s.config_id
"""


def create_schedule(data: ScheduleCreate) -> Schedule:
    with get_connection() as conn:
        cursor = conn.execute(
            'INSERT INTO scheduled_tests (name, config_id, cron) VALUES (?, ?, ?)',
            (data.name, data.config_id, data.cron),
        )
        row = conn.execute(
            f'{_SELECT} WHERE s.id = ?', (cursor.lastrowid,)
        ).fetchone()
    return _row_to_schedule(row)


def list_schedules() -> List[Schedule]:
    with get_connection() as conn:
        rows = conn.execute(
            f'{_SELECT} ORDER BY s.created_at DESC'
        ).fetchall()
    return [_row_to_schedule(r) for r in rows]


def list_enabled_schedules() -> List[Schedule]:
    with get_connection() as conn:
        rows = conn.execute(
            f'{_SELECT} WHERE s.enabled = 1'
        ).fetchall()
    return [_row_to_schedule(r) for r in rows]


def get_schedule(schedule_id: int) -> Optional[Schedule]:
    with get_connection() as conn:
        row = conn.execute(
            f'{_SELECT} WHERE s.id = ?', (schedule_id,)
        ).fetchone()
    return _row_to_schedule(row) if row else None


def delete_schedule(schedule_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            'DELETE FROM scheduled_tests WHERE id = ?', (schedule_id,)
        )
    return cursor.rowcount > 0


def toggle_schedule(schedule_id: int) -> Optional[Schedule]:
    with get_connection() as conn:
        conn.execute(
            'UPDATE scheduled_tests SET enabled = NOT enabled WHERE id = ?',
            (schedule_id,),
        )
        row = conn.execute(
            f'{_SELECT} WHERE s.id = ?', (schedule_id,)
        ).fetchone()
    return _row_to_schedule(row) if row else None


def mark_last_run(schedule_id: int) -> None:
    """Registra ejecución exitosa: actualiza last_run, limpia error previo."""
    with get_connection() as conn:
        conn.execute(
            """UPDATE scheduled_tests
               SET last_run = CURRENT_TIMESTAMP,
                   last_status = 'success',
                   last_error = NULL
               WHERE id = ?""",
            (schedule_id,),
        )


def mark_last_error(schedule_id: int, error_msg: str) -> None:
    """Registra fallo de ejecución: persiste el mensaje de error en la DB."""
    with get_connection() as conn:
        conn.execute(
            """UPDATE scheduled_tests
               SET last_run = CURRENT_TIMESTAMP,
                   last_status = 'error',
                   last_error = ?
               WHERE id = ?""",
            (error_msg, schedule_id),
        )


def _row_to_schedule(row) -> Schedule:
    return Schedule(
        id=row['id'],
        name=row['name'],
        config_id=row['config_id'],
        config_name=row['config_name'],
        cron=row['cron'],
        enabled=bool(row['enabled']),
        last_run=row['last_run'],
        last_status=row['last_status'],
        last_error=row['last_error'],
        created_at=row['created_at'],
    )
