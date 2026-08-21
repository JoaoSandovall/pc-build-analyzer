from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

class ItemCategoriaInput(str, Enum):
    GPU = "GPU"
    FONTE = "FONTE"
    GABINETE = "GABINETE"
    FAN = "FAN"
    PLACA_MAE = "PLACA_MAE"
    CPU = "CPU"
    RAM = "RAM"
    ARMAZENAMENTO = "ARMAZENAMENTO"
    COOLER = "COOLER"
    OUTRO = "OUTRO"

PositivePrice = Annotated[
    Decimal, Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
]

class ExtractedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descricao_original: str = Field(min_length=1, max_length=500)
    categoria: ItemCategoriaInput
    preco_orcamento: PositivePrice
    loja_origem: str | None = None

    @field_validator("descricao_original")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("a descrição não pode ficar vazia")
        return value

class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    itens: list[ExtractedItem] = Field(min_length=1, max_length=100)

class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome_arquivo: str = Field(min_length=1, max_length=255)

    @field_validator("nome_arquivo")
    @classmethod
    def reject_paths(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("envie somente o nome do arquivo, sem caminho")
        return value.strip()

class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    budget_id: UUID

class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descricao_original: str | None = Field(default=None, min_length=1, max_length=500)
    categoria: ItemCategoriaInput | None = None
    preco_orcamento: PositivePrice | None = None

    @field_validator("descricao_original")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value else value

class VereditoPreco(str, Enum):
    JUSTO = "JUSTO"
    ACIMA_DA_MEDIA = "ACIMA_DA_MEDIA"
    MUITO_ACIMA = "MUITO_ACIMA"
    SEM_DADOS = "SEM_DADOS"

class MarketPriceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    loja: str
    preco: Decimal
    url_produto: str
    nome_produto_encontrado: str | None = None
    coletado_em: str

class ComparisonItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    descricao_original: str
    categoria: str
    preco_orcamento: Decimal
    loja_origem: str | None = None
    status_scraping: str
    menor_preco_mercado: Decimal | None = None
    preco_medio_mercado: Decimal | None = None
    veredito: VereditoPreco
    precos_mercado: list[MarketPriceOut] = Field(default_factory=list)

class ComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    budget_id: str
    valor_total_orcamento: Decimal
    economia_potencial: Decimal
    itens: list[ComparisonItem] = Field(default_factory=list)