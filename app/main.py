from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.test_routes import router

app = FastAPI()

# 👉 incluir rutas
app.include_router(router)

# 👉 servir la UI
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")