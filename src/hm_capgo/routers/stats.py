import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..logger import logger
from ..models import Stat
from ..schemas import CapgoStats

router = APIRouter(tags=["stats"])

# Sent on every app start or download step: neither stored nor logged.
NOISE_ACTIONS = {"app_moved_to_foreground", "app_moved_to_background"}
DOWNLOAD_PROGRESS = re.compile(r"download_\d+")


def is_noise(action: str) -> bool:
    return action in NOISE_ACTIONS or DOWNLOAD_PROGRESS.fullmatch(action) is not None


def is_failure(action: str) -> bool:
    return action.endswith("_fail")


@router.post("/stats")
async def receive_stats(stats: CapgoStats, db: AsyncSession = Depends(get_session)) -> dict[str, str]:
    if is_noise(stats.action):
        return {"status": "skipped"}

    db.add(
        Stat(
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
    )
    await db.commit()

    # Only failures reach the log; everything else is in the stats table (GET /admin/stats).
    if is_failure(stats.action):
        logger.warning(
            f"{stats.action} bundle={stats.version_name} native={stats.version_build} "
            f"device={stats.device_id[:8]} ios={stats.version_os}"
        )
    return {"status": "ok"}
