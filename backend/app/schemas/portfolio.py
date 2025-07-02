from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    ZERODHA = "zerodha"
    GROWW = "groww"
    UPSTOX = "upstox"
    PAYTM_MONEY = "paytm_money"
    COIN = "coin"
    OTHER = "other"

class AssetType(str, Enum):
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    SGB = "sgb"
    ETF = "etf"
    REIT = "reit"

class PlatformAccountBase(BaseModel):
    platform: PlatformType
    client_id: str
    nickname: Optional[str] = None
    account_type: Optional[str] = None

class PlatformAccountCreate(PlatformAccountBase):
    pan_id: int

class PlatformAccount(PlatformAccountBase):
    id: int
    user_id: int
    pan_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class Portfolio(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class HoldingBase(BaseModel):
    symbol: str
    exchange: Optional[str] = None
    asset_type: AssetType
    quantity: float
    average_price: float

class HoldingCreate(HoldingBase):
    platform_account_id: int
    portfolio_id: Optional[int] = None
    scheme_code: Optional[str] = None  # For mutual funds
    isin: Optional[str] = None
    current_price: Optional[float] = None

class Holding(HoldingBase):
    id: int
    platform_account_id: int
    portfolio_id: Optional[int] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    last_updated: datetime
    scheme_code: Optional[str] = None
    isin: Optional[str] = None
    
    class Config:
        from_attributes = True

class HoldingWithDetails(Holding):
    platform_account: PlatformAccount
    
class PortfolioSummary(BaseModel):
    total_value: float
    total_investment: float
    total_pnl: float
    total_pnl_percentage: float
    holdings_count: int
    asset_allocation: dict
    platform_allocation: dict