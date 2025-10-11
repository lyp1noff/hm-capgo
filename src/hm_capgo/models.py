from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)
    url = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    channel = Column(String, default="production")
    active = Column(Integer, default=1)  # bool, но можно хранить int(0/1)
    created_at = Column(DateTime, server_default=func.now())


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False)
    app_id = Column(String, nullable=False)
    channel = Column(String, default="production")
    last_seen = Column(DateTime, server_default=func.now())


class Stat(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, server_default=func.now())
    action = Column(String, nullable=False)
    app_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    custom_id = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    version_name = Column(String, nullable=True)
    version_build = Column(String, nullable=True)
    version_code = Column(String, nullable=True)
    version_os = Column(String, nullable=True)
