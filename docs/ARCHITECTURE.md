# Architecture & System Design

The **Leiloar.com SaaS Auction Framework** is engineered as a modular, event-driven data pipeline designed to ingest, normalize, analyze, and index thousands of auction events daily from Brazilian judicial and extrajudicial sources.

---

## 1. High-Level System Architecture

```text
       ┌────────────────────────┐         ┌────────────────────────┐
       │   Bank Repossessions   │         │  Judicial Auctioneers  │
       │ (Caixa, BB, Santander) │         │ (Zukerman, Mega, etc.) │
       └───────────┬────────────┘         └───────────┬────────────┘
                   │                                  │
                   └─────────────────┬────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │       BaseScraper Framework       │
                   │  - Rate Limiting / Exponential    │
                   │  - User-Agent & Header Rotation   │
                   │  - Proxy Support & Backoff        │
                   └─────────────────┬─────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │      Domain Ingestion Models      │
                   │  - AuctionLot                     │
                   │  - RealEstateAsset / VehicleAsset │
                   │  - LegalProcess / Auctioneer      │
                   └─────────────────┬─────────────────┘
                                     ▼
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     Legal & CNJ Parsers      │              │  Edital Regex & NLP Extractor│
│ - ISO 7064 Modulo 97-10      │              │ - 1ª / 2ª Praça Dates & Values│
│ - Court / Tribunal Resolver  │              │ - Subrogated Debts (CTN 130) │
│ - Jurisdictional Extraction  │              │ - Matrícula & Cartório (RGI) │
└──────────────┬───────────────┘              └──────────────┬───────────────┘
               └──────────────────────┬──────────────────────┘
                                      ▼
                   ┌───────────────────────────────────┐
                   │  Classification & Scoring Engine  │
                   │  - DealScore (0 - 100)            │
                   │  - Liquidity Tier & Occupancy Risk│
                   │  - Net Profit Margin Formula      │
                   │  - Action (BID / WATCH / PASS)    │
                   └─────────────────┬─────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │    Async Database & Repository    │
                   │  - SQLite (Dev) / Postgres (Prod) │
                   │  - Faceted Indexes & Full-Text    │
                   └─────────────────┬─────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │         FastAPI REST API          │
                   │  - /api/v1/radar/lots (Faceted)   │
                   │  - /api/v1/radar/featured         │
                   │  - /api/v1/radar/stats            │
                   └─────────────────┬─────────────────┘
                                     │
                                     ▼
                  [https://leiloar.com/radar-leiloes]
```

---

## 2. Core Modules & Responsibilities

### 2.1 Domain Models (`src/leiloar/models/`)
- Pure Python Pydantic v2 schemas providing type safety and serialization across the application.
- `AuctionLot`: The primary data contract representing an auctioned asset, financial parameters, legal references, and location.
- `LegalProcess`: Captures Brazilian court docket data: CNJ lawsuit number, court (TJSP, TJRJ, TRT2, TRF3), vara, comarca, and litigants.
- `ClassificationResult`: Encapsulates investment viability metrics, DealScore, risk rating, and tags.

### 2.2 Scraper Layer (`src/leiloar/scrapers/`)
- `BaseScraper`: Abstract foundation handling rate-limiting windows, automatic backoff on HTTP 429, session reuse via `aiohttp`, and unified exception handling.
- Extensible Registry: Scrapers register themselves with `@register_scraper("name")`, enabling dynamic discovery and CLI execution.

### 2.3 Legal & Document Parsers (`src/leiloar/parsers/`)
- `cnj_validator`: Validates and parses 20-digit Brazilian court process numbers using the official ISO 7064 Modulo 97-10 checksum algorithm (CNJ Resolução 65/2008).
- `edital_parser`: Extracts praça dates, minimum bids, discount percentages, property registry numbers (Matrículas RGI), municipal debts, and tax subrogation conditions.

### 2.4 Classification & Scoring (`src/leiloar/classification/`)
- `AuctionClassificationEngine`: Evaluates each lot using a multi-factor risk/reward heuristic:
  $$\text{DealScore} = \text{DiscountComponent} + \text{LiquidityBonus} + \text{StabilityBonus} - \sum \text{RiskDeductions}$$
- Computes estimated net margins factoring in legal closing fees (auctioneer 5%, ITBI 3%, Cartório 1%) and eviction provisions.

### 2.5 Storage Repository (`src/leiloar/storage/`)
- Provides clean abstraction over database persistence.
- Handles atomic lot upserts, classification joins, and parameterized faceted search queries for the frontend.

### 2.6 REST API Service (`src/leiloar/api/`)
- FastAPI application exposing REST endpoints for the Leiloar web application.
- Includes OpenAPI documentation, CORS middleware, and structured responses.
