from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_admin
from ..database import get_session
from ..devices import device_channel, device_is_prod
from ..models import Device, Stat, Version
from ..schemas import (
    AddVersionRequest,
    AddVersionResponse,
    DeviceGroup,
    DeviceInfo,
    EventGroup,
    PatchVersionRequest,
    StatsSummary,
    VersionInfo,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def version_info(v: Version) -> VersionInfo:
    return VersionInfo(
        version=str(v.version),
        url=str(v.url),
        checksum=str(v.checksum),
        native=v.native,
        channel=v.channel,
        active=bool(v.active),
        created_at=v.created_at,
    )


async def find_version(db: AsyncSession, version: str, channel: str) -> Version:
    v = await db.scalar(select(Version).where(Version.version == version, Version.channel == channel))
    if v is None:
        raise HTTPException(status_code=404, detail=f"Version '{version}' not found in channel '{channel}'")
    return v


@router.post("/version", response_model=AddVersionResponse)
async def add_version(
    req: AddVersionRequest,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> AddVersionResponse:
    """Add a new version if it doesn't already exist for the same channel."""
    existing = await db.scalar(
        select(Version).where(
            Version.version == req.version,
            Version.channel == req.channel,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version '{req.version}' already exists in channel '{req.channel}'",
        )

    v = Version(
        version=req.version,
        url=req.url,
        checksum=req.checksum,
        native=req.native,
        channel=req.channel,
        active=int(req.active),
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    return AddVersionResponse(status="ok", version=str(v.version), channel=str(v.channel))


@router.get("/version", response_model=list[VersionInfo])
async def get_versions(
    channel: str | None = None,
    native: str | None = None,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> list[VersionInfo]:
    """Return all versions, newest first, optionally filtered by channel and native build."""
    query = select(Version).order_by(desc(Version.created_at), desc(Version.id))
    if channel:
        query = query.where(Version.channel == channel)
    if native:
        query = query.where(Version.native == native)

    result = await db.execute(query)
    return [version_info(v) for v in result.scalars().all()]


@router.patch("/version/{version}", response_model=VersionInfo)
async def update_version(
    version: str,
    req: PatchVersionRequest,
    channel: str = "production",
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> VersionInfo:
    """Change a version; {"active": false} takes it back, and devices move to the previous one."""
    v = await find_version(db, version, channel)

    if req.url is not None:
        v.url = req.url
    if req.checksum is not None:
        v.checksum = req.checksum
    if req.native is not None:
        v.native = req.native
    if req.active is not None:
        v.active = int(req.active)
    await db.commit()
    await db.refresh(v)

    return version_info(v)


@router.delete("/version/{version}", response_model=AddVersionResponse)
async def delete_version(
    version: str,
    channel: str = "production",
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> AddVersionResponse:
    """Delete version record."""
    v = await find_version(db, version, channel)

    await db.delete(v)
    await db.commit()

    return AddVersionResponse(status="deleted", version=str(v.version), channel=str(v.channel))


@router.get("/devices", response_model=list[DeviceInfo])
async def get_devices(
    limit: int = 50,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> list[DeviceInfo]:
    """The devices seen last, with the channel and bundle each one reported."""
    result = await db.execute(select(Device).order_by(desc(Device.last_seen)).limit(min(limit, 500)))

    return [
        DeviceInfo(
            device_id=str(d.device_id),
            app_id=str(d.app_id),
            channel=device_channel(d),
            channel_override=bool(d.channel),
            is_prod=device_is_prod(d),
            version_build=d.version_build,
            version_name=d.version_name,
            last_seen=d.last_seen,
        )
        for d in result.scalars().all()
    ]


@router.get("/stats", response_model=StatsSummary)
async def get_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> StatsSummary:
    """How updates go for the last days: devices by channel, native build and bundle, and updater events by bundle."""
    days = max(1, min(days, 365))
    since = func.now() - timedelta(days=days)

    channel = func.coalesce(Device.channel, case((Device.is_prod == 0, "test"), else_="production"))
    device_rows = await db.execute(
        select(channel, Device.version_build, Device.version_name, func.count())
        .where(Device.last_seen > since)
        .group_by(channel, Device.version_build, Device.version_name)
        .order_by(func.count().desc())
    )
    devices = [
        DeviceGroup(channel=row[0], version_build=row[1], version_name=row[2], devices=row[3]) for row in device_rows
    ]

    event_rows = await db.execute(
        select(Stat.version_name, Stat.action, func.count(), func.count(distinct(Stat.device_id)))
        .where(Stat.ts > since)
        .group_by(Stat.version_name, Stat.action)
        .order_by(Stat.version_name.desc(), func.count().desc())
    )
    events = [EventGroup(version_name=row[0], action=row[1], events=row[2], devices=row[3]) for row in event_rows]

    return StatsSummary(
        days=days,
        active_devices=sum(group.devices for group in devices),
        failures=sum(group.events for group in events if group.action.endswith("_fail")),
        devices=devices,
        events=events,
    )
