"""Domain models for auctions, auctioneers, lots, and legal judicial processes."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class AuctionSourceType(str, Enum):
    """Origin source of the auction listing."""
    JUDICIAL = "judicial"  # Leilão Judicial (TJ, TRT, TRF)
    EXTRAJUDICIAL_BANK = "extrajudicial_bank"  # Alienação fiduciária (Caixa, BB, Santander, etc.)
    EXTRAJUDICIAL_CORPORATE = "extrajudicial_corporate"  # Desinvestimento corporativo/industrial
    GOVERNMENT_DETRAN = "government_detran"  # Leilões de órgãos públicos e DETRAN
    DIRECT_SALE = "direct_sale"  # Venda direta / leilão homologado


class AuctionStage(str, Enum):
    """Auction bidding stage / praça."""
    FIRST_STAGE = "1a_praca"  # 1ª Praça / Hasta pública inicial (valor integral de avaliação)
    SECOND_STAGE = "2a_praca"  # 2ª Praça (desconto de até 50% ou lance mínimo legal)
    SINGLE_STAGE = "praca_unica"  # Praça única (comum em extrajudiciais e frotas)
    DIRECT_PROPOSAL = "proposta_direta"  # Fase pós-leilão / venda direta


class AuctionStatus(str, Enum):
    """Lifecycle status of the lot/auction."""
    UPCOMING = "upcoming"  # Agendado
    OPEN = "open"  # Aberto para lances
    SUSPENDED = "suspended"  # Suspenso por decisão judicial (liminar/agravo)
    CANCELLED = "cancelled"  # Cancelado / Extinto
    SOLD = "sold"  # Arrematado
    UNSOLD = "unsold"  # Deserto / Negativo


class LegalSegment(str, Enum):
    """Brazilian Judiciary segment (Resolução CNJ nº 65/2008)."""
    STF = "STF"
    CNJ = "CNJ"
    STJ = "STJ"
    JUSTICA_FEDERAL = "TRF"
    JUSTICA_DO_TRABALHO = "TRT"
    JUSTICA_ELEITORAL = "TRE"
    JUSTICA_MILITAR_UNIAO = "JMU"
    JUSTICA_ESTADUAL = "TJ"
    JUSTICA_MILITAR_ESTADUAL = "JME"
    OUTRO = "OUTRO"


class LegalProcess(BaseModel):
    """Judicial process details related to a court-ordered auction."""
    cnj_number: str = Field(..., description="CNJ formatted number: NNNNNNN-DD.YYYY.J.TR.OOOO")
    court: str = Field(default="", description="Court name (e.g. TJSP, TRT2, TRF3)")
    vara: str = Field(default="", description="Judicial division (e.g. 1ª Vara Cível)")
    comarca: str = Field(default="", description="Jurisdiction/city (e.g. Foro Central Cível de São Paulo)")
    exequente: Optional[str] = Field(default=None, description="Plaintiff/Creditor (e.g. Condomínio, Banco)")
    executado: Optional[str] = Field(default=None, description="Defendant/Debtor")
    action_type: Optional[str] = Field(default=None, description="Class (e.g. Execução de Título Extrajudicial)")
    court_link: Optional[str] = Field(default=None, description="Direct URL to court docket/process")


class Auctioneer(BaseModel):
    """Auctioneer entity (Leiloeiro Oficial)."""
    name: str = Field(..., description="Trade name or official auctioneer name")
    registry_number: Optional[str] = Field(default=None, description="Registration at Board of Trade (ex: JUCESP 1234)")
    website: Optional[str] = Field(default=None, description="Portal URL")
    state: str = Field(default="SP", description="Federation Unit (UF)")
    is_verified: bool = Field(default=True, description="Verified official auctioneer")


class AuctionLot(BaseModel):
    """Individual auction lot representing an asset being auctioned."""
    lot_id: str = Field(..., description="Unique lot hash or source identifier")
    title: str = Field(..., description="Concise lot headline")
    description: str = Field(default="", description="Complete description of the asset and conditions")
    category: str = Field(default="imovel_residencial", description="Taxonomic category")
    source_type: AuctionSourceType = Field(default=AuctionSourceType.JUDICIAL)
    status: AuctionStatus = Field(default=AuctionStatus.UPCOMING)
    
    # Financials
    appraisal_value: float = Field(default=0.0, description="Valor de avaliação oficial (R$)")
    minimum_bid: float = Field(default=0.0, description="Current minimum starting bid (R$)")
    stage_1_date: Optional[datetime] = Field(default=None, description="1ª Praça end date")
    stage_1_price: Optional[float] = Field(default=None, description="1ª Praça minimum bid")
    stage_2_date: Optional[datetime] = Field(default=None, description="2ª Praça end date")
    stage_2_price: Optional[float] = Field(default=None, description="2ª Praça minimum bid")
    current_discount_pct: float = Field(default=0.0, description="Discount relative to appraisal value (0-100%)")
    
    # Legal & Debts
    legal_process: Optional[LegalProcess] = Field(default=None)
    matricula: Optional[str] = Field(default=None, description="Property registry number (Matrícula RGI)")
    cartorio: Optional[str] = Field(default=None, description="Real estate registry office (Cartório de Registro)")
    debt_condominio: float = Field(default=0.0, description="Known condominium arrears (R$)")
    debt_iptu: float = Field(default=0.0, description="Known municipal tax arrears (R$)")
    subrogated_debts: bool = Field(default=True, description="Whether taxes subrogate in the auction price (Art. 130 CTN)")
    occupied: Optional[bool] = Field(default=None, description="Whether property is physically occupied")
    
    # Location
    address: Optional[str] = Field(default=None)
    neighborhood: Optional[str] = Field(default=None)
    city: str = Field(default="São Paulo")
    state: str = Field(default="SP", max_length=2)
    postal_code: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    
    # External URLs
    url: str = Field(..., description="Auctioneer's lot listing URL")
    edital_url: Optional[str] = Field(default=None, description="Direct URL to legal public notice (Edital)")
    auctioneer_name: str = Field(default="Leiloeiro Oficial")
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class Auction(BaseModel):
    """Auction event containing one or more lots."""
    auction_id: str = Field(..., description="Unique auction event identifier")
    title: str = Field(..., description="Auction headline")
    auctioneer: Auctioneer
    source_type: AuctionSourceType = Field(default=AuctionSourceType.JUDICIAL)
    legal_process: Optional[LegalProcess] = Field(default=None)
    lots: List[AuctionLot] = Field(default_factory=list)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    url: Optional[str] = Field(default=None)

