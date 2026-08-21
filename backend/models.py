import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base

class BudgetStatus(str, enum.Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    ERRO = "erro"

class ItemCategoria(str, enum.Enum):
    GPU = "GPU"
    FONTE = "Fonte"
    GABINETE = "Gabinete"
    FAN = "Fan"
    PLACA_MAE = "Placa-mãe"
    CPU = "CPU"
    RAM = "RAM"
    ARMAZENAMENTO = "Armazenamento"
    COOLER = "Cooler"
    OUTRO = "Outro"

class ScrapingStatus(str, enum.Enum):
    PENDENTE = "pendente"
    CONCLUIDO = "concluido"
    ERRO = "erro"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    nome_arquivo = Column(String, nullable=False)
    s3_key = Column(String, nullable=False, unique=True)
    status = Column(SQLEnum(BudgetStatus), default=BudgetStatus.PENDENTE)
    valor_total_orcamento = Column(Numeric(12, 2), nullable=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="budgets")
    items = relationship("Item", back_populates="budget", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    descricao_original = Column(String, nullable=False)
    categoria = Column(SQLEnum(ItemCategoria), nullable=True)
    preco_orcamento = Column(Numeric(12, 2), nullable=False)
    loja_origem = Column(String, nullable=True)
    status_scraping = Column(SQLEnum(ScrapingStatus), default=ScrapingStatus.PENDENTE)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    budget = relationship("Budget", back_populates="items")
    market_prices = relationship("MarketPrice", back_populates="item", cascade="all, delete-orphan")

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False, index=True)
    loja = Column(String, nullable=False)
    preco = Column(Numeric(12, 2), nullable=False)
    url_produto = Column(String, nullable=True)
    nome_produto_encontrado = Column(String, nullable=True)
    coletado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    item = relationship("Item", back_populates="market_prices")

Index("ix_market_prices_item_coletado_em", MarketPrice.item_id, MarketPrice.coletado_em)