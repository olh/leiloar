# Leiloar.com — SaaS Auction Research and Classification Framework

[![CI](https://github.com/olh/leiloar/actions/workflows/ci.yml/badge.svg)](https://github.com/olh/leiloar/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

An automated ingestion, legal parsing, opportunity classification, and search framework for Brazilian judicial and extrajudicial auctions, powering the backend intelligence of **[Leiloar.com Radar de Leilões](https://leiloar.com/radar-leiloes)**.

---

## 🎯 What the Project Does

In the Brazilian real estate and automotive auction ecosystem, valuable asset opportunities are dispersed across hundreds of disconnected portals:
- **Bank Portals (Extrajudicial):** Caixa Econômica Federal (*imóveis retomados e leilão SFI*), Banco do Brasil, Santander, Bradesco, Itaú.
- **Official Auctioneers (*Leiloeiros Oficiais*):** Zukerman Leilões, Mega Leilões, Sodré Santoro, Freitas Leiloeiro, Superbid.
- **Judicial Courts (*Leilões Judiciais*):** Tribunal de Justiça de São Paulo (TJSP), TJRJ, TRT2, TRF3, etc.
- **Official Gazettes (*Diários Oficiais*):** Editais de hasta pública published in DOU and DJE.

**Leiloar** provides a production-grade asynchronous pipeline that:
1. **Crawls & Ingests:** Scrapes auction listings from bank feeds, HTML portals, and judicial public notices with polite rate limiting and automated retries.
2. **Parses Legal Documents:** Automatically extracts and validates Brazilian lawsuit identifiers (**CNJ numbers**) via ISO 7064 Modulo 97-10 check digits, 1ª and 2ª praça schedules, property deeds (**Matrículas RGI**), and debt subrogation conditions (Art. 130 CTN / Art. 908 CPC).
3. **Classifies & Scores:** Analyzes every lot with a proprietary **DealScore (0–100)** heuristic combining discount spread, legal debt burdens, eviction complexity, and metropolitan liquidity.
4. **Indexes & Powers Radar:** Delivers high-speed faceted search, statistics, and alert webhooks via a FastAPI REST service consumed directly by `https://leiloar.com/radar-leiloes`.

---

## 👥 Who It's For

- **Leiloar.com SaaS Users & Subscribers:** Real estate investors, funds (FIIs), and private buyers searching for 40%–70% discounted properties without hidden legal traps.
- **Real Estate Attorneys & Due Diligence Specialists:** Professionals needing instant extraction of court dockets, municipal IPTU debts, and condominium liabilities from judicial editais.
- **Auctioneers & Institutional Sellers:** Platforms needing automated catalog syndication, classification tagging, and deal distribution.

---

## 🛠️ What It's Built With

- **Language:** Python 3.10+
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) with asynchronous request handling and OpenAPI Swagger docs.
- **Data Modeling & Validation:** [Pydantic v2](https://docs.pydantic.dev/) with strict schema enforcement.
- **HTTP & Crawling Engine:** `aiohttp`, `requests`, and `httpx` with exponential backoff and polite rate limiting.
- **Legal & Document Parsing:** ISO 7064 Modulo 97-10 CNJ checksum algorithm, regex-based edital parsers, and `python-dateutil`.
- **Database & Persistence:** SQLite (embedded local development & edge) and PostgreSQL (production deployment).
- **Testing:** `pytest` and `anyio` with 100% test pass rate across unit and integration suites.

---

## 🏗️ Architecture Blueprint

```text
  [Internet Sources]
   ├─ Bank Portals (Caixa SFI, BB, Santander)
   ├─ Auctioneers (Portal Zuk, Mega Leilões, Sodré Santoro)
   └─ Official Gazettes / DJE (Editais & Diários)
            │
            ▼
   ┌─────────────────────────────────────────┐
   │        Scraper Fleet & Ingestion        │
   │  - Async rate limiting & backoff        │
   │  - Anti-detect headers & session reuse  │
   └────────────────────┬────────────────────┘
                        ▼
   ┌─────────────────────────────────────────┐
   │        Legal & Document Parsers         │
   │  - CNJ Checksum Validator (Mod 97)      │
   │  - Edital Praça & Value Regex Extractor │
   │  - Property Matrícula / RGI Parser      │
   └────────────────────┬────────────────────┘
                        ▼
   ┌─────────────────────────────────────────┐
   │     Classification & Scoring Engine     │
   │  - Discount Spread & Net ROI Model      │
   │  - Legal & Debt Risk Matrix (DealScore) │
   │  - Categorization & Tagging Taxonomy    │
   └────────────────────┬────────────────────┘
                        ▼
   ┌─────────────────────────────────────────┐
   │          Storage & Radar API            │
   │  - Async Repository (SQLite / Postgres) │
   │  - FastAPI REST Service                 │
   │  - Webhook Alert Dispatcher             │
   └────────────────────┬────────────────────┘
                        │
                        ▼
       [https://leiloar.com/radar-leiloes]
```

Detailed architectural specifications are available in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🚀 Quickstart & How to Run

### 1. Installation

Clone the repository and install dependencies in editable mode:

```bash
git clone https://github.com/olh/leiloar.git
cd leiloar
pip install -e ".[dev]"
```

### 2. Environment Configuration

Copy the sample environment file:

```bash
cp .env.example .env
```

*(Note: Zero secrets or private credentials are required for local operation. The template comes pre-configured with safe defaults).*

### 3. Running Scrapers & Ingestion

Ingest sample auction data from Caixa Econômica Federal:

```bash
# Ingest and classify Caixa repossessed property lots
python -m leiloar.cli crawl --scraper caixa --fixture fixtures/sample_caixa_data.json
```

Output:
```text
[INFO] leiloar.cli: Starting crawler 'caixa' for UF=SP...
[INFO] leiloar.cli: Extracted 3 lots from 'caixa'
[INFO] leiloar.cli: Successfully processed and indexed 3 lots into Radar database.
```

### 4. Parsing a Judicial Auction Notice (Edital)

Parse a real or sample Brazilian court auction notice:

```bash
python -m leiloar.cli parse-edital --file fixtures/sample_edital_judicial.txt
```

Output:
```text
============================================================
LEILOAR RADAR - EDITAL JUDICIAL EXTRACTION
============================================================
Processo CNJ:      1014522-74.2021.8.26.0100
Tribunal / Vara:   TJSP - 32ª VARA CÍVEL
Comarca:           SÃO PAULO
Exequente:         CONDOMÍNIO EDIFÍCIO VILA REAL
Executado:         MARCOS ROBERTO DA SILVA
Matrícula / RGI:   45.892 (4º OFICIAL DE REGISTRO DE IMÓVEIS DE SÃO PAULO/SP)
Avaliação:         R$ 1,200,000.00
1ª Praça:          10/12/2026 - Lance Mín: R$ 1,200,000.00
2ª Praça:          13/12/2026 - Lance Mín: R$ 600,000.00 (50.0% desconto)
Débito Condomínio: R$ 85,420.15
Débito IPTU:       R$ 32,180.00
Sub-rogação:       Sim (Art. 130 CTN)
Ocupação:          Ocupado
============================================================
```

### 5. Validating CNJ Lawsuit Numbers

Verify Brazilian court lawsuit checksums:

```bash
python -m leiloar.cli validate-cnj --cnj 1014522-74.2021.8.26.0100
```

### 6. Starting the Radar REST API Server

Launch the FastAPI backend service:

```bash
python -m leiloar.cli serve --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

### 7. Running with Docker & Docker Compose

Run the fully containerized API server with healthchecks:

```bash
docker compose up -d
```

### 8. Running Tests

Execute the comprehensive test suite:

```bash
python -m pytest -v
```

```text
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_list_radar_lots PASSED
tests/test_api.py::test_filter_radar_by_state_and_discount PASSED
tests/test_api.py::test_get_featured_deals PASSED
tests/test_api.py::test_get_market_statistics PASSED
tests/test_api.py::test_get_lot_details_success_and_404 PASSED
tests/test_classification_engine.py::test_classify_high_opportunity_vacant_apartment PASSED
tests/test_classification_engine.py::test_classify_high_risk_non_subrogated_debt PASSED
tests/test_cnj_validator.py::test_compute_cnj_check_digits PASSED
tests/test_cnj_validator.py::test_validate_cnj_valid_and_invalid PASSED
tests/test_cnj_validator.py::test_parse_cnj_components PASSED
tests/test_cnj_validator.py::test_extract_cnj_from_edital_text PASSED
tests/test_edital_parser.py::test_parse_sample_edital_judicial PASSED
tests/test_scrapers.py::test_scraper_registry PASSED
tests/test_scrapers.py::test_portal_zuk_parsing PASSED
tests/test_scrapers.py::test_mega_leiloes_parsing PASSED
tests/test_scrapers.py::test_caixa_scraper_parsing_fixture PASSED
tests/test_storage.py::test_repository_upsert_and_search PASSED

======================== 18 passed in 0.72s ========================
```

---

## 🗺️ Roadmap Ahead (180 Hours)

A detailed engineering roadmap comprising **180 hours of planned work** across 6 core milestones is documented in **[ROADMAP.md](ROADMAP.md)** and tracked via **[GitHub Issues](https://github.com/olh/leiloar/issues)**:

| Milestone | Scope | Hours |
|---|---|:---:|
| **Milestone 1** | Multimodal Edital & Matrícula Extraction Pipeline | **32h** |
| **Milestone 2** | Distributed Crawler Fleet & Smart Scraping Infrastructure | **32h** |
| **Milestone 3** | Automated Legal Due Diligence & Court Docket Sync | **32h** |
| **Milestone 4** | Real-Time Radar Alerting, Push & Multi-Channel Dispatch | **28h** |
| **Milestone 5** | SaaS Frontend Headless Sync & GraphQL Integration | **30h** |
| **Milestone 6** | Enterprise Performance, Security & Observability | **26h** |
| **Total** | **Comprehensive Production Roadmap** | **180h** |

---

## 🔒 Security & Privacy

- **Zero Personal or Regulated Data:** The framework exclusively ingests and processes public, non-confidential asset listings from official court gazettes and bank auction catalogs. It does not collect, process, or store personal data (PII), customer records, or regulated financial/health information.
- **No Secrets in History:** The repository contains zero API keys, passwords, or personal credentials. Configuration is strictly environment-based via `.env.example`.
- **Synthetic Sample Data:** All test fixtures and sample editais use mock identifiers and fictional characters to protect privacy.
- **Non-Frontier / Rule-Based Architecture:** Uses deterministic parsers, heuristics, and financial models for asset evaluation without building, training, or benchmarking frontier AI models.
- **Code Standards:** Built in compliance with PEP 8 and modern Python type annotations.

---

## 📄 License

This project is open-source software licensed under the **[MIT License](LICENSE)**.
