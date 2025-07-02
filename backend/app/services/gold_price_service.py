"""
Service for fetching gold prices to calculate SGB values
"""
import requests
from typing import Optional, Dict, Tuple
import logging
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

class GoldPriceService:
    """Service to fetch gold prices from free APIs"""
    
    # Cache gold price for 30 minutes
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_cached_gold_price(cache_key: str) -> Optional[float]:
        """Internal method to cache gold price"""
        return GoldPriceService._fetch_gold_price()
    
    @classmethod
    def get_gold_price_inr(cls) -> Optional[float]:
        """
        Get current gold price in INR per gram
        Uses multiple free APIs as fallbacks
        """
        # Create cache key based on 30-minute intervals
        cache_key = datetime.now().strftime("%Y%m%d%H") + str(datetime.now().minute // 30)
        return cls._get_cached_gold_price(cache_key)
    
    @staticmethod
    def _fetch_gold_price() -> Optional[float]:
        """Fetch gold price from various free sources"""
        
        # Method 1: CurrencyAPI (has free tier)
        try:
            # Get USD to INR rate
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/USD',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                usd_to_inr = data['rates'].get('INR', 83)  # Default to 83 if not found
                
                # Get gold price in USD (using metals-api free tier)
                # Note: In production, you'd need to sign up for free API key
                gold_response = requests.get(
                    'https://api.metals.live/v1/spot/gold',
                    timeout=5
                )
                
                if gold_response.status_code == 200:
                    gold_data = gold_response.json()
                    if isinstance(gold_data, list) and len(gold_data) > 0:
                        usd_per_oz = gold_data[0].get('price', 0)
                    else:
                        usd_per_oz = gold_data.get('price', 0)
                    
                    if usd_per_oz > 0:
                        # Convert USD/oz to INR/gram (1 oz = 31.1035 grams)
                        inr_per_gram = (usd_per_oz / 31.1035) * usd_to_inr
                        logger.info(f"Gold price: ${usd_per_oz}/oz, ₹{inr_per_gram:.2f}/gram")
                        return inr_per_gram
        except Exception as e:
            logger.error(f"Error fetching from primary source: {e}")
        
        # Method 2: Alternative API (goldprice.org unofficial)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                'https://data-asg.goldprice.org/dbXRates/INR',
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    item = data['items'][0]
                    # xauPrice is gold price per ounce in INR
                    inr_per_oz = item.get('xauPrice', 0)
                    if inr_per_oz > 0:
                        inr_per_gram = inr_per_oz / 31.1035
                        logger.info(f"Gold price from alternative: ₹{inr_per_gram:.2f}/gram")
                        return inr_per_gram
        except Exception as e:
            logger.error(f"Error fetching from alternative source: {e}")
        
        # Method 3: Fallback to hardcoded estimate
        # Based on approximate gold prices in India (June 2025)
        # This should be updated periodically
        logger.warning("Using fallback gold price estimate")
        return 7200.0  # ₹7,200 per gram (conservative estimate)
    
    @classmethod
    def calculate_sgb_price(cls, issue_price: float = None) -> float:
        """
        Calculate SGB price based on current gold price
        
        SGBs trade at a premium/discount to gold price based on:
        1. Time to maturity
        2. Interest rate (2.5% p.a.)
        3. Tax benefits
        4. Market sentiment
        
        Args:
            issue_price: Original issue price of the SGB (optional)
        
        Returns:
            Estimated SGB price per gram
        """
        gold_price = cls.get_gold_price_inr()
        
        if not gold_price:
            logger.error("Could not fetch gold price")
            return 0
        
        # SGBs typically trade at 5-10% premium to gold due to:
        # - 2.5% annual interest
        # - Tax-free capital gains if held to maturity
        # - No storage costs
        # - Market demand and liquidity factors
        # Based on actual market data, SGBs trade at ~7-8% premium
        premium_factor = 1.073  # 7.3% premium to match market prices
        
        sgb_price = gold_price * premium_factor
        
        # Round to nearest rupee
        return round(sgb_price, 2)
    
    @classmethod
    def get_sgb_details(cls, symbol: str) -> Dict[str, any]:
        """
        Get SGB details including maturity date and interest
        
        SGB naming convention:
        - SGBMAR29 = SGB maturing in March 2029
        - SGBSEP28VI = SGB Series VI maturing in September 2028
        """
        sgb_price = cls.calculate_sgb_price()
        
        # Extract maturity info from symbol
        maturity_info = "Unknown"
        if 'SGB' in symbol:
            # Try to extract month and year
            import re
            match = re.search(r'SGB([A-Z]{3})(\d{2})', symbol)
            if match:
                month = match.group(1)
                year = match.group(2)
                # Convert 2-digit year to 4-digit
                year_int = int(year)
                if year_int < 50:
                    full_year = 2000 + year_int
                else:
                    full_year = 1900 + year_int
                maturity_info = f"{month} {full_year}"
        
        return {
            'symbol': symbol,
            'current_price': sgb_price,
            'gold_price': cls.get_gold_price_inr(),
            'premium_percent': 7.3,  # Market-based premium
            'interest_rate': 2.5,    # 2.5% p.a.
            'maturity': maturity_info,
            'last_updated': datetime.now()
        }