from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..devices import device_channel, touch_device
from ..models import Version
from ..schemas import UpdateRequest, UpdateResponse

router = APIRouter(tags=["updates"])

# The plugin's name for the bundle shipped inside the app: answering it sends the device back to that bundle.
BUILTIN = "builtin"


@router.post("/update", response_model=UpdateResponse, response_model_exclude_none=True)
async def get_update(req: UpdateRequest, db: AsyncSession = Depends(get_session)) -> UpdateResponse:
    device = await touch_device(
        db,
        req.device_id,
        req.app_id,
        is_prod=req.is_prod,
        version_build=req.version_build,
        version_name=req.version_name,
    )

    # A bundle runs only on the native build it was made with: a newer one may call native code an older app lacks.
    version = None
    if req.version_build:
        version = await db.scalar(
            select(Version)
            .where(
                Version.channel == device_channel(device),
                Version.native == req.version_build,
                Version.active == 1,
            )
            .order_by(Version.created_at.desc(), Version.id.desc())
            .limit(1)
        )

    # Nothing for this build (or everything for it switched off): the device goes back to its own bundle.
    if version is None:
        return UpdateResponse(version=BUILTIN)

    return UpdateResponse(version=version.version, url=version.url, checksum=version.checksum)
