# API Sentinel – AI API Quality Analyzer

Una herramienta profesional para probar y analizar la calidad de APIs usando inteligencia artificial. Detecta problemas de validación, tipos de datos inválidos y proporciona insights detallados sobre la salud de tu API.

## Características

- **Testing Automático**: Ejecuta tests contra cualquier endpoint HTTP
- **Análisis de Validación**: Detecta problemas de validación de datos y tipos inválidos
- **Scoring de Calidad**: Obtén un score 0-100 basado en los resultados de los tests
- **Análisis IA**: Recibe insights inteligentes sobre problemas detectados
- **Dashboard Moderno**: Interfaz SaaS dark-mode con visualización de resultados en tiempo real
- **Clasificación de Severidad**: Identifica problemas como Low, High o Critical

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5 + Vanilla JavaScript + CSS3
- **Testing**: Requests library con timeout configurable
- **IA**: Análisis inteligente de resultados y generación de insights

## Instalación

### Requisitos

- Python 3.8+
- pip o pip virtual environment

### Setup

```bash
# Clonar el repositorio
git clone git@github.com:ivanpr87/Probador_APIs.git
cd Probador_APIs

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn requests

# Iniciar servidor
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://127.0.0.1:8000`

## Estructura del Proyecto

```
.
├── app/
│   ├── main.py                 # Configuración FastAPI
│   ├── routes/
│   │   └── test_routes.py      # Endpoints de la API
│   ├── services/
│   │   ├── test_service.py     # Orquestación de tests
│   │   ├── test_generator.py   # Generación de tests
│   │   ├── analyzer.py         # Análisis de resultados
│   │   └── ai_analyzer.py      # Análisis con IA
│   └── static/
│       └── index.html          # Dashboard frontend
├── venv/                       # Entorno virtual
├── .gitignore
└── README.md
```

## API Endpoints

### POST /run-test

Ejecuta una serie de tests contra el endpoint especificado.

**Request Body:**
```json
{
  "url": "https://api.example.com/endpoint",
  "method": "GET",
  "payload": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Parámetros:**
- `url` (string, requerido): URL del endpoint a probar
- `method` (string, requerido): Método HTTP (GET, POST)
- `payload` (object, opcional): Datos a enviar en la request

**Response:**
```json
{
  "total_tests": 5,
  "results": [
    {
      "test_name": "test_1",
      "status_code": 200,
      "response_time": 0.123,
      "error": null
    }
  ],
  "issues_detected": [
    "Validación de payload incompleta",
    "Tipos de datos inválidos"
  ],
  "severity": "high",
  "quality_score": 65,
  "ai_insights": [
    "La API no valida la presencia de datos obligatorios..."
  ]
}
```

## Uso del Dashboard

1. **Ingresa la URL**: Escribe la URL del endpoint a probar
2. **Selecciona el método HTTP**: GET o POST
3. **Agrega payload** (opcional): JSON para requests POST
4. **Ejecuta los tests**: Click en "Ejecutar Tests"
5. **Revisa resultados**:
   - Score de calidad (0-100)
   - Nivel de severidad (Low/High/Critical)
   - Detalles de tests ejecutados
   - Problemas detectados
   - Insights de IA

## Interpretación de Resultados

### Quality Score
- **80-100**: Excelente – API está bien validada
- **70-79**: Bueno – Algunos problemas menores
- **40-69**: Regular – Problemas de validación detectados
- **0-39**: Crítico – Riesgos significativos

### Severity Levels
- **Low** (Verde): No hay problemas detectados
- **High** (Naranja): Problemas de validación de datos
- **Critical** (Rojo): Problemas de tipos de datos o riesgos en producción

## Desarrollo

### Ejecutar tests (si existen)
```bash
# Framework: Playwright (cuando esté configurado)
pnpm test
```

### Code Style
- Python: PEP 8
- JavaScript: 4 espacios, single quotes
- Comentarios solo donde no sea obvio

## Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-feature`)
3. Commit cambios (`git commit -m 'feat: descripción'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está disponible bajo licencia MIT.

## Autor

**Ivan Bastos** – AI Automation Specialist  
Buenos Aires, Argentina  
[ivanbastos18@gmail.com](mailto:ivanbastos18@gmail.com)

## Soporte

Para reportar bugs o sugerir features, abre un issue en GitHub.

---

**Última actualización:** 2026-04-19
