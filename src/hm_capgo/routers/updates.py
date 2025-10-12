from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Device, Version
from ..schemas import UpdateRequest, UpdateResponse

router = APIRouter(tags=["updates"])


@router.post("/update", response_model=UpdateResponse)
async def get_update(req: UpdateRequest, db: AsyncSession = Depends(get_session)) -> UpdateResponse:
    result = await db.execute(select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id))
    device = result.scalar_one_or_none()

    if not device:
        device = Device(device_id=req.device_id, app_id=req.app_id)
        db.add(device)
        await db.commit()
        await db.refresh(device)

    version = await db.scalar(
        select(Version)
        .where(Version.channel == device.channel, Version.active == 1)
        .order_by(Version.created_at.desc())
        .limit(1)
    )
    if not version:
        return UpdateResponse()

    return UpdateResponse(version=version.version, url=version.url, checksum=version.checksum)
