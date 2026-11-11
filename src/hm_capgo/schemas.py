from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AddVersionRequest(BaseModel):
    version: str
    url: str
    checksum: str
    native: str
    channel: str = "production"
    active: bool = True


class PatchVersionRequest(BaseModel):
    url: Optional[str] = None
    checksum: Optional[str] = None
    native: Optional[str] = None
    active: Optional[bool] = None


class VersionInfo(BaseModel):
    version: str
    url: str
    checksum: str
    native: Optional[str] = None
    channel: Optional[str] = None
    active: bool
    created_at: Optional[datetime] = None


class DeviceInfo(BaseModel):
    device_id: str
    app_id: str
    channel: str
    channel_override: bool
    is_prod: Optional[bool] = None
    version_build: Optional[str] = None
    version_name: Optional[str] = None
    last_seen: Optional[datetime] = None


class AddVersionResponse(BaseModel):
    status: str
    version: str
    channel: str


class UpdateRequest(BaseModel):
    app_id: str
    device_id: str
    platform: Optional[str] = None
    version_name: Optional[str] = None
    version_build: Optional[str] = None
    plugin_version: Optional[str] = None
    is_prod: Optional[bool] = None


class UpdateResponse(BaseModel):
    version: Optional[str] = None
    url: Optional[str] = None
    checksum: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class CapgoStats(BaseModel):
    action: str
    app_id: str
    device_id: str
    custom_id: Optional[str] = None
    platform: Optional[str] = None
    version_name: Optional[str] = None
    version_build: Optional[str] = None
    version_code: Optional[str] = None
    version_os: Optional[str] = None


class ChannelRequest(BaseModel):
    device_id: str
    app_id: str
    channel: Optional[str] = None
    is_prod: Optional[bool] = None
    version_build: Optional[str] = None
    version_name: Optional[str] = None


class ChannelResponse(BaseModel):
    status: str
    channel: Optional[str] = None
    allowSet: Optional[bool] = True
    message: Optional[str] = None
    error: Optional[str] = None
