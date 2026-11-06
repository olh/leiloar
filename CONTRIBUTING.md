# Contributing to Leiloar

Thank you for your interest in contributing to **Leiloar.com SaaS Auction Intelligence Framework**! This framework powers the backend aggregation, parsing, scoring, and indexing of Brazilian judicial and extrajudicial auctions for **[Leiloar.com Radar de Leilões](https://leiloar.com/radar-leiloes)**.

---

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/olh/leiloar.git
   cd leiloar
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies in editable mode:**
   ```bash
   pip install -e ".[dev]"
   pip install httpx
   ```

4. **Verify the test suite passes:**
   ```bash
   python -m pytest -v
   ```

---

## 🏗️ Adding a New Auctioneer Scraper

To add support for a new Brazilian auction portal (e.g. Freitas Leiloeiro, Sodré Santoro, Milan Leilões):

1. Create a new directory under `src/leiloar/scrapers/<portal_name>/`.
2. Implement your scraper subclassing `BaseScraper`:
   ```python
   from leiloar.models.auction import AuctionLot
   from leiloar.scrapers.base import BaseScraper
   from leiloar.scrapers.registry import register_scraper

   @register_scraper("my_auctioneer")
   class MyAuctioneerScraper(BaseScraper):
       source_name = "my_auctioneer"
       source_type = "judicial"  # or extrajudicial_bank

       async def scrape(self, **kwargs) -> list[AuctionLot]:
           # Ingest and return standardized AuctionLot instances
           ...
   ```
3. Register the import in `src/leiloar/scrapers/__init__.py`.
4. Add unit tests in `tests/test_scrapers.py`.
5. Run the test suite: `python -m pytest tests/test_scrapers.py`.

---

## 🧪 Code Quality & Pull Request Guidelines

- **Zero Secrets Policy:** Never commit `.env`, private keys, passwords, or personal credentials.
- **Privacy:** Use synthetic or anonymized sample data in fixtures and tests.
- **Type Hints:** Use PEP 484 type annotations on all public functions and models.
- **Tests Required:** Every new scraper or parser must include unit tests.
- **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
  - `feat(...)`: New feature or parser
  - `fix(...)`: Bug fix
  - `docs(...)`: Documentation updates
  - `test(...)`: Test additions or adjustments

---

## 📄 License

By contributing to this repository, you agree that your contributions will be licensed under the [MIT License](LICENSE).
