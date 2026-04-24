from app.services.notification_service import (
    send_severity_escalation_notification,
    should_notify_severity_transition,
)


class TestShouldNotifySeverityTransition:

    def test_dispara_cuando_escala_a_critical_desde_low(self):
        assert should_notify_severity_transition("LOW", "CRITICAL") is True

    def test_dispara_cuando_no_hay_run_previo(self):
        assert should_notify_severity_transition(None, "CRITICAL") is True

    def test_no_dispara_si_ya_estaba_en_critical(self):
        assert should_notify_severity_transition("CRITICAL", "CRITICAL") is False

    def test_no_dispara_si_el_run_actual_no_es_critical(self):
        assert should_notify_severity_transition("HIGH", "HIGH") is False


class TestSendSeverityEscalationNotification:

    def test_envia_a_webhook_y_slack_cuando_esta_habilitado(self, mocker):
        mock_post = mocker.patch("app.services.notification_service.requests.post")
        mocker.patch("app.services.notification_service.settings.NOTIFICATIONS_ENABLED", True)
        mocker.patch("app.services.notification_service.settings.WEBHOOK_URL", "https://hooks.example.com/webhook")
        mocker.patch("app.services.notification_service.settings.SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")

        send_severity_escalation_notification(
            schedule_name="API prod hourly",
            url="https://api.example.com/users",
            method="GET",
            current_severity="CRITICAL",
            quality_score=20,
            previous_severity="LOW",
        )

        assert mock_post.call_count == 2

    def test_no_envia_si_notificaciones_estan_deshabilitadas(self, mocker):
        mock_post = mocker.patch("app.services.notification_service.requests.post")
        mocker.patch("app.services.notification_service.settings.NOTIFICATIONS_ENABLED", False)
        mocker.patch("app.services.notification_service.settings.WEBHOOK_URL", "https://hooks.example.com/webhook")

        send_severity_escalation_notification(
            schedule_name="API prod hourly",
            url="https://api.example.com/users",
            method="GET",
            current_severity="CRITICAL",
            quality_score=20,
            previous_severity="LOW",
        )

        mock_post.assert_not_called()

    def test_error_del_webhook_no_explota(self, mocker):
        mock_post = mocker.patch(
            "app.services.notification_service.requests.post",
            side_effect=RuntimeError("network down"),
        )
        mocker.patch("app.services.notification_service.settings.NOTIFICATIONS_ENABLED", True)
        mocker.patch("app.services.notification_service.settings.WEBHOOK_URL", "https://hooks.example.com/webhook")
        mocker.patch("app.services.notification_service.settings.SLACK_WEBHOOK_URL", "")

        send_severity_escalation_notification(
            schedule_name="API prod hourly",
            url="https://api.example.com/users",
            method="GET",
            current_severity="CRITICAL",
            quality_score=20,
            previous_severity="LOW",
        )

        assert mock_post.call_count == 1
