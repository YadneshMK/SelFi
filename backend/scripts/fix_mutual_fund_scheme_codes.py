#!/usr/bin/env python3
"""
Script to find and populate missing mutual fund scheme codes
"""
import sys
import os
import requests

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

# Known mutual fund to scheme code mappings
KNOWN_SCHEME_CODES = {
    'PARAG PARIKH FLEXI CAP FUND - DIRECT PLAN': '122639',
    'PARAG PARIKH ELSS TAX SAVER FUND - DIRECT PLAN': '138683',  # Already has INF879O01100
    'TATA DIGITAL INDIA FUND DIRECT PLAN GROWTH': '135798',
    'MIRAE ASSET ELSS TAX SAVER FUND - DIRECT PLAN': '147251',  # Already has INF769K01DM9
    'SBI SMALL CAP FUND - DIRECT PLAN': '125494',  # Already has INF200K01T51
}

def search_scheme_code(fund_name):
    """Search for scheme code using MF API"""
    try:
        # Clean the fund name
        search_query = fund_name.replace(' - ', ' ').replace('  ', ' ')
        
        # Search using MF API
        response = requests.get("https://api.mfapi.in/mf/search", params={"q": search_query})
        if response.status_code == 200:
            results = response.json()
            
            # Try to find exact or close match
            for result in results:
                scheme_name = result.get('schemeName', '').upper()
                scheme_code = result.get('schemeCode')
                
                # Check if it's a good match
                if 'DIRECT' in fund_name.upper() and 'DIRECT' in scheme_name:
                    if all(word in scheme_name for word in fund_name.upper().split()[:3]):
                        return scheme_code
                elif 'REGULAR' in fund_name.upper() and 'REGULAR' in scheme_name:
                    if all(word in scheme_name for word in fund_name.upper().split()[:3]):
                        return scheme_code
            
            # If no exact match, return first result if available
            if results:
                print(f"  No exact match, using first result: {results[0].get('schemeName')}")
                return results[0].get('schemeCode')
    except Exception as e:
        print(f"  Error searching for scheme code: {e}")
    
    return None

def fix_mutual_fund_scheme_codes():
    """Find and fix missing scheme codes for mutual funds"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all mutual funds without scheme codes
        result = conn.execute(text("""
            SELECT id, symbol, scheme_code
            FROM holdings
            WHERE asset_type IN ('MUTUAL_FUND', 'mutual_fund')
            AND (scheme_code IS NULL OR scheme_code = '')
            ORDER BY symbol
        """))
        
        holdings = result.fetchall()
        print(f"Found {len(holdings)} mutual funds without scheme codes")
        
        fixed_count = 0
        
        for holding in holdings:
            id, symbol, _ = holding
            print(f"\nProcessing: {symbol}")
            
            # First check known mappings
            scheme_code = None
            symbol_upper = symbol.upper()
            
            for known_name, known_code in KNOWN_SCHEME_CODES.items():
                if known_name in symbol_upper or symbol_upper in known_name:
                    scheme_code = known_code
                    print(f"  Found in known mappings: {scheme_code}")
                    break
            
            # If not found in known mappings, search API
            if not scheme_code:
                print(f"  Searching MF API...")
                scheme_code = search_scheme_code(symbol)
                if scheme_code:
                    print(f"  Found via API: {scheme_code}")
            
            if scheme_code:
                # Update the database
                conn.execute(text("""
                    UPDATE holdings
                    SET scheme_code = :scheme_code
                    WHERE id = :id
                """), {"scheme_code": scheme_code, "id": id})
                
                # Now update the current NAV
                try:
                    response = requests.get(f"https://api.mfapi.in/mf/{scheme_code}")
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and len(data['data']) > 0:
                            current_nav = float(data['data'][0]['nav'])
                            
                            # Get quantity and average price
                            holding_data = conn.execute(text("""
                                SELECT quantity, average_price
                                FROM holdings
                                WHERE id = :id
                            """), {"id": id}).fetchone()
                            
                            if holding_data:
                                quantity, avg_price = holding_data
                                current_value = quantity * current_nav
                                pnl = current_value - (quantity * avg_price)
                                pnl_percentage = (pnl / (quantity * avg_price) * 100) if avg_price > 0 else 0
                                
                                conn.execute(text("""
                                    UPDATE holdings
                                    SET current_price = :current_price,
                                        current_value = :current_value,
                                        pnl = :pnl,
                                        pnl_percentage = :pnl_percentage
                                    WHERE id = :id
                                """), {
                                    "current_price": current_nav,
                                    "current_value": current_value,
                                    "pnl": pnl,
                                    "pnl_percentage": pnl_percentage,
                                    "id": id
                                })
                                
                                print(f"  Updated NAV: ₹{current_nav} (was ₹{avg_price})")
                
                except Exception as e:
                    print(f"  Error updating NAV: {e}")
                
                fixed_count += 1
            else:
                print(f"  Could not find scheme code")
        
        conn.commit()
        print(f"\nFixed {fixed_count} mutual fund scheme codes")

if __name__ == "__main__":
    fix_mutual_fund_scheme_codes()