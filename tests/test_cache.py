from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

_URL = "https://exemplo.com/"


async def test_cache_hit_redireciona_sem_consultar_db(client: AsyncClient) -> None:
    """Com cache hit, o redirect acontece sem consultar o banco."""
    with (
        patch("app.core.cache.get_redirect_cache", new_callable=AsyncMock, return_value=(_URL, 1)),
        patch("app.services.url_service.registrar_clique_bg", new_callable=AsyncMock),
        patch("app.services.url_service.buscar_por_slug", new_callable=AsyncMock) as mock_db,
    ):
        resp = await client.get("/qualquerslug", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == _URL
    mock_db.assert_not_called()


async def test_cache_miss_redis_indisponivel_usa_banco(client: AsyncClient) -> None:
    """Com Redis indisponível (retorna None), o redirect usa o banco normalmente."""
    resp_criar = await client.post("/shorten", json={"original_url": _URL})
    slug = resp_criar.json()["slug"]

    with patch("app.core.cache.get_redirect_cache", new_callable=AsyncMock, return_value=None):
        resp = await client.get(f"/{slug}", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == _URL


async def test_cache_ttl_zero_para_url_ja_expirada() -> None:
    """calcular_cache_ttl retorna 0 para URLs já expiradas (não devem ser cacheadas)."""
    from datetime import datetime, timedelta, timezone

    from app.models.url import Url
    from app.services.url_service import calcular_cache_ttl

    url_expirada = Url(
        id=1,
        slug="abc1234",
        original_url=_URL,
        total_clicks=0,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    assert calcular_cache_ttl(url_expirada) == 0


async def test_cache_ttl_default_para_url_sem_expiracao() -> None:
    """calcular_cache_ttl retorna o default (3600) para URLs sem expiração."""
    from app.models.url import Url
    from app.services.url_service import calcular_cache_ttl

    url_sem_expiracao = Url(id=1, slug="abc1234", original_url=_URL, total_clicks=0, expires_at=None)
    assert calcular_cache_ttl(url_sem_expiracao) == 3600
