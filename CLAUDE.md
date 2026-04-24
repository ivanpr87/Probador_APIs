# CLAUDE.md — API Sentinel (ai-api-testing-agent)

> Contexto de proyecto para Claude. Complementa el CLAUDE.md global en `~/.claude/CLAUDE.md`.
> Las reglas globales (SOLID, Clean Architecture, restricciones, comandos) siguen vigentes.

---

## Qué es este proyecto

Analizador de calidad de APIs con IA. Stress-testea endpoints HTTP automáticamente,
puntúa su robustez de validación (0–100) y genera insights bilingües (ES/EN)
con un LLM local (Ollama `qwen3:8b`) o fallback rule-based si Ollama no está disponible.

**Estado:** Producción.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| AI Engine | Ollama (`qwen3:8b`) — LLM local vía REST |
| HTTP Testing | `requests` · `ThreadPoolExecutor` (4 workers, paralelo) |
| Scheduling | APScheduler 3.x (BackgroundScheduler, CronTrigger) |
| Persistencia | SQLite vía `sqlite3` — patrón Repository |
| Validación | Pydantic v2 |
| Frontend | HTML5 · Vanilla JS · CSS3 (dark mode) |
| Gestor de paquetes | pip (entorno virtual en `venv/`) |

---

## Arquitectura

Clean Architecture en Python. Capas en `app/`:

```
api/routes/      → Routers FastAPI (presentación) — no contienen lógica
services/        → Lógica de negocio: test_service, analysis_service, ai_service, scheduler_service
repositories/    → Acceso a SQLite: test_repository, configs_repository, scheduler_repository
models/          → Schemas Pydantic: request_models, response_models, scheduler_models
core/            → config.py (settings vía .env), database.py (init SQLite, WAL mode)
utils/           → http_client.py (ejecutor HTTP con timeout 5s y captura de body)
static/          → Frontend: index.html, app.js, styles.css
tests/           → Pytest: espeja estructura de app/, DB en :memory:, mocks con pytest-mock
```

**Regla crítica:** los servicios no importan de `api/routes/`. Los repositorios no importan de `services/`. Las dependencias fluyen hacia adentro.

---

## Módulos y archivos clave

| Archivo | Responsabilidad |
|---|---|
| `app/services/test_service.py` | Generación de casos de prueba + ejecución paralela (ThreadPoolExecutor) |
| `app/services/analysis_service.py` | Motor de scoring (0–100), detección de issues (5 categorías), severidad |
| `app/services/ai_service.py` | Integración Ollama + fallback rule-based bilingüe |
| `app/services/scheduler_service.py` | Ciclo de vida APScheduler + registro de jobs |
| `app/repositories/test_repository.py` | CRUD historial de tests en SQLite |
| `app/repositories/configs_repository.py` | CRUD configuraciones guardadas |
| `app/repositories/scheduler_repository.py` | CRUD schedules + toggle + last_run |
| `app/core/config.py` | Settings: URL Ollama, modelo, timeouts, path DB |
| `app/core/database.py` | Init SQLite, WAL mode, creación de schema |
| `app/utils/http_client.py` | Ejecutor HTTP (timeout 5s, captura 500 chars del body) |
| `sentinel.db` | Base de datos SQLite (se crea automáticamente) |

---

## API Endpoints

| Endpoint | Método | Descripción |
|---|---|---|
| `/run-test` | POST | Ejecuta batería de tests contra un endpoint |
| `/history` | GET | Historial paginado (20/página), filtros: `url_filter`, `severity_filter`, `page` |
| `/history/{id}` | GET | Resultado completo de un test |
| `/configs` | GET/POST/DELETE | CRUD configuraciones guardadas |
| `/schedules` | GET/POST/DELETE | CRUD schedules cron |
| `/schedules/{id}/toggle` | PATCH | Activar/desactivar schedule sin eliminarlo |

---

## Lógica de scoring — NO modificar sin análisis previo

El score parte de 100 y aplica penalizaciones en orden de prioridad:

| Señal | Penalización |
|---|---|
| 5xx o endpoint inalcanzable | Techo: score máximo = 40 |
| Solo 4xx (sin 5xx) | Piso: score mínimo = 40 |
| Cada test fallido | −10 pts |
| 100% fallo + 5xx | −50 pts |
| 100% fallo, solo 4xx | −30 pts |
| Tasa de fallo > 50% | −20 pts |
| Cada respuesta 4xx | −5 pts (cap −30) |
| Latencia promedio > 1200 ms | −10 pts |
| Latencia promedio > 700 ms | −5 pts |
| Tipos inválidos aceptados | −20 pts |
| Payload faltante aceptado | −10 pts |
| Falso positivo (200 + body de error) | −5 pts |

**Severidad** se deriva de señales, no del score:
- CRITICAL: cualquier 5xx o endpoint inalcanzable
- HIGH: 100% de fallo sin 5xx
- MEDIUM: cualquier 4xx o fallo no clasificado
- LOW: sin fallos

---

## Generación de test cases

| Método | Tests generados |
|---|---|
| DELETE | 1: `valid_request` |
| GET sin payload | 1–2 tests |
| POST / PUT / PATCH | Hasta 4: `valid_request`, `missing_payload`, `invalid_types`, `incomplete_payload` |
| Casos custom del usuario | Se agregan y ejecutan en paralelo |

---

## Comandos

```bash
# Levantar servidor
venv\Scripts\activate
uvicorn app.main:app --reload          # :8000

# Instalar dependencias
pip install -r requirements.txt

# Correr todos los tests
pytest tests/ -v

# Correr un test específico
pytest tests/services/test_analysis_service.py::TestIsFailure::test_valid_request_2xx_pasa -v

# Cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

Ollama (opcional para insights IA):
```bash
ollama pull qwen3:8b
ollama serve
```

---

## Variables de entorno

Copiar `.env.example` → `.env` y ajustar. Cargadas automáticamente al iniciar vía `python-dotenv`.

| Variable | Default | Descripción |
|---|---|---|
| `DB_PATH` | `sentinel.db` | Path a la base SQLite |
| `HTTP_TIMEOUT` | `5` | Timeout por request HTTP (segundos) |
| `HISTORY_LIMIT` | `50` | Máximo de items por página en historial |
| `OLLAMA_URL` | `http://localhost:11434` | URL del servidor Ollama local |
| `OLLAMA_MODEL` | `qwen3:8b` | Modelo LLM a usar |
| `OLLAMA_TIMEOUT` | `30` | Timeout para respuesta de Ollama (segundos) |

---

## Restricciones específicas de este proyecto

- **No cambiar la lógica de scoring** (`analysis_service.py`) sin `/pre-code` aprobado — es el núcleo del producto.
- **No cambiar el schema de SQLite** (`database.py`) sin migración explícita — rompe el historial existente en `sentinel.db`.
- **Ollama es opcional**: el sistema debe funcionar siempre con el fallback rule-based. Nunca hacer el AI service obligatorio.
- **ThreadPoolExecutor usa 4 workers**: no cambiar sin medir impacto en latencia.
- **Pydantic v2**: no mezclar sintaxis v1. Usar `model_validator`, `field_validator`, no `@validator`.
- **Gestor de paquetes: pip** con virtualenv en `venv/`. No usar poetry ni pnpm.
- **Tests unitarios con Pytest** — ver sección "Testing unitario" más abajo. Framework y estructura ya definidos.

---

## Testing unitario

**Framework:** Pytest

### Setup (una sola vez)

```bash
venv\Scripts\activate
pip install pytest pytest-mock
```

### Estructura de tests

Los tests viven en `tests/`, espejando la estructura de `app/`:

```
tests/
  services/
    test_analysis_service.py    ← prioridad ALTA
    test_test_service.py        ← prioridad ALTA
    test_ai_service.py          ← prioridad MEDIA
    test_scheduler_service.py   ← prioridad BAJA
  repositories/
    test_test_repository.py     ← prioridad MEDIA
```

Script para correr los tests:

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

### Qué cubrir primero (por impacto de negocio)

| Módulo | Prioridad | Casos críticos a cubrir |
|---|---|---|
| `analysis_service.py` | 🔴 Alta | Score 100 sin penalizaciones, techo=40 con 5xx, piso=40 con solo 4xx, penalización por tipos inválidos aceptados, latencia > 1200 ms |
| `test_service.py` | 🔴 Alta | GET sin payload genera 1-2 casos, POST genera 4 casos, DELETE genera 1 caso, casos custom se agregan correctamente |
| `ai_service.py` | 🟡 Media | Ollama disponible retorna insights, Ollama caído activa fallback rule-based, respuesta vacía no rompe el flujo |
| `test_repository.py` | 🟡 Media | Guardar resultado, paginar historial, filtrar por URL y severidad |

### Convenciones

- Usar `pytest-mock` (`mocker.patch`) para mockear llamadas HTTP a Ollama y a endpoints externos.
- Nunca usar `sentinel.db` real en tests — usar una DB en memoria (`":memory:"`) o fixture temporal.
- Nombres descriptivos: `test_score_es_40_cuando_hay_respuesta_5xx`.
- Un test por comportamiento, no por función.

---

## Limitaciones conocidas (documentadas en README)

- Sin OAuth / token refresh — los headers de auth son pass-through.
- Scoring basado en promedio de latencia, sin p95/p99.
- SQLite solo apto para uso local — migrar a PostgreSQL cambiando solo `database.py`.
- SQLite single-writer — no apto para múltiples procesos concurrentes.
