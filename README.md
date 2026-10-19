# Leiloar.com SaaS Auction Research and Classification Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An automated research, ingestion, parsing, and classification framework for Brazilian judicial and extrajudicial auctions, powering the backend intelligence of **[Leiloar.com Radar de Leilões](https://leiloar.com/radar-leiloes)**.

---

## 🎯 Overview

Finding high-yield opportunities in the Brazilian auction market (*leilões de imóveis e veículos*) is historically plagued by extreme fragmentation across hundreds of disparate auctioneers (*leiloeiros oficiais*), official state gazettes (*Diários Oficiais*), bank repossession catalogs (Caixa Econômica Federal, Banco do Brasil, Santander, Itaú, Bradesco), and state judicial court systems (TJSP, TJRJ, TRT, TRF).

Furthermore, analyzing an auction requires deep legal due diligence:
- Validating the **CNJ Process Number** (`NNNNNNN-DD.YYYY.J.TR.OOOO`).
- Extracting auction dates and minimum bids for **1ª Praça** and **2ª Praça** (often discounted at 50% or more).
- Parsing property registry numbers (**Matrículas** e Cartórios de Registro de Imóveis - RGI).
- Calculating **debt burdens** (*débitos condominiais e tributários propter rem* vs. art. 130 do CTN e art. 908 do CPC).
- Assessing **occupancy risks** (vacant vs. occupied by defendant/tenants).

**Leiloar** provides a unified, production-grade asynchronous pipeline that systematically crawls, extracts, scores, and indexes auction lots into the **Leiloar Radar** API.

---

## 🏗 Architecture Blueprint

```text
  [Internet Sources]
   ├─ Bank Portals (Caixa, BB, Santander)
   ├─ Auctioneers (Portal Zuk, Mega Leilões, Sodré Santoro)
   └─ Judicial Gazettes / DJE (Editais & Diários)
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

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- `pip` or `uv`

### Installation
```bash
git clone https://github.com/olh/leiloar.git
cd leiloar
pip install -e ".[dev]"
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
