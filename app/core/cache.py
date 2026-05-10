import json

import redis.asyncio as aioredis

from app.core.config import settings

_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client


async def _cache_get(key: str) -> str | None:
    try:
        result = await _get_client().get(key)
        return str(result) if result is not None else None
    except Exception:
        return None


async def _cache_set(key: str, value: str, ex: int) -> None:
    try:
        await _get_client().set(key, value, ex=ex)
    except Exception:
        pass


async def _cache_delete(key: str) -> None:
    try:
        await _get_client().delete(key)
    except Exception:
        pass


async def get_redirect_cache(slug: str) -> tuple[str, int] | None:
    """Retorna (original_url, url_id) do cache ou None se não encontrado/Redis indisponível."""
    raw = await _cache_get(f"slug:{slug}")
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return data["original_url"], data["url_id"]
    except Exception:
        return None


async def set_redirect_cache(slug: str, original_url: str, url_id: int, ttl: int) -> None:
    if ttl <= 0:
        return
    value = json.dumps({"original_url": original_url, "url_id": url_id})
    await _cache_set(f"slug:{slug}", value, ex=ttl)


async def delete_redirect_cache(slug: str) -> None:
    await _cache_delete(f"slug:{slug}")
