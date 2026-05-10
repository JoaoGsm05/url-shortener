# URL Shortener

> Encurtador de URLs com analytics completo e observabilidade em tempo real.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-red?style=flat-square&logo=redis)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## Sobre o Projeto

Servico de encurtamento de URLs construido com **FastAPI**, focado em performance e observabilidade. Conta com rastreamento de cliques em tempo real, metricas expostas via **Prometheus**, dashboards no **Grafana** e cache com **Redis** para respostas sub-milissegundo.

Deploy disponivel no **Render**.

## Funcionalidades

- Encurtamento de URLs com slug customizavel ou gerado automaticamente
- Analytics por URL: total de cliques, cliques unicos, referencia e user-agent
- Cache com Redis (TTL configuravel)
- Autenticacao JWT para gerenciamento de URLs privadas
- Metricas expostas via /metrics (Prometheus)
- Dashboard pre-configurado no Grafana
- Ambiente completo via Docker Compose
- Migrations automaticas com Alembic
- Testes automatizados com Pytest

## Tecnologias

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn |
| Banco de dados | PostgreSQL 15 |
| Cache | Redis 7 |
| Observabilidade | Prometheus + Grafana |
| Containerizacao | Docker + Docker Compose |
| Migrations | Alembic |
| Deploy | Render |

## Como Rodar Localmente

### Pre-requisitos

- Docker e Docker Compose instalados

### 1. Clone o repositorio

```bash
git clone https://github.com/JoaoGsm05/url-shortener.git
cd url-shortener
```

### 2. Configure as variaveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas configuracoes
```

### 3. Suba os containers

```bash
docker-compose up -d
```

### 4. Acesse

| Servico | URL |
|---|---|
| API | http://localhost:8000 |
| Docs (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

## Estrutura do Projeto

```
url-shortener/
├── app/
│   ├── api/          # Rotas e endpoints
│   ├── core/         # Configuracoes e seguranca
│   ├── models/       # Modelos do banco de dados
│   ├── schemas/      # Schemas Pydantic
│   └── services/     # Logica de negocio
├── docker/           # Configs Docker (Grafana, Prometheus)
├── migrations/       # Migrations Alembic
├── scripts/          # Scripts utilitarios
├── tests/            # Testes automatizados
├── docker-compose.yml
└── render.yaml       # Configuracao de deploy
```

## Rodando os Testes

```bash
docker-compose exec api pytest tests/ -v
```

## Observabilidade

O projeto expoe metricas no padrao OpenMetrics via `/metrics`. O Grafana inclui um dashboard pre-configurado com:

- Requisicoes por segundo
- Latencia media por endpoint
- Taxa de erros
- Uso de cache (hit/miss ratio)

## Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Desenvolvido por [Joao Gabriel](https://github.com/JoaoGsm05) - [LinkedIn](https://linkedin.com/in/joaogsm05)
