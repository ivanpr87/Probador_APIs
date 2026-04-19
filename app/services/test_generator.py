def generate_tests(base_request):
    url = base_request.get("url")
    method = base_request.get("method")
    payload = base_request.get("payload", {})

    tests = []

    # ✅ 1. Test válido
    tests.append({
        "test_name": "valid_request",
        "url": url,
        "method": method,
        "payload": payload
    })

    # ❌ 2. Sin payload
    tests.append({
        "test_name": "missing_payload",
        "url": url,
        "method": method,
        "payload": None
    })

    # ❌ 3. Tipos inválidos
    invalid_payload = {}

    for key, value in payload.items():
        if isinstance(value, int):
            invalid_payload[key] = "invalid_string"
        elif isinstance(value, str):
            invalid_payload[key] = 999
        else:
            invalid_payload[key] = None

    tests.append({
        "test_name": "invalid_types",
        "url": url,
        "method": method,
        "payload": invalid_payload
    })

    # ❌ 4. Payload incompleto (falta un campo)
    if payload:
        incomplete_payload = payload.copy()
        first_key = list(payload.keys())[0]
        incomplete_payload.pop(first_key)

        tests.append({
            "test_name": "incomplete_payload",
            "url": url,
            "method": method,
            "payload": incomplete_payload
        })

    return tests