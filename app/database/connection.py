from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.logging import logger


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""

    pass


settings = get_settings()

db_url = settings.async_database_url

# Configure engine parameters based on database dialect
engine_kwargs = {"echo": False, "future": True}
if db_url.startswith("postgresql"):
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database tables initialized successfully on [{db_url.split('://')[0]}].")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {str(e)}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
