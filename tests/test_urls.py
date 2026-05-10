from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

_URL = "https://exemplo.com/"  # Pydantic HttpUrl normaliza adicionando barra final


async def _criar_url(client: AsyncClient, url: str = _URL, **kwargs: object) -> dict:
    payload = {"original_url": url, **kwargs}
    resp = await client.post("/shorten", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def test_criar_url_retorna_slug_e_campos(client: AsyncClient) -> None:
    data = await _criar_url(client)

    assert len(data["slug"]) == 7
    assert data["short_url"] == f"http://localhost:8000/{data['slug']}"
    assert data["original_url"] == _URL
    assert data["total_clicks"] == 0
    assert data["expires_at"] is None


async def test_redirecionar_retorna_302(client: AsyncClient) -> None:
    data = await _criar_url(client)
    resp = await client.get(f"/{data['slug']}", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == _URL


async def test_redirecionar_slug_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get("/aaaaaaa", follow_redirects=False)
    assert resp.status_code == 404


async def test_redirecionar_url_expirada_retorna_410(client: AsyncClient) -> None:
    expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    data = await _criar_url(client, expires_at=expires)

    resp = await client.get(f"/{data['slug']}", follow_redirects=False)
    assert resp.status_code == 410


async def test_stats_retorna_campos_iniciais(client: AsyncClient) -> None:
    data = await _criar_url(client)
    resp = await client.get(f"/stats/{data['slug']}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == data["slug"]
    assert body["original_url"] == _URL
    assert body["total_clicks"] == 0
    assert body["last_click"] is None
    assert body["top_user_agents"] == []


async def test_stats_slug_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get("/stats/aaaaaaa")
    assert resp.status_code == 404


async def test_clique_incrementa_total_e_registra_last_click(client: AsyncClient) -> None:
    data = await _criar_url(client)

    await client.get(f"/{data['slug']}", follow_redirects=False)

    resp = await client.get(f"/stats/{data['slug']}")
    body = resp.json()

    assert body["total_clicks"] == 1
    assert body["last_click"] is not None
