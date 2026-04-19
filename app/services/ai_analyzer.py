def ai_analyze(issues, results):
    insights = []
    severity = "low"

    if any("payload" in i for i in issues):
        severity = "high"
        insights.append(
            "La API no valida la presencia de datos obligatorios. Puede aceptar requests incompletos."
        )

    if any("tipos inválidos" in i for i in issues):
        severity = "critical"
        insights.append(
            "La API no valida tipos de datos. Riesgo de errores en base de datos o fallos en producción."
        )

    if not issues:
        insights.append("No se detectaron problemas en los tests ejecutados.")

    return {
        "severity": severity,
        "insights": insights
    }
    
def calculate_score(issues):
    score = 100

    for issue in issues:
        if "payload" in issue:
            score -= 30
        elif "tipos inválidos" in issue:
            score -= 40

    return max(score, 0)