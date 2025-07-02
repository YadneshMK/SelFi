import yfinance as yf
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class StockDataService:
    """Service for fetching stock data using Yahoo Finance"""
    
    @staticmethod
    def get_stock_info(symbol: str, exchange: str = "NS") -> Optional[Dict[str, Any]]:
        """Get stock information from Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., RELIANCE)
            exchange: Exchange suffix (NS for NSE, BO for BSE)
        """
        try:
            # Add exchange suffix for Indian stocks if not already present
            if exchange and not symbol.endswith(f".{exchange}"):
                ticker_symbol = f"{symbol}.{exchange}"
            else:
                ticker_symbol = symbol
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # For ETFs, we should always prefer history data as info can be unreliable
            # First, try to get from history which is more reliable
            history = ticker.history(period="2d")
            if not history.empty:
                current_price = float(history['Close'].iloc[-1])
                previous_close = float(history['Close'].iloc[-2]) if len(history) > 1 else info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            else:
                # Fallback to info fields if history is not available
                current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("price", 0)
                previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            
            # Get market time for the data
            market_time = info.get("regularMarketTime")
            if market_time:
                # Convert Unix timestamp to datetime
                last_updated = datetime.fromtimestamp(market_time).isoformat()
            else:
                last_updated = datetime.now().isoformat()
            
            return {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "current_price": current_price,
                "previous_close": previous_close,
                "day_change": current_price - previous_close if current_price and previous_close else 0,
                "day_change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close and previous_close != 0 else 0,
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "last_updated": last_updated,
                "data_source": "history" if not history.empty else "info"
            }
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}.{exchange}: {str(e)}")
            return None
    
    @staticmethod
    def get_stock_history(symbol: str, period: str = "1mo", exchange: str = "NS") -> Optional[List[Dict[str, Any]]]:
        """Get historical stock data
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            exchange: Exchange suffix
        """
        try:
            # Add exchange suffix for Indian stocks if not already present
            if exchange and not symbol.endswith(f".{exchange}"):
                ticker_symbol = f"{symbol}.{exchange}"
            else:
                ticker_symbol = symbol
            ticker = yf.Ticker(ticker_symbol)
            history = ticker.history(period=period)
            
            data = []
            for date, row in history.iterrows():
                data.append({
                    "date": date.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            
            return data
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def get_bulk_quotes(symbols: List[str], exchange: str = "NS") -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple stocks"""
        quotes = {}
        
        # Add exchange suffix to all symbols
        ticker_symbols = [f"{s}.{exchange}" for s in symbols]
        tickers = yf.Tickers(" ".join(ticker_symbols))
        
        for symbol, ticker_symbol in zip(symbols, ticker_symbols):
            try:
                ticker = tickers.tickers[ticker_symbol]
                info = ticker.info
                quotes[symbol] = {
                    "current_price": info.get("currentPrice", 0),
                    "previous_close": info.get("previousClose", 0),
                    "day_change": info.get("currentPrice", 0) - info.get("previousClose", 0),
                    "day_change_percent": ((info.get("currentPrice", 0) - info.get("previousClose", 0)) / info.get("previousClose", 1)) * 100
                }
            except Exception as e:
                logger.error(f"Error fetching quote for {symbol}: {str(e)}")
                quotes[symbol] = {
                    "current_price": 0,
                    "previous_close": 0,
                    "day_change": 0,
                    "day_change_percent": 0
                }
        
        return quotes


class MutualFundService:
    """Service for fetching mutual fund data using MF API"""
    
    BASE_URL = "https://api.mfapi.in/mf"
    
    @staticmethod
    def search_mutual_fund(query: str) -> List[Dict[str, Any]]:
        """Search for mutual funds by name"""
        try:
            response = requests.get(f"{MutualFundService.BASE_URL}/search", params={"q": query})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error searching mutual funds: {str(e)}")
            return []
    
    @staticmethod
    def get_mutual_fund_info(scheme_code: str) -> Optional[Dict[str, Any]]:
        """Get mutual fund information by scheme code"""
        try:
            response = requests.get(f"{MutualFundService.BASE_URL}/{scheme_code}")
            if response.status_code == 200:
                data = response.json()
                
                # Get latest NAV
                nav_data = data.get("data", [])
                latest_nav = nav_data[0] if nav_data else {}
                
                return {
                    "scheme_code": scheme_code,
                    "scheme_name": data.get("meta", {}).get("scheme_name", ""),
                    "fund_house": data.get("meta", {}).get("fund_house", ""),
                    "scheme_type": data.get("meta", {}).get("scheme_type", ""),
                    "scheme_category": data.get("meta", {}).get("scheme_category", ""),
                    "nav": float(latest_nav.get("nav", 0)),
                    "date": latest_nav.get("date", "")
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching mutual fund info: {str(e)}")
            return None
    
    @staticmethod
    def get_mutual_fund_history(scheme_code: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get historical NAV data for a mutual fund"""
        try:
            response = requests.get(f"{MutualFundService.BASE_URL}/{scheme_code}")
            if response.status_code == 200:
                data = response.json()
                nav_data = data.get("data", [])[:days]
                
                history = []
                for nav in nav_data:
                    history.append({
                        "date": nav.get("date"),
                        "nav": float(nav.get("nav", 0))
                    })
                
                return history
            return None
        except Exception as e:
            logger.error(f"Error fetching mutual fund history: {str(e)}")
            return None
    
    @staticmethod
    def get_all_schemes() -> List[Dict[str, Any]]:
        """Get list of all mutual fund schemes"""
        try:
            response = requests.get(MutualFundService.BASE_URL)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching all schemes: {str(e)}")
            return []


class SGBService:
    """Service for Sovereign Gold Bond data"""
    
    @staticmethod
    def get_sgb_info(symbol: str) -> Optional[Dict[str, Any]]:
        """Get SGB information using multiple sources"""
        # First try Yahoo Finance
        yahoo_data = StockDataService.get_stock_info(symbol, "NS")
        if yahoo_data and yahoo_data.get('current_price', 0) > 0:
            return yahoo_data
        
        # If Yahoo doesn't have data, use our SGB price service
        try:
            from app.services.sgb_price_service import SGBPriceService
            
            # Get SGB price per unit
            # SGBs are denominated in grams, typical holding is in units
            # Each unit = 1 gram of gold
            price_per_gram = SGBPriceService.get_sgb_price(symbol)
            
            if price_per_gram:
                return {
                    'symbol': symbol,
                    'current_price': price_per_gram,
                    'previous_close': price_per_gram,  # Same as current for now
                    'change': 0,
                    'change_percent': 0,
                    'currency': 'INR',
                    'exchange': 'SGB',
                    'last_updated': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error fetching SGB price for {symbol}: {e}")
        
        return None