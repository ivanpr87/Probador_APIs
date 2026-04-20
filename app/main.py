from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.api.routes.configs_routes import router as configs_router
from app.api.routes.test_routes import router
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

init_db()

app.include_router(router)
app.include_router(configs_router)


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if any(request.url.path.endswith(ext) for ext in (".js", ".css", ".html", "")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
