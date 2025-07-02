from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db import models
from app.services.market_data import StockDataService, MutualFundService, SGBService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stock/{symbol}")
def get_stock_info(
    symbol: str,
    exchange: str = Query("NS", description="Exchange code (NS for NSE, BO for BSE)"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current stock information"""
    info = StockDataService.get_stock_info(symbol.upper(), exchange)
    if not info:
        raise HTTPException(status_code=404, detail="Stock not found")
    return info

@router.get("/stock/{symbol}/history")
def get_stock_history(
    symbol: str,
    period: str = Query("1mo", description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)"),
    exchange: str = Query("NS", description="Exchange code"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get historical stock data"""
    history = StockDataService.get_stock_history(symbol.upper(), period, exchange)
    if not history:
        raise HTTPException(status_code=404, detail="No history found")
    return history

@router.post("/stock/bulk-quotes")
def get_bulk_stock_quotes(
    symbols: List[str],
    exchange: str = Query("NS", description="Exchange code"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get quotes for multiple stocks"""
    symbols = [s.upper() for s in symbols]
    quotes = StockDataService.get_bulk_quotes(symbols, exchange)
    return quotes

@router.get("/mutual-fund/search")
def search_mutual_funds(
    query: str = Query(..., description="Search query"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Search for mutual funds"""
    results = MutualFundService.search_mutual_fund(query)
    return results

@router.get("/mutual-fund/{scheme_code}")
def get_mutual_fund_info(
    scheme_code: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """Get mutual fund information"""
    info = MutualFundService.get_mutual_fund_info(scheme_code)
    if not info:
        raise HTTPException(status_code=404, detail="Mutual fund not found")
    return info

@router.get("/mutual-fund/{scheme_code}/history")
def get_mutual_fund_history(
    scheme_code: str,
    days: int = Query(30, description="Number of days of history"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get mutual fund NAV history"""
    history = MutualFundService.get_mutual_fund_history(scheme_code, days)
    if not history:
        raise HTTPException(status_code=404, detail="No history found")
    return history

@router.post("/update-holdings-prices")
async def update_holdings_prices(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current prices for all user holdings"""
    # Get all user holdings
    holdings = db.query(models.Holding).join(
        models.PlatformAccount
    ).filter(
        models.PlatformAccount.user_id == current_user.id
    ).all()
    
    updated_count = 0
    
    for holding in holdings:
        try:
            if holding.asset_type in [models.AssetType.STOCK, models.AssetType.ETF, models.AssetType.REIT]:
                # Update stock/ETF/REIT price (ETFs and REITs are traded like stocks)
                # Convert exchange name to suffix (NSE -> NS, BSE -> BO)
                exchange_suffix = "NS"  # default
                if holding.exchange:
                    if holding.exchange.upper() == "NSE":
                        exchange_suffix = "NS"
                    elif holding.exchange.upper() == "BSE":
                        exchange_suffix = "BO"
                    else:
                        exchange_suffix = holding.exchange
                
                logger.info(f"Fetching price for {holding.symbol} on {exchange_suffix}")
                info = StockDataService.get_stock_info(holding.symbol, exchange_suffix)
                
                if info and info.get("current_price"):
                    holding.current_price = info["current_price"]
                    holding.current_value = holding.quantity * info["current_price"]
                    holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                    holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                    holding.last_updated = datetime.utcnow()
                    updated_count += 1
                    logger.info(f"Updated {holding.symbol}: ₹{info['current_price']}")
                else:
                    logger.warning(f"No price data for {holding.symbol}")
                    
            elif holding.asset_type == models.AssetType.MUTUAL_FUND and holding.scheme_code:
                # Update mutual fund NAV
                info = MutualFundService.get_mutual_fund_info(holding.scheme_code)
                if info:
                    holding.current_price = info["nav"]
                    holding.current_value = holding.quantity * info["nav"]
                    holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                    holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                    updated_count += 1
                    
            elif holding.asset_type == models.AssetType.SGB:
                # Update SGB price
                info = SGBService.get_sgb_info(holding.symbol)
                if info:
                    holding.current_price = info["current_price"]
                    holding.current_value = holding.quantity * info["current_price"]
                    holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                    holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                    updated_count += 1
                    
        except Exception as e:
            # Log error but continue with other holdings
            print(f"Error updating {holding.symbol}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "message": f"Updated {updated_count} holdings",
        "total_holdings": len(holdings),
        "updated_count": updated_count
    }