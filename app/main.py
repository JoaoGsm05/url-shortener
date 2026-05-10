import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.router import router
from app.core import metrics

app = FastAPI(title="URL Shortener", version="0.1.0")

_PATHS_FIXOS = frozenset({"/health", "/metrics", "/shorten", "/docs", "/redoc", "/openapi.json"})


def _normalizar_path(path: str) -> str:
    if path in _PATHS_FIXOS:
        return path
    if path.startswith("/stats/"):
        return "/stats/{slug}"
    return "/{slug}"


@app.middleware("http")
async def track_http_metrics(request: Request, call_next: object) -> Response:
    path = _normalizar_path(request.url.path)
    inicio = time.perf_counter()
    response = await call_next(request)
    duracao = time.perf_counter() - inicio
    metrics.http_request_duration.labels(request.method, path).observe(duracao)
    metrics.http_requests.labels(request.method, path, response.status_code).inc()
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# router incluído após /health e /metrics para que /{slug} não intercepte rotas fixas
app.include_router(router)
