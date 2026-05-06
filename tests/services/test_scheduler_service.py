"""
Tests unitarios para app/services/scheduler_service.py (AF-011).

Cubre:
  - register_job: registra job solo si habilitado
  - remove_job: elimina job del scheduler si existe
  - start_scheduler: carga jobs desde DB y arranca
  - stop_scheduler: detiene scheduler si esta corriendo
  - _run_scheduled_test: flujo exitoso y manejo de error
"""

from app.models.scheduler_models import Schedule


def _make_schedule(
    id=1,
    name="test-schedule",
    config_id=42,
    cron="*/30 * * * *",
    enabled=True,
):
    return Schedule(
        id=id,
        name=name,
        config_id=config_id,
        config_name="test-config",
        cron=cron,
        enabled=enabled,
        last_run=None,
        last_status=None,
        last_error=None,
        created_at="2026-01-01T00:00:00",
    )


class TestRegisterJob:
    """AF-011: register_job — registra job en el scheduler."""

    def test_registra_job_cuando_habilitado(self, mocker):
        """GIVEN schedule enabled WHEN register_job THEN add_job es llamado."""
        mock_add = mocker.patch("app.services.scheduler_service._scheduler.add_job")
        mock_trigger = mocker.patch(
            "app.services.scheduler_service.CronTrigger.from_crontab",
            return_value="mock-trigger",
        )

        from app.services import scheduler_service

        schedule = _make_schedule(enabled=True)
        scheduler_service.register_job(schedule)

        mock_add.assert_called_once()
        call_kwargs = mock_add.call_args
        assert call_kwargs[0][1] == "mock-trigger"  # trigger
        assert call_kwargs[1]["id"] == f"schedule_{schedule.id}"
        assert call_kwargs[1]["replace_existing"] is True

    def test_no_registra_job_cuando_deshabilitado(self, mocker):
        """GIVEN schedule disabled WHEN register_job THEN add_job NO es llamado."""
        mock_add = mocker.patch("app.services.scheduler_service._scheduler.add_job")

        from app.services import scheduler_service

        schedule = _make_schedule(enabled=False)
        scheduler_service.register_job(schedule)

        mock_add.assert_not_called()


class TestRemoveJob:
    """AF-011: remove_job — elimina job del scheduler."""

    def test_elimina_job_existente(self, mocker):
        """GIVEN job existe en scheduler WHEN remove_job THEN remove_job es llamado."""
        mock_get = mocker.patch(
            "app.services.scheduler_service._scheduler.get_job",
            return_value="job-exists",
        )
        mock_remove = mocker.patch(
            "app.services.scheduler_service._scheduler.remove_job",
        )

        from app.services import scheduler_service

        scheduler_service.remove_job(42)
        mock_get.assert_called_once_with("schedule_42")
        mock_remove.assert_called_once_with("schedule_42")

    def test_no_elimina_job_inexistente(self, mocker):
        """GIVEN job NO existe WHEN remove_job THEN remove_job NO es llamado."""
        mock_get = mocker.patch(
            "app.services.scheduler_service._scheduler.get_job",
            return_value=None,
        )
        mock_remove = mocker.patch(
            "app.services.scheduler_service._scheduler.remove_job",
        )

        from app.services import scheduler_service

        scheduler_service.remove_job(99)
        mock_get.assert_called_once_with("schedule_99")
        mock_remove.assert_not_called()


class TestStartScheduler:
    """AF-011: start_scheduler — arranque con jobs desde DB."""

    def test_carga_jobs_y_arranca(self, mocker):
        """GIVEN DB con schedules enabled WHEN start_scheduler THEN register + start."""
        schedule = _make_schedule(id=1, enabled=True)
        mocker.patch(
            "app.services.scheduler_service.list_enabled_schedules",
            return_value=[schedule],
        )
        mock_add = mocker.patch("app.services.scheduler_service._scheduler.add_job")
        mock_start = mocker.patch("app.services.scheduler_service._scheduler.start")
        mock_trigger = mocker.patch(
            "app.services.scheduler_service.CronTrigger.from_crontab",
            return_value="mock-trigger",
        )

        from app.services import scheduler_service
        scheduler_service.start_scheduler()

        mock_add.assert_called_once()
        mock_start.assert_called_once()

    def test_sin_jobs_arranca_igual(self, mocker):
        """GIVEN DB sin schedules enabled WHEN start_scheduler THEN start sin add_job."""
        mocker.patch(
            "app.services.scheduler_service.list_enabled_schedules",
            return_value=[],
        )
        mock_add = mocker.patch("app.services.scheduler_service._scheduler.add_job")
        mock_start = mocker.patch("app.services.scheduler_service._scheduler.start")

        from app.services import scheduler_service
        scheduler_service.start_scheduler()

        mock_add.assert_not_called()
        mock_start.assert_called_once()


class TestStopScheduler:
    """AF-011: stop_scheduler — apagado limpio."""

    def test_detiene_si_esta_corriendo(self, mocker):
        """GIVEN scheduler running WHEN stop_scheduler THEN shutdown es llamado."""
        # Mock _scheduler como un mock completo donde .running = True
        mock_sched = mocker.MagicMock()
        mock_sched.running = True
        mocker.patch("app.services.scheduler_service._scheduler", mock_sched)

        from app.services import scheduler_service
        scheduler_service.stop_scheduler()

        mock_sched.shutdown.assert_called_once_with(wait=False)

    def test_no_detiene_si_no_esta_corriendo(self, mocker):
        """GIVEN scheduler NOT running WHEN stop_scheduler THEN shutdown NO es llamado."""
        mock_sched = mocker.MagicMock()
        mock_sched.running = False
        mocker.patch("app.services.scheduler_service._scheduler", mock_sched)

        from app.services import scheduler_service
        scheduler_service.stop_scheduler()

        mock_sched.shutdown.assert_not_called()




class TestRunScheduledTest:
    """AF-011: _run_scheduled_test — flujo exitoso y manejo de error."""

    def test_ejecuta_test_y_marca_last_run(self, mocker):
        """GIVEN config existe WHEN _run_scheduled_test THEN run_test + mark_last_run."""
        mock_config = mocker.Mock()
        mock_config.url = "https://api.example.com/users"
        mock_config.method = "GET"
        mock_config.payload = None
        mock_config.headers = None
        mock_config.auth_config = None
        mocker.patch(
            "app.services.scheduler_service.get_config_by_id",
            return_value=mock_config,
        )
        mock_schedule = _make_schedule(id=10, name="sched", config_id=42)
        mocker.patch(
            "app.services.scheduler_service.get_schedule",
            return_value=mock_schedule,
        )

        mock_run_test = mocker.patch(
            "app.services.scheduler_service.run_test",
            return_value=mocker.Mock(
                quality_score=85,
                severity="LOW",
                model_dump=mocker.Mock(return_value={"quality_score": 85, "severity": "LOW"}),
            ),
        )
        mock_mark_run = mocker.patch("app.services.scheduler_service.mark_last_run")
        mock_fetch_prev = mocker.patch(
            "app.services.scheduler_service.fetch_previous_comparable_result",
            return_value=None,
        )
        mocker.patch("app.services.scheduler_service.should_notify_severity_transition", return_value=False)
        mocker.patch("app.services.scheduler_service.save_result")

        from app.services import scheduler_service
        scheduler_service._run_scheduled_test(42, 10)

        mock_run_test.assert_called_once()
        mock_mark_run.assert_called_once_with(10)

    def test_marca_error_si_config_no_existe(self, mocker):
        """GIVEN config_id no existe WHEN _run_scheduled_test THEN mark_last_error."""
        mocker.patch(
            "app.services.scheduler_service.get_config_by_id",
            return_value=None,
        )
        mocker.patch(
            "app.services.scheduler_service.get_schedule",
            return_value=None,
        )
        mock_mark_error = mocker.patch("app.services.scheduler_service.mark_last_error")
        mock_run_test = mocker.patch("app.services.scheduler_service.run_test")

        from app.services import scheduler_service
        scheduler_service._run_scheduled_test(999, 99)

        mock_run_test.assert_not_called()
        mock_mark_error.assert_called_once_with(99, "Config 999 no encontrada")

    def test_marca_error_si_run_test_falla(self, mocker):
        """GIVEN run_test lanza excepcion WHEN _run_scheduled_test THEN catch + mark_last_error."""
        mock_config = mocker.Mock()
        mock_config.url = "https://api.example.com/users"
        mock_config.method = "GET"
        mock_config.payload = None
        mock_config.headers = None
        mock_config.auth_config = None
        mocker.patch(
            "app.services.scheduler_service.get_config_by_id",
            return_value=mock_config,
        )
        mock_schedule = _make_schedule(id=5, name="failing", config_id=42)
        mocker.patch(
            "app.services.scheduler_service.get_schedule",
            return_value=mock_schedule,
        )

        mocker.patch(
            "app.services.scheduler_service.run_test",
            side_effect=RuntimeError("API connection failed"),
        )
        mock_mark_error = mocker.patch("app.services.scheduler_service.mark_last_error")
        mock_save_result = mocker.patch("app.services.scheduler_service.save_result")
        mock_fetch_prev = mocker.patch(
            "app.services.scheduler_service.fetch_previous_comparable_result",
            return_value=None,
        )
        mocker.patch("app.services.scheduler_service.should_notify_severity_transition", return_value=False)

        from app.services import scheduler_service
        scheduler_service._run_scheduled_test(42, 5)

        mock_mark_error.assert_called_once_with(5, "API connection failed")
        # Debe guardar resultado de error en historial
        mock_save_result.assert_called_once()
        saved_result = mock_save_result.call_args[0][2]
        assert saved_result["severity"] == "CRITICAL"
        assert saved_result["quality_score"] == 0
