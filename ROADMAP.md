# Leiloar.com — SaaS Auction Intelligence Framework Roadmap

This document outlines the planned engineering roadmap for the **Leiloar.com SaaS Auction Research and Classification Framework**, designed to completely power **[Leiloar.com Radar de Leilões](https://leiloar.com/radar-leiloes)**.

Each milestone is broken down into specific engineering deliverables with estimated hours, technical scope, and verification criteria.

**Total Planned Work: 180 Hours**

---

```
                                  LEILOAR RADAR ROADMAP (180h)
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ Milestone 1: Multimodal OCR/PDF │ Milestone 2: Distributed Fleet  │ Milestone 3: Due Diligence Sync │
│            (32 Hours)           │            (32 Hours)           │            (32 Hours)           │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ Milestone 4: Alerting & Webhook │ Milestone 5: Headless Sync / UI │ Milestone 6: Security & Scale   │
│            (28 Hours)           │            (30 Hours)           │            (26 Hours)           │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

---

## 🎯 Milestone 1: Multimodal Edital & Matrícula Document Extraction Pipeline
**Estimated Time:** 32 Hours  
**Focus:** Ingest scanned and text-based PDFs of legal public notices (*Editais de Praça*) and property registry deeds (*Matrículas de Imóveis - RGI*).

### Tasks
- [ ] **Task 1.1: Scanned & Native PDF Document Ingestion Pipeline (8h)**
  - Integrate `PyMuPDF` (fitz) and `pdfplumber` with stream-based chunking.
  - Extract structured tables for multi-lot judicial auctions (e.g., bankruptcy asset lists).
  - *Acceptance Criteria:* Ingest 50+ page bankruptcy editais in < 2.5 seconds with zero memory leaks.

- [ ] **Task 1.2: Property Registry (Matrícula RGI) Lien & Encumbrance Parser (10h)**
  - Parse *Livro nº 2 - Registro Geral* to extract:
    - R. (Registros) and Av. (Averbações).
    - Judicial liens (*penhoras*), mortgages (*hipotecas*), usufruct (*usufruto*), and tax indisponibilities (*indisponibilidade de bens - CNIB*).
  - Flag risks of third-party ownership claims or conflicting mortgage preferences.
  - *Acceptance Criteria:* Correctly identifies 95%+ of gravames on a test suite of 40 Brazilian matrículas.

- [ ] **Task 1.3: OCR Fallback Engine for Legacy Scanned Editais (8h)**
  - Implement Tesseract / EasyOCR pipeline with preprocessing (deskewing, binarization, noise removal).
  - Extract text from poor-quality photocopies often published by state municipal forums.
  - *Acceptance Criteria:* OCR accuracy > 88% on degraded historical auction notices.

- [ ] **Task 1.4: Comprehensive Document Parser Benchmark Suite (6h)**
  - Build synthetic and anonymized test fixtures covering TJSP, TJRJ, TJMG, and TRF notices.
  - Automated CI regression runner measuring precision and recall on parsed legal values.
  - *Acceptance Criteria:* 100% automated test coverage across all legal document extraction rules.

---

## 🌐 Milestone 2: Distributed Crawler Fleet & Smart Scraping Infrastructure
**Estimated Time:** 32 Hours  
**Focus:** High-throughput, resilient scraping of 100+ Brazilian auctioneer portals and official state gazettes.

### Tasks
- [ ] **Task 2.1: Headless Browser Crawler Engine for JavaScript/SPA Portals (10h)**
  - Build Playwright / Camoufox crawler adapters with stealth mode for dynamic frontend portals (Superbid, Sodré Santoro, Freitas Leiloeiro).
  - Handle infinite scrolling, dynamic AJAX loading, and client-side rendered lot cards.
  - *Acceptance Criteria:* Reliable crawling without browser fingerprint detection or CAPTCHA triggers.

- [ ] **Task 2.2: Intelligent Proxy Rotation & Anti-Detect Middleware (8h)**
  - Implement Brazilian residential and datacenter proxy rotation with health scoring.
  - Automatic backoff on HTTP 403/429 and session cookie pooling.
  - *Acceptance Criteria:* Maintain > 99.2% request success rate over 24-hour continuous crawler runs.

- [ ] **Task 2.3: Diários Oficiais (DOU, DJE-SP, DJE-RJ) Ingestion Worker (8h)**
  - Ingest daily publications from Official Gazettes via open RSS, search queries, and legal publication feeds.
  - Detect upcoming auctions 15-30 days before they appear on commercial auctioneer websites.
  - *Acceptance Criteria:* Index first-published court notices within 6 hours of gazette issuance.

- [ ] **Task 2.4: Distributed Job Orchestration with Redis / Arq (6h)**
  - Scale out asynchronous worker pools using Redis and Arq.
  - Implement priority queues (instant re-check for lots ending within 24h vs. periodic broad scans).
  - *Acceptance Criteria:* Support concurrent scraping of 25+ auction portals simultaneously.

---

## ⚖️ Milestone 3: Automated Legal Due Diligence & Court Records Cross-Referencing
**Estimated Time:** 32 Hours  
**Focus:** Automatic verification of active lawsuits, appeals, debtor solvency, and municipal debts.

### Tasks
- [ ] **Task 3.1: e-SAJ and PJe Court Docket Scraper (12h)**
  - Query judicial docket portals (TJSP e-SAJ, TJRJ, TRT2 PJe, TRF3) using CNJ numbers.
  - Extract current procedural stage: check if the auction order has been appealed (*Agravo de Instrumento*) or suspended (*Efeito Suspensivo*).
  - *Acceptance Criteria:* Accurately identify suspensions within 1 hour of docket update.

- [ ] **Task 3.2: Debtor Solvency & Insolvency Cross-Check (8h)**
  - Query state bankruptcy registries (*recuperação judicial e falência*) for corporate defendants.
  - Assess risk of labor claims (*créditos trabalhistas superprivilegiados*) competing with the auction proceeds.
  - *Acceptance Criteria:* Generate risk indicator when defendant has > 3 active executions.

- [ ] **Task 3.3: Direct Municipal Tax (IPTU) API Integration (8h)**
  - Query online municipal debt portals for major capitals (São Paulo, Rio de Janeiro, Belo Horizonte, Curitiba) using the municipal tax enrollment number (*Inscrição Imobiliária / SQL*).
  - Reconcile actual real-time municipal debts against the values declared in the edital.
  - *Acceptance Criteria:* Real-time IPTU debt retrieval for SP and RJ municipality queries.

- [ ] **Task 3.4: Automated Certidão Negativa de Débitos (CND) Worker (4h)**
  - Scrape federal CND (Receita Federal / PGFN) and state tax compliance certidões.
  - Store timestamped PDF certificates attached to the lot due diligence package.
  - *Acceptance Criteria:* Automatic generation of due diligence checklist for each indexed lot.

---

## 🔔 Milestone 4: Real-Time Radar Alerting, Push & Multi-Channel Dispatcher
**Estimated Time:** 28 Hours  
**Focus:** Instant notification dispatch to Radar users when deals matching their criteria are indexed.

### Tasks
- [ ] **Task 4.1: Saved Search Query & Geo-Polygon Matching Engine (8h)**
  - Real-time matcher comparing freshly indexed lots against thousands of saved user search alerts.
  - Filter by discount %, city, neighborhood, maximum bid, property type, and minimum DealScore.
  - *Acceptance Criteria:* Match 1,000 newly scraped lots against 50,000 alert rules in < 500ms.

- [ ] **Task 4.2: Instant WhatsApp & Telegram Bot Dispatchers (8h)**
  - Deliver instant rich alert cards with lot photos, discount badge, appraisal, DealScore, and direct auction link.
  - Interactive bot commands: `/rastrear SP 50%`, `/lote <id>`, `/favoritos`.
  - *Acceptance Criteria:* Message delivery latency < 15 seconds from scraper persistence.

- [ ] **Task 4.3: Curated Email Digest Engine (6h)**
  - Weekly and daily curated HTML newsletters highlighting "Top Opportunities of the Week".
  - Sectioned by category: Residential Apartments, Judicial Houses, Bank Retomados, Commercial.
  - *Acceptance Criteria:* Fully responsive HTML email templates with unsubscribe and frequency controls.

- [ ] **Task 4.4: B2B Webhook Dispatcher with HMAC Signatures (6h)**
  - Allow real estate funds (FIIs), lawyers, and institutional investors to receive structured JSON webhooks.
  - Include cryptographic signature header (`X-Leiloar-Signature: sha256=...`) and automated retry policy.
  - *Acceptance Criteria:* Standardized webhook delivery with delivery logs and retry backoff.

---

## 💻 Milestone 5: SaaS Frontend Headless Sync & GraphQL Integration
**Estimated Time:** 30 Hours  
**Focus:** Seamless, real-time integration with `https://leiloar.com/radar-leiloes`.

### Tasks
- [ ] **Task 5.1: Real-Time WebSocket Channel for Live Auction Bids (8h)**
  - WebSocket connection manager streaming live bid increments and status changes (e.g., "1ª Praça Negativa -> 2ª Praça Aberta").
  - Auto-reconnect and state synchronization for active browser sessions.
  - *Acceptance Criteria:* Broadcast lot status change to 5,000 connected clients in < 100ms.

- [ ] **Task 5.2: Headless GraphQL Schema (Strawberry GraphQL) (8h)**
  - Implement full GraphQL API enabling the Leiloar React/Next.js frontend to query flexible fields and nested relations.
  - Query lot details, auctioneer profiles, court processes, and classification scores in a single request.
  - *Acceptance Criteria:* Full schema documentation with GraphiQL explorer available in development.

- [ ] **Task 5.3: Geocoding & OpenStreetMap Polygon Search (8h)**
  - Normalize addresses and compute high-accuracy latitude/longitude coordinates using Nominatim / Pelias.
  - Support bounding box and radius queries (e.g., "Find all auctions within 5 km of Faria Lima").
  - *Acceptance Criteria:* Coordinate resolution rate > 92% on Brazilian address strings.

- [ ] **Task 5.4: Investment Dossier PDF Report Generator (6h)**
  - Generate a downloadable branded "Dossiê de Arrematação" PDF for any lot.
  - Includes valuation analysis, net margin breakdown, court process summary, risks, and checklist.
  - *Acceptance Criteria:* PDF rendering in < 1.2s with charts and clean typography.

---

## 🛡️ Milestone 6: Enterprise Performance, Security Auditing & Scale
**Estimated Time:** 26 Hours  
**Focus:** Production hardening, PostgreSQL migration, observability, and open-source documentation.

### Tasks
- [ ] **Task 6.1: PostgreSQL Migration with pgvector and Full-Text Search (8h)**
  - Migrate schema to PostgreSQL with `pgvector` for semantic auction search.
  - Alembic database migration scripts with zero-downtime execution strategy.
  - *Acceptance Criteria:* Sub-50ms query latency on catalog of 500,000+ historical auction lots.

- [ ] **Task 6.2: Observability, OpenTelemetry & Prometheus Metrics (8h)**
  - Instrument scrapers, database queries, and API endpoints with OpenTelemetry.
  - Expose Prometheus `/metrics` endpoint (scraper throughput, error rates, proxy latency, parser success rate).
  - Pre-configured Grafana dashboard templates.
  - *Acceptance Criteria:* Full end-to-end trace from scraper fetch to API response.

- [ ] **Task 6.3: API Authentication, Rate Limiting & RBAC (6h)**
  - JWT authentication and API key management for SaaS tiers (Free, Pro, Institutional).
  - Token-bucket rate limiter per API tier.
  - *Acceptance Criteria:* OWASP-compliant authentication with strict role checks.

- [ ] **Task 6.4: Load Testing, Security Audit & SDK Documentation (4h)**
  - Locust stress testing simulating 1,000 requests/second on the search endpoints.
  - Static security analysis with Bandit and automated OpenAPI client SDK generation (TypeScript / Python).
  - *Acceptance Criteria:* P95 response time < 120ms under 1,000 req/s load.

---

## 📊 Summary of Effort Allocation

| Milestone | Scope | Hours |
|---|---|:---:|
| **Milestone 1** | Multimodal Edital & Matrícula Extraction Pipeline | **32h** |
| **Milestone 2** | Distributed Crawler Fleet & Smart Scraping | **32h** |
| **Milestone 3** | Automated Legal Due Diligence & Court Docket Sync | **32h** |
| **Milestone 4** | Real-Time Radar Alerting, Push & Multi-Channel Dispatch | **28h** |
| **Milestone 5** | SaaS Frontend Headless Sync & GraphQL Integration | **30h** |
| **Milestone 6** | Enterprise Performance, Security & Observability | **26h** |
| **Total** | **Comprehensive Production Roadmap** | **180h** |
