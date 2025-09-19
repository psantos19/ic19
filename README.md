# IC19 — Melhor Hora para Sair (MVP)

App que recomenda horas de saída personalizadas para evitar o pico no IC-19, mantendo a procura por intervalo de 5 minutos abaixo do limiar de saturação (capacidade).

## Stack

- **Frontend**: React Native (Expo)
- **Backend**: FastAPI (Python)
- **DB**: Postgres
- **Cache/locks**: Redis
- **Orquestração local**: Docker Compose

## Como correr localmente

```bash
cd infra
cp .env.example .env
docker compose up -d --build

# (Opcional) Semear dados sintéticos e recomendações
docker compose exec backend python -m app.seeds

# Testar API
curl http://localhost:8000/health
```