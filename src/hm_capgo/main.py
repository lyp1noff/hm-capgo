from fastapi import FastAPI

from .routers import admin, channels, stats, updates

app = FastAPI(root_path="/capgo")

app.include_router(updates.router)
app.include_router(stats.router)
app.include_router(channels.router)
app.include_router(admin.router)
