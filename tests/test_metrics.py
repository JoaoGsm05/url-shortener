import re

from httpx import AsyncClient

_URL = "https://exemplo.com/"


def _ler_contador(texto: str, nome: str) -> float:
    """Extrai o valor de uma métrica pelo nome exato (com labels opcionais)."""
    padrao = rf'^{re.escape(nome)}\s+([\d.e+]+)'
    match = re.search(padrao, texto, re.MULTILINE)
    return float(match.group(1)) if match else 0.0


async def test_metrics_endpoint_retorna_200(client: AsyncClient) -> None:
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]


async def test_metrics_contem_nomes_esperados(client: AsyncClient) -> None:
    resp = await client.get("/metrics")
    corpo = resp.text
    assert "url_shortener_urls_created_total" in corpo
    assert "url_shortener_redirects_total" in corpo
    assert "url_shortener_redirect_errors_total" in corpo
    assert "url_shortener_http_requests_total" in corpo
    assert "url_shortener_http_request_duration_seconds" in corpo


async def test_metrics_incrementa_urls_criadas(client: AsyncClient) -> None:
    antes = _ler_contador((await client.get("/metrics")).text, "url_shortener_urls_created_total")

    await client.post("/shorten", json={"original_url": _URL})

    depois = _ler_contador((await client.get("/metrics")).text, "url_shortener_urls_created_total")
    assert depois == antes + 1


async def test_metrics_incrementa_redirect_cache_miss(client: AsyncClient) -> None:
    resp = await client.post("/shorten", json={"original_url": _URL})
    slug = resp.json()["slug"]

    nome = 'url_shortener_redirects_total{cache="miss"}'
    antes = _ler_contador((await client.get("/metrics")).text, nome)

    await client.get(f"/{slug}", follow_redirects=False)

    depois = _ler_contador((await client.get("/metrics")).text, nome)
    assert depois == antes + 1


async def test_metrics_incrementa_erro_not_found(client: AsyncClient) -> None:
    nome = 'url_shortener_redirect_errors_total{reason="not_found"}'
    antes = _ler_contador((await client.get("/metrics")).text, nome)

    await client.get("/aaaaaaa", follow_redirects=False)

    depois = _ler_contador((await client.get("/metrics")).text, nome)
    assert depois == antes + 1


async def test_metrics_http_requests_registra_latencia(client: AsyncClient) -> None:
    await client.get("/health")
    corpo = (await client.get("/metrics")).text
    # Verifica que o bucket do histogram foi populado
    assert 'url_shortener_http_request_duration_seconds_bucket{le="0.1",method="GET",path="/health"}' in corpo
