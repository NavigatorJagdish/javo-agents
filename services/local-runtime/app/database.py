"""SQLAlchemy async database setup for SQLite."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def _get_engine():
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    if "sqlite" in settings.database_url:
        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.close()
    return engine


engine = None
async_session_factory = None


def init_engine():
    """Initialize the engine and session factory."""
    global engine, async_session_factory
    engine = _get_engine()
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    if async_session_factory is None:
        init_engine()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    """Create all tables in the database."""
    if engine is None:
        init_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close the database engine."""
    global engine, async_session_factory
    if engine:
        await engine.dispose()
        engine = None
        async_session_factory = None
