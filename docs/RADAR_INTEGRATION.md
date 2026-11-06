# Leiloar.com Radar Integration Guide

This guide describes how the frontend at **[leiloar.com/radar-leiloes](https://leiloar.com/radar-leiloes)** consumes the API and data contracts produced by this framework.

---

## 1. Primary Endpoints

### 1.1 Faceted Lot Search
**Endpoint:** `GET /api/v1/radar/lots`

Query Parameters:
- `q`: Free text query matching titles, descriptions, and city names.
- `state`: 2-letter state code (`SP`, `RJ`, `MG`, `PR`, etc.).
- `city`: Substring city filter (e.g. `São Paulo`, `Campinas`).
- `category`: Asset category (`imovel_apartamento`, `imovel_casa`, `imovel_terreno`, `imovel_comercial`).
- `min_discount`: Minimum discount threshold percentage (e.g. `50`).
- `max_price`: Price ceiling in BRL.
- `min_score`: Filter by minimum DealScore (0 - 100).
- `source_type`: `judicial` or `extrajudicial_bank`.
- `page` / `limit`: Pagination controls.

**Example Response:**
```json
{
  "items": [
    {
      "lot_id": "caixa_8444401234567",
      "title": "Apartamento - Mooca, São Paulo/SP",
      "category": "imovel_apartamento",
      "source_type": "extrajudicial_bank",
      "status": "open",
      "appraisal_value": 480000.0,
      "minimum_bid": 264000.0,
      "current_discount_pct": 45.0,
      "occupied": 1,
      "city": "São Paulo",
      "state": "SP",
      "url": "https://venda-imoveis.caixa.gov.br/...",
      "auctioneer_name": "Caixa Econômica Federal",
      "opportunity_score": 82.5,
      "risk_rating": "B_LOW",
      "liquidity_tier": "muito_alta",
      "estimated_net_margin_pct": 36.5,
      "recommended_action": "BID",
      "summary": "Excelente oportunidade (Score 82.5/100) com desconto de 45.0%...",
      "tags": ["40%+ Desconto", "Aceita Financiamento", "Aceita FGTS", "Radar Destaque"]
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

---

### 1.2 Featured Opportunities
**Endpoint:** `GET /api/v1/radar/featured?limit=6`

Returns top-scoring deals (DealScore >= 75) for rendering in the hero carousel and high-yield deal section on `leiloar.com/radar-leiloes`.

---

### 1.3 Market Statistics
**Endpoint:** `GET /api/v1/radar/stats`

Returns platform counters:
- `total_active_lots`
- `average_discount_pct`
- `total_appraisal_volume_brl`
- `total_bid_volume_brl`
- `judicial_lots` vs `bank_lots`
- `vacant_lots` count
- `top_states` breakdown

---

## 2. Frontend Deal Badges & Color Semantics

| DealScore Range | Badge Text | Recommended Color |
|:---:|:---:|:---:|
| **85 - 100** | Radar Ouro | Emerald / Gold |
| **70 - 84** | Radar Destaque | Blue / Indigo |
| **50 - 69** | Oportunidade Moderada | Amber / Yellow |
| **< 50** | Alto Risco | Slate / Red |
