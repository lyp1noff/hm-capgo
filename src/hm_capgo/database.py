from collections.abc import AsyncGenerator

from fastapi.logger import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import SQLALCHEMY_DATABASE_URL

# pre_ping: after a database restart the pool would hand out dead connections and the next request fails with 500.
engine: AsyncEngine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"Session {id(db)} error: {e}")
            await db.rollback()
            raise
        finally:
            if db.in_transaction():
                await db.rollback()
            logger.debug(f"Session {id(db)} closed")
