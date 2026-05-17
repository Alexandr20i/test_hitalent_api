from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.is_test,   # SQL-лог только в тестах
    pool_pre_ping=True,       # проверяет соединение перед использованием
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # объекты остаются живыми после commit
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — открывает сессию на запрос,
    коммитит при успехе, откатывает при исключении.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise