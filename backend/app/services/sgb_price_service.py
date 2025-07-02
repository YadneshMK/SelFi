"""
Service for fetching SGB prices from multiple sources
"""
import requests
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SGBPriceService:
    """Service to fetch SGB prices from various sources"""
    
    # Cache for SGB prices (simple in-memory cache)
    _price_cache = {}
    _cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    @classmethod
    def get_sgb_price(cls, symbol: str) -> Optional[float]:
        """
        Get SGB price from various sources
        Priority order:
        1. Gold price calculation (most reliable)
        2. Web scraping from financial sites
        3. Cached values
        """
        # Check cache first
        cached_price = cls._get_cached_price(symbol)
        if cached_price:
            return cached_price
        
        # Try different methods
        price = None
        
        # Method 1: Calculate based on gold price
        if 'SGB' in symbol:
            price = cls._calculate_sgb_price_from_gold()
        
        # Method 2: Try to get from financial websites
        if not price:
            price = cls._fetch_from_moneycontrol(symbol)
        
        # Method 3: Try BSE/NSE bhavcopy
        if not price:
            price = cls._fetch_from_bhavcopy(symbol)
        
        # Cache the price if found
        if price:
            cls._cache_price(symbol, price)
        
        return price
    
    @classmethod
    def _calculate_sgb_price_from_gold(cls) -> Optional[float]:
        """
        Calculate SGB price based on current gold price
        SGBs are priced based on gold price with premium
        """
        try:
            from app.services.gold_price_service import GoldPriceService
            
            # Get SGB price calculated from current gold price
            sgb_price = GoldPriceService.calculate_sgb_price()
            
            if sgb_price > 0:
                logger.info(f"Calculated SGB price from gold: ₹{sgb_price:.2f}")
                return sgb_price
            
        except Exception as e:
            logger.error(f"Error calculating SGB price from gold: {e}")
        
        # Fallback - use hardcoded estimate
        # This should be updated periodically
        logger.warning("Using fallback SGB price estimate")
        return 7500.0  # Approximate SGB price per gram
    
    @classmethod
    def _fetch_from_moneycontrol(cls, symbol: str) -> Optional[float]:
        """Try to fetch SGB price from MoneyControl"""
        try:
            # MoneyControl doesn't have a public API, but we can try web scraping
            # This is just a placeholder - would need proper implementation
            logger.info(f"Attempting to fetch {symbol} from MoneyControl")
            # Implementation would go here
            return None
        except Exception as e:
            logger.error(f"Error fetching from MoneyControl: {e}")
            return None
    
    @classmethod
    def _fetch_from_bhavcopy(cls, symbol: str) -> Optional[float]:
        """Try to fetch SGB price from NSE/BSE bhavcopy"""
        try:
            # NSE publishes daily bhavcopy with all traded securities
            # This would need to download and parse the CSV
            logger.info(f"Attempting to fetch {symbol} from bhavcopy")
            # Implementation would go here
            return None
        except Exception as e:
            logger.error(f"Error fetching from bhavcopy: {e}")
            return None
    
    @classmethod
    def _get_cached_price(cls, symbol: str) -> Optional[float]:
        """Get price from cache if available and not expired"""
        if symbol in cls._price_cache:
            cached_data = cls._price_cache[symbol]
            if datetime.now() - cached_data['timestamp'] < cls._cache_duration:
                return cached_data['price']
        return None
    
    @classmethod
    def _cache_price(cls, symbol: str, price: float):
        """Cache the price with timestamp"""
        cls._price_cache[symbol] = {
            'price': price,
            'timestamp': datetime.now()
        }
    
    @classmethod
    def get_all_sgb_prices(cls) -> Dict[str, float]:
        """
        Get prices for all known SGBs
        Returns a dictionary of symbol: price
        """
        # Known SGB issues with approximate prices
        # These should be dynamically updated
        known_sgbs = {
            'SGBMAR29': 7600,
            'SGBDEC28': 7550,
            'SGBSEP28VI': 7500,
            'SGBAUG28': 7450,
            'SGBJUN28': 7400,
            'SGBMAR28': 7350,
            # Add more as needed
        }
        
        prices = {}
        for symbol, fallback_price in known_sgbs.items():
            price = cls.get_sgb_price(symbol)
            prices[symbol] = price or fallback_price
        
        return prices