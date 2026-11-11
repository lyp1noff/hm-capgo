from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..devices import CHANNELS, device_channel, device_is_prod, install_channel, touch_device
from ..schemas import ChannelRequest, ChannelResponse

router = APIRouter(tags=["channels"])


@router.put("/channel_self", response_model=ChannelResponse, response_model_exclude_none=True)
async def put_channel(req: Request, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    data = await req.json()
    device_id, app_id = data.get("device_id"), data.get("app_id")
    is_prod = data.get("is_prod")

    if not device_id or not app_id:
        return ChannelResponse(status="default", channel=install_channel(is_prod), allowSet=False)

    device = await touch_device(
        db,
        device_id,
        app_id,
        is_prod=is_prod if isinstance(is_prod, bool) else None,
        version_build=data.get("version_build"),
        version_name=data.get("version_name"),
    )
    status = "override" if device.channel else "default"
    return ChannelResponse(status=status, channel=device_channel(device), allowSet=device_is_prod(device) is False)


@router.post("/channel_self", response_model=ChannelResponse, response_model_exclude_none=True)
async def set_channel(req: ChannelRequest, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    # Only test installs may switch: an App Store install never gets bundles meant for testers.
    if req.is_prod is not False:
        return ChannelResponse(status="error", error="channel_not_allowed", allowSet=False)
    if req.channel not in CHANNELS:
        return ChannelResponse(status="error", error="unknown_channel")

    device = await touch_device(
        db,
        req.device_id,
        req.app_id,
        is_prod=req.is_prod,
        version_build=req.version_build,
        version_name=req.version_name,
    )
    device.channel = None if req.channel == install_channel(req.is_prod) else req.channel
    await db.commit()

    return ChannelResponse(status="ok", message="Channel set", channel=req.channel)


@router.delete("/channel_self", response_model=ChannelResponse, response_model_exclude_none=True)
async def unset_channel(req: ChannelRequest, db: AsyncSession = Depends(get_session)) -> ChannelResponse:
    device = await touch_device(db, req.device_id, req.app_id, is_prod=req.is_prod)
    device.channel = None
    await db.commit()

    return ChannelResponse(status="ok", message="Channel unset", channel=install_channel(req.is_prod))
