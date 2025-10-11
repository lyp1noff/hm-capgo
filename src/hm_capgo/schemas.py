from typing import Optional

from pydantic import BaseModel


class AddVersionRequest(BaseModel):
    version: str
    url: str
    checksum: str
    channel: str = "production"
    active: bool = True


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


class UpdateResponse(BaseModel):
    version: str
    url: str
    checksum: str


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


class ChannelResponse(BaseModel):
    status: str
    channel: Optional[str] = None
    allowSet: Optional[bool] = True
    message: Optional[str] = None
    error: Optional[str] = None
