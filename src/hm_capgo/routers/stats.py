from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..logger import logger
from ..models import Stat
from ..schemas import CapgoStats

router = APIRouter(tags=["stats"])


@router.post("/stats")
async def receive_stats(stats: CapgoStats, request: Request, db: AsyncSession = Depends(get_session)) -> dict[str, str]:
    if stats.action not in {"download_failed", "download_complete"} and stats.action.startswith(
        ("download_", "app_moved_to")
    ):
        logger.info(f"[SKIP] {stats.device_id} {stats.version_name} {stats.action}")
        return {"status": "skipped"}

    entry = Stat(
        action=stats.action,
        app_id=stats.app_id,
        device_id=stats.device_id,
        custom_id=stats.custom_id,
        platform=stats.platform,
        version_name=stats.version_name,
        version_build=stats.version_build,
        version_code=stats.version_code,
        version_os=stats.version_os,
    )
    db.add(entry)
    await db.commit()
    host = request.client.host if request.client else "unknown"
    logger.info(f"[{datetime.now(UTC).isoformat()}] {host}: {stats.device_id} {stats.version_name} {stats.action}")
    return {"status": "ok"}
