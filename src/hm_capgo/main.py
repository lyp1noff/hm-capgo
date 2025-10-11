from datetime import datetime, UTC

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .models import Version, Device, Stat
from .schemas import UpdateRequest, UpdateResponse, CapgoStats, ChannelRequest, ChannelResponse, AddVersionResponse, \
    AddVersionRequest

IGNORED_ACTION_PREFIXES = ["download_", "app_moved_to"]
app = FastAPI(root_path="/capgo")


@app.post("/admin/version", response_model=AddVersionResponse)
async def add_version(req: AddVersionRequest, session: AsyncSession = Depends(get_session)):
    v = Version(
        version=req.version,
        url=req.url,
        checksum=req.checksum,
        channel=req.channel,
        active=req.active
    )
    session.add(v)
    await session.commit()
    return AddVersionResponse(status="ok", version=v.version, channel=v.channel)


@app.post("/update", response_model=UpdateResponse)
async def get_update(req: UpdateRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        device = Device(device_id=req.device_id, app_id=req.app_id)
        session.add(device)
        await session.commit()
        await session.refresh(device)

    version = await session.scalar(
        select(Version)
        .where(Version.channel == device.channel, Version.active == 1)
        .order_by(Version.created_at.desc())
        .limit(1)
    )
    if not version or version.version == req.version_name:
        return UpdateResponse()

    return UpdateResponse(version=version.version, url=version.url, checksum=version.checksum)


@app.post("/stats")
async def receive_stats(stats: CapgoStats, request: Request, session: AsyncSession = Depends(get_session)):
    if any(stats.action.startswith(prefix) for prefix in IGNORED_ACTION_PREFIXES) and stats.action != "download_failed":
        print(f"[SKIP] {stats.device_id} {stats.version_name} {stats.action}")
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
    session.add(entry)
    await session.commit()
    print(
        f"[{datetime.now(UTC).isoformat()}] {request.client.host}: {stats.device_id} {stats.version_name} {stats.action}")
    return {"status": "ok"}


@app.put("/channel_self", response_model=ChannelResponse)
async def put_channel(req: Request, session: AsyncSession = Depends(get_session)):
    data = await req.json()
    device_id = data.get("device_id")
    app_id = data.get("app_id")

    if not device_id or not app_id:
        return ChannelResponse(status="default", channel="production", allowSet=True)

    result = await session.execute(
        select(Device).where(Device.device_id == device_id, Device.app_id == app_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        device = Device(device_id=device_id, app_id=app_id, channel="production")
        session.add(device)
        await session.commit()
        await session.refresh(device)

    status = "override" if device.channel != "production" else "default"

    return ChannelResponse(status=status, channel=device.channel, allowSet=True)


@app.post("/channel_self", response_model=ChannelResponse)
async def set_channel(req: ChannelRequest, session: AsyncSession = Depends(get_session)):
    if not req.channel:
        return ChannelResponse(status="error", error="Channel not specified")
    result = await session.execute(
        select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        device = Device(device_id=req.device_id, app_id=req.app_id, channel=req.channel)
        session.add(device)
    else:
        device.channel = req.channel
    await session.commit()
    return ChannelResponse(status="ok", message="Channel set", channel=req.channel)


@app.delete("/channel_self", response_model=ChannelResponse)
async def unset_channel(req: ChannelRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Device).where(Device.device_id == req.device_id, Device.app_id == req.app_id)
    )
    device = result.scalar_one_or_none()
    if device:
        device.channel = "production"
        await session.commit()
    return ChannelResponse(status="ok", message="Channel unset", channel="production")
