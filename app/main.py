from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.test_routes import router
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

init_db()

app.include_router(router)
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
