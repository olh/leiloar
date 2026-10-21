"""Domain models for asset specifications (Real Estate, Vehicles, Machinery)."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AssetCategory(str, Enum):
    """Normalized asset categorization."""
    REAL_ESTATE_APARTMENT = "imovel_apartamento"
    REAL_ESTATE_HOUSE = "imovel_casa"
    REAL_ESTATE_COMMERCIAL = "imovel_comercial"
    REAL_ESTATE_LAND = "imovel_terreno"
    REAL_ESTATE_RURAL = "imovel_rural"
    REAL_ESTATE_INDUSTRIAL = "imovel_galpao"
    VEHICLE_CAR = "veiculo_carro"
    VEHICLE_MOTORCYCLE = "veiculo_moto"
    VEHICLE_HEAVY = "veiculo_caminhao"
    MACHINERY = "maquinario_industrial"
    SUNDRY = "bens_diversos"


class OccupancyStatus(str, Enum):
    """Occupancy status of a real estate asset."""
    VACANT = "desocupado"
    OCCUPIED_BY_DEFENDANT = "ocupado_mutuario_ou_executado"
    RENTED_TO_THIRD_PARTY = "locado_terceiros"
    UNKNOWN = "desconhecido"


class RealEstateAsset(BaseModel):
    """Detailed real estate specifications."""
    usable_area_m2: Optional[float] = Field(default=None, description="Área útil ou privativa em m²")
    total_area_m2: Optional[float] = Field(default=None, description="Área total ou do terreno em m²")
    bedrooms: Optional[int] = Field(default=None)
    suites: Optional[int] = Field(default=None)
    bathrooms: Optional[int] = Field(default=None)
    parking_spots: Optional[int] = Field(default=None)
    floor: Optional[int] = Field(default=None)
    condominium_monthly_fee: Optional[float] = Field(default=None, description="Valor mensal estimado de condomínio (R$)")
    iptu_annual_fee: Optional[float] = Field(default=None, description="Valor anual de IPTU (R$)")
    occupancy_status: OccupancyStatus = Field(default=OccupancyStatus.UNKNOWN)
    accepts_financing: bool = Field(default=False, description="Whether bank allows mortgage/SFH financing")
    accepts_fgts: bool = Field(default=False, description="Whether FGTS balance can be used")


class VehicleAsset(BaseModel):
    """Detailed vehicle specifications."""
    make: Optional[str] = Field(default=None, description="Fabricante (e.g. Toyota, Honda, VW)")
    model: Optional[str] = Field(default=None, description="Modelo (e.g. Corolla 2.0 XEi)")
    year_manufacture: Optional[int] = Field(default=None)
    year_model: Optional[int] = Field(default=None)
    color: Optional[str] = Field(default=None)
    fuel_type: Optional[str] = Field(default=None, description="Combustível (Flex, Gasolina, Diesel)")
    mileage_km: Optional[int] = Field(default=None)
    fipe_value: Optional[float] = Field(default=None, description="Tabela FIPE benchmark value (R$)")
    running_condition: bool = Field(default=True, description="Veículo funcionando / motor dá partida")
    has_keys: bool = Field(default=True)
