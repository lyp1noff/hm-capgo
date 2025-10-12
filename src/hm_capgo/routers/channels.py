from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Device
from ..schemas import ChannelRequest, ChannelResponse

router = APIRouter(tags=["channels"])


@router.put("/channel_self", response_model=ChannelResponse)
async def put_channel(req: Request, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    data = await req.json()
    device_id, app_id = data.get("device_id"), data.get("app_id")

    if not device_id or not app_id:
        return ChannelResponse(status="default", channel="production", allowSet=True)

    result = await db.execute(select(Device).where(Device.device_id == device_id, Device.app_id == app_id))
    device = result.scalar_one_or_none()

    if not device:
        device = Device(device_id=device_id, app_id=app_id, channel="production")
        db.add(device)
        await db.commit()
        await db.refresh(device)

    status = "override" if device.channel != "production" else "default"
    return ChannelResponse(status=status, channel=device.channel, allowSet=True)


@router.post("/channel_self", response_model=ChannelResponse)
async def set_channel(req: ChannelRequest, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    if not req.channel:
        return ChannelResponse(status="error", error="Channel not specified")

    result = await db.execute(select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id))
    device = result.scalar_one_or_none()

    if not device:
        device = Device(device_id=req.device_id, app_id=req.app_id, channel=req.channel)
        db.add(device)
    else:
        device.channel = req.channel

    await db.commit()
    return ChannelResponse(status="ok", message="Channel set", channel=req.channel)


@router.delete("/channel_self", response_model=ChannelResponse)
async def unset_channel(req: ChannelRequest, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    result = await db.execute(select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id))
    device = result.scalar_one_or_none()
    if device:
        device.channel = "production"
        await db.commit()
    return ChannelResponse(status="ok", message="Channel unset", channel="production")
