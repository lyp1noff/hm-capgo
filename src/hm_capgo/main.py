from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime, UTC

app = FastAPI()

class CapgoStats(BaseModel):
    action: str
    app_id: str
    device_id: str
    platform: str | None = None
    version_name: str | None = None
    version_build: str | None = None
    version_code: str | None = None
    version_os: str | None = None
    plugin_version: str | None = None
    is_emulator: bool | None = None
    is_prod: bool | None = None

@app.post("/capgo/stats")
async def receive_stats(stats: CapgoStats, request: Request):
    ip = request.client.host
    ts = datetime.now(UTC).isoformat()

    print(f"[{ts}] From {ip}: {stats.action} {stats.version_name} {stats.device_id}")

    return {"status": "ok"}
