import os

# Define antes de qualquer import do app para que Settings() leia este valor
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app

_ASYNC_URL = "sqlite+aiosqlite:///./test.db"
_SYNC_URL = "sqlite:///./test.db"

_async_engine = create_async_engine(_ASYNC_URL)
_session_factory = async_sessionmaker(_async_engine, expire_on_commit=False, class_=AsyncSession)
_sync_engine = create_engine(_SYNC_URL)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    Base.metadata.create_all(_sync_engine)
    yield
    Base.metadata.drop_all(_sync_engine)
    _sync_engine.dispose()


@pytest.fixture(autouse=True)
async def limpar_tabelas() -> None:
    yield
    # clicks primeiro por causa da FK
    async with _async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM clicks"))
        await conn.execute(text("DELETE FROM urls"))


@pytest.fixture
async def client() -> AsyncClient:
    async def override_get_db() -> AsyncSession:
        async with _session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
