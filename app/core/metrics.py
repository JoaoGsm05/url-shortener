from prometheus_client import Counter, Histogram

urls_criadas = Counter(
    "url_shortener_urls_created",
    "Total de URLs encurtadas criadas",
)

redirects = Counter(
    "url_shortener_redirects",
    "Total de redirects realizados com sucesso",
    ["cache"],  # "hit" | "miss"
)

redirect_errors = Counter(
    "url_shortener_redirect_errors",
    "Total de erros ao redirecionar",
    ["reason"],  # "not_found" | "expired"
)

http_requests = Counter(
    "url_shortener_http_requests",
    "Total de requisições HTTP recebidas",
    ["method", "path", "status"],
)

http_request_duration = Histogram(
    "url_shortener_http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)
