from fastapi import FastAPI

from .config import DEBUG
from .routers import admin, channels, stats, updates

app = FastAPI(
    title="Capgo API",
    root_path="/capgo",
    docs_url=None if not DEBUG else "/docs",
    redoc_url=None if not DEBUG else "/redoc",
    openapi_url=None if not DEBUG else "/openapi.json",
)

app.include_router(updates.router)
app.include_router(stats.router)
app.include_router(channels.router)
app.include_router(admin.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
