import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import get_settings
from app.database.connection import engine, Base, SessionLocal
from app.database.seed import seed_database
from app.routes import auth, api, relatorios
from app.routes.websocket import websocket_morangia

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Moranguinho Stock Manager API",
    description="API de almoxarifado do Supermercado Moranguinho",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(api.router)
app.include_router(relatorios.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "online", "sistema": "Moranguinho Stock Manager", "ia": "MorangIA"}


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if os.path.isdir(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.websocket("/ws/morangia")
async def ws_morangia(websocket: WebSocket, token: str = ""):
    await websocket_morangia(websocket, token)
