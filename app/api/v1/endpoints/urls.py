import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache, metrics
from app.core.config import settings
from app.db.session import get_db
from app.schemas.url import StatsResponse, UrlCreate, UrlResponse
from app.services import url_service

router = APIRouter()


@router.post("/shorten", response_model=UrlResponse, status_code=201)
async def encurtar_url(payload: UrlCreate, db: AsyncSession = Depends(get_db)) -> UrlResponse:
    url = await url_service.criar_url(db, str(payload.original_url), payload.expires_at)
    metrics.urls_criadas.inc()
    return UrlResponse(
        slug=url.slug,
        short_url=f"{settings.base_url}/{url.slug}",
        original_url=url.original_url,
        total_clicks=url.total_clicks,
        created_at=url.created_at,
        expires_at=url.expires_at,
    )


@router.get("/stats/{slug}", response_model=StatsResponse)
async def stats_url(slug: str, db: AsyncSession = Depends(get_db)) -> StatsResponse:
    url = await url_service.buscar_por_slug(db, slug)
    if not url:
        raise HTTPException(status_code=404, detail="URL não encontrada")
    last_click, top_user_agents = await url_service.buscar_stats(db, url.id)
    return StatsResponse(
        slug=url.slug,
        original_url=url.original_url,
        total_clicks=url.total_clicks,
        last_click=last_click,
        top_user_agents=top_user_agents,
    )


@router.get("/{slug}")
async def redirecionar(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    ip_raw = request.client.host if request.client else None
    ip_hash = hashlib.sha256(ip_raw.encode()).hexdigest()[:16] if ip_raw else None
    user_agent = request.headers.get("user-agent")

    # Cache hit → redireciona sem consultar o banco
    cached = await cache.get_redirect_cache(slug)
    if cached:
        original_url, url_id = cached
        metrics.redirects.labels(cache="hit").inc()
        background_tasks.add_task(url_service.registrar_clique_bg, url_id, user_agent, ip_hash)
        return RedirectResponse(url=original_url, status_code=302)

    # Cache miss → consulta banco e popula cache
    url = await url_service.buscar_por_slug(db, slug)
    if not url:
        metrics.redirect_errors.labels(reason="not_found").inc()
        raise HTTPException(status_code=404, detail="URL não encontrada")
    if url_service.url_expirada(url):
        metrics.redirect_errors.labels(reason="expired").inc()
        raise HTTPException(status_code=410, detail="URL expirada")

    ttl = url_service.calcular_cache_ttl(url)
    await cache.set_redirect_cache(slug, url.original_url, url.id, ttl)

    metrics.redirects.labels(cache="miss").inc()
    background_tasks.add_task(url_service.registrar_clique_bg, url.id, user_agent, ip_hash)
    return RedirectResponse(url=url.original_url, status_code=302)
