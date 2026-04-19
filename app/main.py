from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.test_routes import router
from app.services.history_service import init_db

app = FastAPI()

init_db()

app.include_router(router)
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")