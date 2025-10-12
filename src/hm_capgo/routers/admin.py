from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import verify_admin
from ..database import get_session
from ..models import Version
from ..schemas import AddVersionRequest, AddVersionResponse, UpdateResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/version", response_model=AddVersionResponse)
async def add_version(
    req: AddVersionRequest,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> AddVersionResponse:
    """Add a new version if it doesn't already exist for the same channel."""
    result = await db.execute(
        select(Version).where(
            Version.version == req.version,
            Version.channel == req.channel,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version '{req.version}' already exists in channel '{req.channel}'",
        )

    v = Version(
        version=req.version,
        url=req.url,
        checksum=req.checksum,
        channel=req.channel,
        active=int(req.active),
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    return AddVersionResponse(status="ok", version=str(v.version), channel=str(v.channel))


@router.get("/version", response_model=list[UpdateResponse])
async def get_versions(
    channel: str | None = None,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> list[UpdateResponse]:
    """Return all versions, optionally filtered by channel."""
    query = select(Version).order_by(desc(Version.created_at))
    if channel:
        query = query.where(Version.channel == channel)

    result = await db.execute(query)
    versions = result.scalars().all()

    return [
        UpdateResponse(
            version=str(v.version),
            url=str(v.url),
            checksum=str(v.checksum),
        )
        for v in versions
    ]


@router.patch("/version/{version}", response_model=AddVersionResponse)
async def update_version_status(
    version: str,
    req: AddVersionRequest,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> AddVersionResponse:
    """Update existing version parameters manually."""
    result = await db.execute(select(Version).where(Version.version == version))
    v = result.scalar_one_or_none()

    if v is None:
        raise HTTPException(status_code=404, detail=f"Version '{version}' not found")

    v.url = req.url
    v.checksum = req.checksum
    v.channel = req.channel
    v.active = int(req.active)
    await db.commit()
    await db.refresh(v)

    return AddVersionResponse(status="ok", version=str(v.version), channel=str(v.channel))


@router.delete("/version/{version}", response_model=AddVersionResponse)
async def delete_version(
    version: str,
    db: AsyncSession = Depends(get_session),
    _: str = Depends(verify_admin),
) -> AddVersionResponse:
    """Delete version record."""
    result = await db.execute(select(Version).where(Version.version == version))
    v = result.scalar_one_or_none()

    if v is None:
        raise HTTPException(status_code=404, detail=f"Version '{version}' not found")

    await db.delete(v)
    await db.commit()

    return AddVersionResponse(status="deleted", version=str(v.version), channel=str(v.channel))
