"""Command Line Interface (CLI) for Leiloar framework operations."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from leiloar.classification.engine import AuctionClassificationEngine
from leiloar.config import settings
from leiloar.parsers.cnj_validator import parse_cnj, validate_cnj
from leiloar.parsers.edital_parser import JudicialEditalParser
from leiloar.scrapers import get_scraper_class, list_registered_scrapers
from leiloar.storage.database import DatabaseManager
from leiloar.storage.repository import AuctionRepository

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("leiloar.cli")


async def run_crawl(scraper_name: str, uf: str, fixture: Optional[str] = None) -> None:
    """Execute auction crawler, score discovered lots, and persist to radar database."""
    logger.info(f"Starting crawler '{scraper_name}' for UF={uf}...")
    scraper_cls = get_scraper_class(scraper_name)
    scraper = scraper_cls()

    db = DatabaseManager(settings.database_path)
    repo = AuctionRepository(db)
    engine = AuctionClassificationEngine()

    try:
        lots = await scraper.scrape(uf=uf, fixture_file=fixture)
        logger.info(f"Extracted {len(lots)} lots from '{scraper_name}'")

        classified_count = 0
        for lot in lots:
            classification = engine.classify(lot)
            repo.upsert_lot(lot, classification)
            classified_count += 1

        logger.info(f"Successfully processed and indexed {classified_count} lots into Radar database.")
    finally:
        await scraper.close()
        db.close()


def run_parse_edital(file_path: str) -> None:
    """Parse raw text from a judicial auction notice (Edital)."""
    p = Path(file_path)
    if not p.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        content = f.read()

    parser = JudicialEditalParser()
    result = parser.parse(content)

    print("\n" + "=" * 60)
    print("LEILOAR RADAR - EDITAL JUDICIAL EXTRACTION")
    print("=" * 60)
    print(f"Processo CNJ:      {result.cnj_number or 'Não identificado'}")
    print(f"Tribunal / Vara:   {result.court or ''} - {result.vara or ''}")
    print(f"Comarca:           {result.comarca or ''}")
    print(f"Exequente:         {result.exequente or ''}")
    print(f"Executado:         {result.executado or ''}")
    print(f"Matrícula / RGI:   {result.matricula or ''} ({result.cartorio_rgi or ''})")
    print(f"Avaliação:         R$ {result.appraisal_value:,.2f}")
    if result.stage_1_date:
        print(f"1ª Praça:          {result.stage_1_date.strftime('%d/%m/%Y')} - Lance Mín: R$ {result.stage_1_price or 0:,.2f}")
    if result.stage_2_date:
        print(f"2ª Praça:          {result.stage_2_date.strftime('%d/%m/%Y')} - Lance Mín: R$ {result.stage_2_price or 0:,.2f} ({result.stage_2_discount_pct:.1f}% desconto)")
    print(f"Débito Condomínio: R$ {result.debt_condominio:,.2f}")
    print(f"Débito IPTU:       R$ {result.debt_iptu:,.2f}")
    print(f"Sub-rogação:       {'Sim (Art. 130 CTN)' if result.subrogates_debts else 'Não (Arrematante assume)'}")
    print(f"Ocupação:          {'Ocupado' if result.is_occupied else 'Desocupado'}")
    print("=" * 60 + "\n")


def run_validate_cnj(cnj_str: str) -> None:
    """Validate and inspect CNJ lawsuit number."""
    valid = validate_cnj(cnj_str)
    parsed = parse_cnj(cnj_str)
    print(f"\nCNJ Number: {cnj_str}")
    print(f"Valid Checksum (Modulo 97): {'YES' if valid else 'NO'}")
    if parsed:
        print(f"Formatted:  {parsed.formatted}")
        print(f"Segment:    {parsed.segment_name}")
        print(f"Court:      {parsed.court_name}")
        print(f"Year:       {parsed.year}")
        print(f"Order:      {parsed.order_number}")
    print()


def run_stats() -> None:
    """Print market summary statistics from the local radar database."""
    db = DatabaseManager(settings.database_path)
    repo = AuctionRepository(db)
    stats = repo.get_market_statistics()
    print("\n" + "=" * 60)
    print("LEILOAR RADAR - MARKET STATISTICS")
    print("=" * 60)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("=" * 60 + "\n")
    db.close()


def run_serve(host: str, port: int, reload: bool) -> None:
    """Launch FastAPI Uvicorn server."""
    import uvicorn
    logger.info(f"Starting Leiloar Radar API on http://{host}:{port} ...")
    uvicorn.run("leiloar.api:create_app", host=host, port=port, reload=reload, factory=True)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="leiloar",
        description="Leiloar.com SaaS auction research and classification framework CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # crawl
    p_crawl = subparsers.add_parser("crawl", help="Run ingestion scraper and classifier")
    p_crawl.add_argument("--scraper", default="caixa", choices=list_registered_scrapers(), help="Target scraper")
    p_crawl.add_argument("--uf", default=settings.default_uf, help="Federation State code (e.g. SP, RJ)")
    p_crawl.add_argument("--fixture", default=None, help="Optional local fixture JSON path")

    # parse-edital
    p_edital = subparsers.add_parser("parse-edital", help="Parse judicial edital text file")
    p_edital.add_argument("--file", required=True, help="Path to edital text file")

    # validate-cnj
    p_cnj = subparsers.add_parser("validate-cnj", help="Validate CNJ legal lawsuit identifier")
    p_cnj.add_argument("--cnj", required=True, help="CNJ process string")

    # stats
    subparsers.add_parser("stats", help="Display market and database statistics")

    # serve
    p_serve = subparsers.add_parser("serve", help="Run FastAPI Radar server")
    p_serve.add_argument("--host", default=settings.api_host, help="Bind host")
    p_serve.add_argument("--port", type=int, default=settings.api_port, help="Bind port")
    p_serve.add_argument("--reload", action="store_true", help="Enable dev auto-reload")

    args = parser.parse_args()

    if args.command == "crawl":
        asyncio.run(run_crawl(args.scraper, args.uf, args.fixture))
    elif args.command == "parse-edital":
        run_parse_edital(args.file)
    elif args.command == "validate-cnj":
        run_validate_cnj(args.cnj)
    elif args.command == "stats":
        run_stats()
    elif args.command == "serve":
        run_serve(args.host, args.port, args.reload)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
