def analyze_results(results):
    issues = []

    for result in results:
        test_name = result.get("test_name")
        status = result.get("status_code")

        # Reglas básicas QA
        if test_name == "missing_payload" and (status == 200 or status == 201):
            issues.append("API acepta requests sin payload (debería fallar)")

        if test_name == "invalid_types" and (status == 200 or status == 201):
            issues.append("API acepta tipos inválidos (falta validación)")

    return issues