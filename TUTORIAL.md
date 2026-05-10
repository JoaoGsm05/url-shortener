# Tutorial — URL Shortener

Passo a passo completo: do clone ao app rodando em produção no Render.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Rodando com Docker (recomendado)](#2-rodando-com-docker-recomendado)
3. [Usando a API](#3-usando-a-api)
4. [Monitorando com Grafana](#4-monitorando-com-grafana)
5. [Rodando sem Docker (desenvolvimento)](#5-rodando-sem-docker-desenvolvimento)
6. [Rodando os testes](#6-rodando-os-testes)
7. [Deploy no Render](#7-deploy-no-render)
8. [Backup e restore do banco](#8-backup-e-restore-do-banco)

---

## 1. Pré-requisitos

| Ferramenta | Versão mínima | Como verificar |
|---|---|---|
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| Python (opcional, sem Docker) | 3.12+ | `python --version` |
| uv (opcional, sem Docker) | 0.5+ | `uv --version` |

---

## 2. Rodando com Docker (recomendado)

### 2.1 Clone e suba o stack

```bash
git clone https://github.com/JoaoGsm05/url-shortener.git
cd url-shortener
docker compose up --build
```

> Na primeira vez, o Docker baixa as imagens e instala as dependências (~2-3 min).
> Nas próximas, usa o cache (~20s).

### 2.2 Verifique que tudo subiu

```
✓ db         → PostgreSQL 16 rodando na porta 5432 (interno)
✓ redis      → Redis 7 rodando na porta 6379 (interno)
✓ app        → FastAPI em http://localhost:8000
✓ prometheus → http://localhost:9090
✓ grafana    → http://localhost:3000
```

Teste rápido:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### 2.3 Parando o stack

```bash
# Para os containers (mantém os volumes/dados):
docker compose stop

# Para e remove containers + volumes (reset completo):
docker compose down -v
```

---

## 3. Usando a API

A documentação interativa completa está em **http://localhost:8000/docs** (Swagger UI).

### 3.1 Encurtar uma URL

```bash
curl -s -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com/JoaoGsm05/url-shortener"}' \
  | python -m json.tool
```

Resposta:

```json
{
  "slug": "k3Xp9mQ",
  "short_url": "http://localhost:8000/k3Xp9mQ",
  "original_url": "https://github.com/JoaoGsm05/url-shortener",
  "total_clicks": 0,
  "created_at": "2026-05-10T03:00:00Z",
  "expires_at": null
}
```

### 3.2 Encurtar com data de expiração

```bash
curl -s -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://exemplo.com/promo",
    "expires_at": "2026-12-31T23:59:59Z"
  }' | python -m json.tool
```

### 3.3 Redirecionar (acessar a URL curta)

```bash
# -L segue o redirect automaticamente
curl -L http://localhost:8000/k3Xp9mQ

# Para ver apenas o status e o Location header (sem seguir):
curl -I http://localhost:8000/k3Xp9mQ
# HTTP/1.1 302 Found
# location: https://github.com/JoaoGsm05/url-shortener
```

### 3.4 Ver analytics do slug

```bash
curl -s http://localhost:8000/stats/k3Xp9mQ | python -m json.tool
```

Resposta:

```json
{
  "slug": "k3Xp9mQ",
  "original_url": "https://github.com/JoaoGsm05/url-shortener",
  "total_clicks": 3,
  "last_click": "2026-05-10T03:05:00Z",
  "top_user_agents": [
    "curl/8.4.0",
    "Mozilla/5.0 ..."
  ]
}
```

### 3.5 Erros esperados

```bash
# Slug não existe → 404
curl -I http://localhost:8000/aaaaaaa
# HTTP/1.1 404 Not Found

# URL expirada → 410
curl -I http://localhost:8000/<slug-expirado>
# HTTP/1.1 410 Gone
```

### 3.6 Ver métricas brutas (Prometheus)

```bash
curl http://localhost:8000/metrics | grep url_shortener
```

---

## 4. Monitorando com Grafana

### 4.1 Acessar o Grafana

1. Abra **http://localhost:3000**
2. Login: `admin` / `admin`
3. O dashboard **URL Shortener** abre automaticamente

### 4.2 Painéis disponíveis

| Painel | Métrica | Descrição |
|---|---|---|
| URLs Criadas / min | `url_shortener_urls_created_total` | Taxa de criação de slugs |
| Redirects / min | `url_shortener_redirects_total` | Hit vs miss no cache Redis |
| Latência HTTP (p50/p95) | `url_shortener_http_request_duration_seconds` | Histograma por endpoint |
| Erros de Redirect / min | `url_shortener_redirect_errors_total` | not_found vs expired |
| Requisições por Status | `url_shortener_http_requests_total` | Volume por status code |

### 4.3 Gerar carga para ver os painéis

```bash
# Cria 10 URLs e faz 50 acessos para gerar dados
SLUG=$(curl -s -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://exemplo.com"}' | python -c "import sys,json; print(json.load(sys.stdin)['slug'])")

for i in $(seq 1 50); do
  curl -s -o /dev/null http://localhost:8000/$SLUG
done

echo "Acesse http://localhost:3000 para ver os dados"
```

---

## 5. Rodando sem Docker (desenvolvimento)

### 5.1 Configure o ambiente

```bash
# Instale o uv se não tiver
pip install uv

# Clone e entre no diretório
git clone https://github.com/JoaoGsm05/url-shortener.git
cd url-shortener

# Instale as dependências
uv sync
```

### 5.2 Configure o banco

Você precisará de um PostgreSQL local. Com Docker só para o banco:

```bash
docker run -d \
  --name url-shortener-db \
  -e POSTGRES_USER=urlshortener \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=urlshortener \
  -p 5432:5432 \
  postgres:16-alpine
```

### 5.3 Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com o DATABASE_URL correto:
# DATABASE_URL=postgresql+asyncpg://urlshortener:devpassword@localhost:5432/urlshortener
```

### 5.4 Rode as migrations e suba o servidor

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

O servidor sobe em **http://localhost:8000** com hot-reload ativo.

---

## 6. Rodando os testes

Os testes usam SQLite em memória — **não precisam de Postgres nem Redis**.

```bash
# Apenas testes
uv run pytest -v

# Com cobertura
uv run pytest --cov=app --cov-report=term-missing

# Um arquivo específico
uv run pytest tests/test_urls.py -v
```

Saída esperada:

```
17 passed in ~15s
Coverage: 85%
```

---

## 7. Deploy no Render

### 7.1 Criar conta no Render

Acesse **https://render.com** e crie uma conta gratuita (não precisa de cartão).

### 7.2 Conectar o repositório

1. No dashboard do Render, clique em **New → Blueprint**
2. Conecte sua conta GitHub se não estiver conectada
3. Selecione o repositório `url-shortener`
4. Clique em **Apply**

O Render lê o `render.yaml` e cria automaticamente:
- Web Service (FastAPI)
- PostgreSQL free

### 7.3 Aguardar o primeiro deploy

O primeiro build leva ~3-5 minutos (instala dependências, roda migrations, sobe o servidor).

Acompanhe em: **Dashboard → url-shortener → Logs**

### 7.4 Configurar BASE_URL

Após o deploy, copie a URL pública gerada (ex: `https://url-shortener-xxxx.onrender.com`) e configure:

1. **Dashboard → url-shortener → Environment**
2. Adicione: `BASE_URL = https://url-shortener-xxxx.onrender.com`
3. Clique em **Save Changes** (o Render fará um redeploy automático)

### 7.5 Testar em produção

```bash
# Substitua pela sua URL real
BASE="https://url-shortener-xxxx.onrender.com"

curl -s -X POST $BASE/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com/JoaoGsm05"}' \
  | python -m json.tool
```

> **Atenção:** O free tier dorme após 15 minutos sem requisições.
> O primeiro acesso após o sleep leva ~30 segundos (cold start).

### 7.6 CI/CD automático

A partir de agora, todo push em `main` dispara automaticamente:

```
lint (ruff + mypy) → testes (pytest) → build Docker → push GHCR → Render redeploya
```

---

## 8. Backup e restore do banco

O PostgreSQL free do Render **expira em 90 dias**. Faça backup antes disso.

### 8.1 Backup

```bash
# Copie a DATABASE_URL do painel do Render (Environment → DATABASE_URL)
export DATABASE_URL="postgresql://urlshortener:senha@host.render.com:5432/urlshortener"

./scripts/backup_db.sh
# Cria: backups/backup_20260510_120000.sql
```

### 8.2 Restore

```bash
# Após criar um novo banco no Render
export DATABASE_URL="postgresql://urlshortener:nova-senha@novo-host.render.com:5432/urlshortener"

./scripts/restore_db.sh backups/backup_20260510_120000.sql
# Pede confirmação antes de sobrescrever
```

### 8.3 Lembrete dos 90 dias

Anote a data de criação do banco e faça backup com ~1 semana de antecedência.

---

## Resumo rápido

```bash
# Subir local
docker compose up --build

# Criar URL
curl -X POST localhost:8000/shorten -H "Content-Type: application/json" \
  -d '{"original_url": "https://exemplo.com"}'

# Acessar
curl -L localhost:8000/<slug>

# Ver stats
curl localhost:8000/stats/<slug>

# Testes
uv run pytest -v

# Lint
uv run ruff check . && uv run ruff format --check . && uv run mypy app/
```
