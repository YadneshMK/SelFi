from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class PlatformType(str, enum.Enum):
    ZERODHA = "zerodha"
    GROWW = "groww"
    UPSTOX = "upstox"
    PAYTM_MONEY = "paytm_money"
    COIN = "coin"
    OTHER = "other"

class AssetType(str, enum.Enum):
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    SGB = "sgb"
    ETF = "etf"
    REIT = "reit"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pan_details = relationship("PANDetail", back_populates="user")
    platform_accounts = relationship("PlatformAccount", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")

class PANDetail(Base):
    __tablename__ = "pan_details"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pan_number = Column(String(10), unique=True, index=True, nullable=False)
    holder_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="pan_details")
    platform_accounts = relationship("PlatformAccount", back_populates="pan_detail")

class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pan_id = Column(Integer, ForeignKey("pan_details.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    client_id = Column(String, nullable=False)
    nickname = Column(String)
    account_type = Column(String)  # trading, investment, mutual_fund
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="platform_accounts")
    pan_detail = relationship("PANDetail", back_populates="platform_accounts")
    holdings = relationship("Holding", back_populates="platform_account")
    transactions = relationship("Transaction", back_populates="platform_account")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")

class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String)  # NSE, BSE
    asset_type = Column(Enum(AssetType), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    current_value = Column(Float)
    pnl = Column(Float)
    pnl_percentage = Column(Float)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional fields for mutual funds
    scheme_code = Column(String)  # For MF API
    isin = Column(String)
    
    # Relationships
    platform_account = relationship("PlatformAccount", back_populates="holdings")
    portfolio = relationship("Portfolio", back_populates="holdings")
    transactions = relationship("Transaction", back_populates="holding")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"), nullable=False)
    holding_id = Column(Integer, ForeignKey("holdings.id"))
    transaction_type = Column(String, nullable=False)  # BUY, SELL, DIVIDEND
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    charges = Column(Float, default=0)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    settlement_date = Column(DateTime(timezone=True))
    exchange_order_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    platform_account = relationship("PlatformAccount", back_populates="transactions")
    holding = relationship("Holding", back_populates="transactions")

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String)
    date = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ImportHistory(Base):
    __tablename__ = "import_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # holdings_csv, pnl_csv, etc.
    import_status = Column(String, nullable=False)  # success, failed, processing
    records_imported = Column(Integer, default=0)
    error_message = Column(Text)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())