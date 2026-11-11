from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Device

PRODUCTION = "production"
TEST = "test"
CHANNELS = (PRODUCTION, TEST)


def install_channel(is_prod: Optional[bool]) -> str:
    """The channel of the install itself: TestFlight and development builds report is_prod false."""
    return TEST if is_prod is False else PRODUCTION


def device_channel(device: Device) -> str:
    return str(device.channel) if device.channel else install_channel(device_is_prod(device))


def device_is_prod(device: Device) -> Optional[bool]:
    return None if device.is_prod is None else bool(device.is_prod)


async def touch_device(
    db: AsyncSession,
    device_id: str,
    app_id: str,
    is_prod: Optional[bool] = None,
    version_build: Optional[str] = None,
    version_name: Optional[str] = None,
) -> Device:
    """Find or create the device and remember what it reported last."""
    device = await db.scalar(select(Device).where(Device.device_id == device_id, Device.app_id == app_id))

    if device is None:
        device = Device(device_id=device_id, app_id=app_id)
        db.add(device)

    if is_prod is not None:
        device.is_prod = int(is_prod)
    if version_build is not None:
        device.version_build = version_build
    if version_name is not None:
        device.version_name = version_name
    device.last_seen = func.now()

    await db.commit()
    await db.refresh(device)
    return device
