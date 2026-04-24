"""
Tests unitarios del motor de evaluación — analysis_service.py

Cubre:
  - _is_failure()         : contratos de pass/fail por test_name
  - _calculate_score()    : penalidades y límites (techo 5xx, piso 4xx)
  - _determine_severity() : clasificación basada en señales, no en score
  - analyze()             : integración del motor completo
"""

import pytest

from app.services.analysis_service import (
    _is_failure,
    _calculate_score,
    _determine_severity,
    analyze,
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _make_summary(total: int, failed: int) -> dict:
    return {
        'total':     total,
        'passed':    total - failed,
        'failed':    failed,
        'fail_rate': round(failed / total * 100, 1) if total else 0.0,
    }


def _make_issue(type_key: str, severity: str = 'MEDIUM') -> dict:
    return {'type': type_key, 'severity': severity, 'count': 1, 'message': ''}


def _make_result(test_name: str, status_code: int, **kwargs) -> dict:
    return {'test_name': test_name, 'status_code': status_code,
            'response_body': None, 'response_time': 0.1, 'error': None, **kwargs}


# ─── _is_failure() ────────────────────────────────────────────────────────────

class TestIsFailure:

    def test_valid_request_2xx_pasa(self):
        assert _is_failure({'test_name': 'valid_request', 'status_code': 200}) is False

    def test_valid_request_201_pasa(self):
        assert _is_failure({'test_name': 'valid_request', 'status_code': 201}) is False

    def test_valid_request_4xx_falla(self):
        assert _is_failure({'test_name': 'valid_request', 'status_code': 400}) is True

    def test_valid_request_5xx_falla(self):
        assert _is_failure({'test_name': 'valid_request', 'status_code': 500}) is True

    def test_missing_payload_2xx_falla(self):
        # La API debería rechazar; si acepta (2xx) → es un fallo
        assert _is_failure({'test_name': 'missing_payload', 'status_code': 200}) is True

    def test_missing_payload_4xx_pasa(self):
        assert _is_failure({'test_name': 'missing_payload', 'status_code': 422}) is False

    def test_invalid_types_2xx_falla(self):
        assert _is_failure({'test_name': 'invalid_types', 'status_code': 200}) is True

    def test_invalid_types_4xx_pasa(self):
        assert _is_failure({'test_name': 'invalid_types', 'status_code': 400}) is False

    def test_incomplete_payload_2xx_falla(self):
        assert _is_failure({'test_name': 'incomplete_payload', 'status_code': 200}) is True

    def test_incomplete_payload_4xx_pasa(self):
        assert _is_failure({'test_name': 'incomplete_payload', 'status_code': 400}) is False

    def test_no_query_params_siempre_pasa(self):
        # Cualquier respuesta sin error de red es aceptable para este caso
        assert _is_failure({'test_name': 'no_query_params', 'status_code': 404}) is False

    def test_error_de_red_es_fallo(self):
        assert _is_failure({'error': 'timeout', 'status_code': None}) is True

    def test_error_con_status_es_fallo(self):
        assert _is_failure({'error': 'conn refused', 'status_code': 200}) is True

    def test_expected_status_coincide(self):
        assert _is_failure({'expected_status': 201, 'status_code': 201}) is False

    def test_expected_status_no_coincide(self):
        assert _is_failure({'expected_status': 200, 'status_code': 201}) is True

    def test_sin_status_code_es_fallo(self):
        assert _is_failure({'test_name': 'valid_request'}) is True

    def test_nombre_desconocido_2xx_pasa(self):
        assert _is_failure({'test_name': 'custom_name', 'status_code': 201}) is False

    def test_nombre_desconocido_4xx_falla(self):
        assert _is_failure({'test_name': 'custom_name', 'status_code': 404}) is True


# ─── _calculate_score() ───────────────────────────────────────────────────────

class TestCalculateScore:

    def test_score_100_sin_fallos(self):
        summary = _make_summary(total=2, failed=0)
        score = _calculate_score(summary, [], has_5xx=False, has_4xx=False)
        assert score == 100

    def test_techo_40_por_5xx(self):
        summary = _make_summary(total=2, failed=0)
        score = _calculate_score(summary, [], has_5xx=True, has_4xx=False)
        assert score <= 40

    def test_penalidad_10_por_test_fallido(self):
        summary = _make_summary(total=2, failed=1)
        score = _calculate_score(summary, [], has_5xx=False, has_4xx=False)
        assert score == 90

    def test_100pct_fallo_con_5xx_aplica_50(self):
        summary = _make_summary(total=1, failed=1)
        score = _calculate_score(summary, [], has_5xx=True, has_4xx=False)
        # techo 40 + penalidad por 1 fallo (-10) + penalidad 100% con 5xx (-50) → clampeado a 0, luego techo 40
        assert score <= 40

    def test_100pct_fallo_sin_5xx_aplica_30(self):
        summary = _make_summary(total=1, failed=1)
        score = _calculate_score(summary, [], has_5xx=False, has_4xx=True)
        # 100 - 10 (fallo) - 30 (100% sin 5xx) = 60 → piso 40 actúa si cae bajo 40
        assert 40 <= score <= 60

    def test_piso_40_solo_4xx(self):
        # Con muchos fallos 4xx, el score no puede caer por debajo de 40
        summary = _make_summary(total=5, failed=5)
        issues = [_make_issue('HTTP_4XX', 'MEDIUM')] * 5
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=True)
        assert score >= 40

    def test_penalidad_4xx_cap_30(self):
        # 10 issues 4xx → 10 × -5 = -50, pero cap es -30
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue(f'HTTP_4{i}x', 'MEDIUM') for i in range(10)]
        # Hacemos que los types empiecen con HTTP_4 para que los cuente
        issues = [{'type': 'HTTP_400', 'severity': 'MEDIUM', 'count': 1, 'message': ''}] * 10
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=True)
        # Sin fallos, sin 5xx: 100 - cap(10×5, 30) = 70
        assert score >= 70

    def test_latencia_critica_resta_10(self):
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue('HIGH_LATENCY_CRITICAL', 'HIGH')]
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=False)
        assert score == 90

    def test_latencia_warn_resta_5(self):
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue('HIGH_LATENCY_WARN', 'MEDIUM')]
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=False)
        assert score == 95

    def test_invalid_types_resta_20(self):
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue('INVALID_TYPES_ACCEPTED', 'CRITICAL')]
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=False)
        assert score == 80

    def test_missing_payload_resta_10(self):
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue('MISSING_PAYLOAD_ACCEPTED', 'HIGH')]
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=False)
        assert score == 90

    def test_false_positive_resta_5(self):
        summary = _make_summary(total=2, failed=0)
        issues = [_make_issue('FALSE_POSITIVE', 'MEDIUM')]
        score = _calculate_score(summary, issues, has_5xx=False, has_4xx=False)
        assert score == 95

    def test_score_clamp_no_menor_cero(self):
        # Escenario con muchos fallos acumulados
        summary = _make_summary(total=10, failed=10)
        issues = [_make_issue('INVALID_TYPES_ACCEPTED', 'CRITICAL'),
                  _make_issue('HIGH_LATENCY_CRITICAL', 'HIGH')]
        score = _calculate_score(summary, issues, has_5xx=True, has_4xx=False)
        assert score >= 0

    def test_score_clamp_no_mayor_100(self):
        summary = _make_summary(total=2, failed=0)
        score = _calculate_score(summary, [], has_5xx=False, has_4xx=False)
        assert score <= 100

    def test_tasa_mayor_50pct_resta_20(self):
        # 3 de 5 fallan → fail_rate = 60% → penalidad -20 adicional
        summary = _make_summary(total=5, failed=3)
        score_sin_tasa = 100 - (3 * 10)   # sin penalidad de tasa
        score = _calculate_score(summary, [], has_5xx=False, has_4xx=False)
        assert score < score_sin_tasa      # la penalidad de tasa se aplicó


# ─── _determine_severity() ────────────────────────────────────────────────────

class TestDetermineSeverity:

    def test_5xx_es_critical(self):
        resultado = _determine_severity([], has_5xx=True, has_4xx=False, fail_rate=100, n_failed=1)
        assert resultado == 'CRITICAL'

    def test_network_error_es_critical(self):
        issues = [_make_issue('NETWORK_ERROR', 'CRITICAL')]
        resultado = _determine_severity(issues, has_5xx=False, has_4xx=False, fail_rate=100, n_failed=1)
        assert resultado == 'CRITICAL'

    def test_100pct_fallo_sin_5xx_es_high(self):
        resultado = _determine_severity([], has_5xx=False, has_4xx=False, fail_rate=100, n_failed=2)
        assert resultado == 'HIGH'

    def test_4xx_parcial_es_medium(self):
        resultado = _determine_severity([], has_5xx=False, has_4xx=True, fail_rate=50, n_failed=1)
        assert resultado == 'MEDIUM'

    def test_fallo_sin_http_es_medium(self):
        resultado = _determine_severity([], has_5xx=False, has_4xx=False, fail_rate=50, n_failed=1)
        assert resultado == 'MEDIUM'

    def test_sin_fallos_es_low(self):
        resultado = _determine_severity([], has_5xx=False, has_4xx=False, fail_rate=0, n_failed=0)
        assert resultado == 'LOW'

    def test_latencia_alta_sin_fallos_escala_severity(self):
        issues = [_make_issue('HIGH_LATENCY_CRITICAL', 'HIGH')]
        resultado = _determine_severity(issues, has_5xx=False, has_4xx=False, fail_rate=0, n_failed=0)
        assert resultado in ('HIGH', 'MEDIUM')

    def test_guard_fallo_nunca_es_low(self):
        resultado = _determine_severity([], has_5xx=False, has_4xx=False, fail_rate=50, n_failed=1)
        assert resultado != 'LOW'


# ─── analyze() ────────────────────────────────────────────────────────────────

class TestAnalyze:

    def test_retorna_estructura_completa(self, mock_ai_service):
        results = [_make_result('valid_request', 200, response_body='{"ok": true}')]
        output = analyze(results)
        assert all(k in output for k in ('issues', 'severity', 'quality_score', 'insights', 'summary'))

    def test_summary_total_correcto(self, mock_ai_service):
        results = [
            _make_result('valid_request', 200),
            _make_result('missing_payload', 422),
            _make_result('invalid_types', 400),
        ]
        output = analyze(results)
        assert output['summary']['total'] == 3

    def test_valid_request_exitoso_low(self, mock_ai_service):
        results = [_make_result('valid_request', 200, response_body='{"id": 1}')]
        output = analyze(results)
        assert output['severity'] == 'LOW'
        assert output['quality_score'] == 100

    def test_5xx_produce_critical(self, mock_ai_service):
        results = [_make_result('valid_request', 500)]
        output = analyze(results)
        assert output['severity'] == 'CRITICAL'
        assert output['quality_score'] <= 40

    def test_guard_score_no_100_con_fallos(self, mock_ai_service):
        results = [_make_result('valid_request', 400)]
        output = analyze(results)
        assert output['quality_score'] != 100

    def test_guard_severity_no_low_con_fallos(self, mock_ai_service):
        results = [_make_result('valid_request', 400)]
        output = analyze(results)
        assert output['severity'] != 'LOW'

    def test_missing_payload_aceptado_agrega_issue(self, mock_ai_service):
        results = [_make_result('missing_payload', 200, response_body='{"ok": true}')]
        output = analyze(results)
        issue_types = [i.split(' · ')[0] for i in output['issues']]
        assert any('MISSING_PAYLOAD' in t or 'missing' in t.lower() or 'payload' in t.lower()
                   for t in issue_types + output['issues'])

    def test_invalid_types_aceptado_agrega_issue(self, mock_ai_service):
        results = [_make_result('invalid_types', 200, response_body='{"ok": true}')]
        output = analyze(results)
        assert any('invalid' in i.lower() or 'type' in i.lower() or 'tipo' in i.lower()
                   for i in output['issues'])

    def test_expected_schema_faltante(self, mock_ai_service):
        import json
        results = [_make_result('valid_request', 200,
                                response_body=json.dumps({'nombre': 'Ivan'}))]
        output = analyze(results, expected_schema={'id': 'int'})
        assert any('id' in i.lower() or 'schema' in i.lower() for i in output['issues'])

    def test_fallback_cuando_ai_lanza_excepcion(self, mocker):
        mocker.patch(
            'app.services.ai_service.generate_ai_insights',
            side_effect=Exception('Ollama no disponible'),
        )
        results = [_make_result('valid_request', 200, response_body='{"ok": true}')]
        output = analyze(results)
        assert len(output['insights']) > 0
