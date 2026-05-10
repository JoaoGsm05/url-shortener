from datetime import datetime, timezone

from nanoid import generate
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.click import Click
from app.models.url import Url


async def criar_url(db: AsyncSession, original_url: str, expires_at: datetime | None = None) -> Url:
    slug = generate(size=settings.slug_length)
    url = Url(original_url=original_url, slug=slug, expires_at=expires_at)
    db.add(url)
    await db.commit()
    await db.refresh(url)
    return url


async def buscar_por_slug(db: AsyncSession, slug: str) -> Url | None:
    resultado = await db.execute(select(Url).where(Url.slug == slug))
    return resultado.scalar_one_or_none()


async def registrar_clique_bg(url_id: int, user_agent: str | None, ip_hash: str | None) -> None:
    # Sessão própria para evitar uso de sessão já fechada pelo request
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        click = Click(url_id=url_id, user_agent=user_agent, ip_hash=ip_hash)
        db.add(click)
        await db.execute(
            update(Url).where(Url.id == url_id).values(total_clicks=Url.total_clicks + 1)
        )
        await db.commit()


def calcular_cache_ttl(url: Url, default: int = 3600) -> int:
    """TTL em segundos: usa o tempo restante até expiração ou o default para URLs sem expiração."""
    if url.expires_at is None:
        return default
    restante = (url.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(restante))


def url_expirada(url: Url) -> bool:
    if url.expires_at is None:
        return False
    return datetime.now(timezone.utc) > url.expires_at.replace(tzinfo=timezone.utc)


async def buscar_stats(db: AsyncSession, url_id: int) -> tuple[datetime | None, list[str]]:
    result_last = await db.execute(
        select(func.max(Click.clicked_at)).where(Click.url_id == url_id)
    )
    last_click: datetime | None = result_last.scalar_one_or_none()

    result_ua = await db.execute(
        select(Click.user_agent, func.count(Click.id).label("cnt"))
        .where(Click.url_id == url_id)
        .where(Click.user_agent.isnot(None))
        .group_by(Click.user_agent)
        .order_by(func.count(Click.id).desc())
        .limit(5)
    )
    top_user_agents: list[str] = [row.user_agent for row in result_ua.all() if row.user_agent]

    return last_click, top_user_agents
