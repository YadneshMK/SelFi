#!/usr/bin/env python3
"""
Script to update all mutual fund NAVs
"""
import sys
import os
import requests
from datetime import datetime

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

def update_mutual_fund_navs():
    """Update NAVs for all mutual funds with scheme codes"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all mutual funds with scheme codes
        result = conn.execute(text("""
            SELECT id, symbol, scheme_code, quantity, average_price
            FROM holdings
            WHERE asset_type IN ('MUTUAL_FUND', 'mutual_fund')
            AND scheme_code IS NOT NULL 
            AND scheme_code != ''
            ORDER BY symbol
        """))
        
        holdings = result.fetchall()
        print(f"Found {len(holdings)} mutual funds with scheme codes")
        
        updated_count = 0
        
        for holding in holdings:
            id, symbol, scheme_code, quantity, avg_price = holding
            
            try:
                print(f"\nUpdating: {symbol}")
                print(f"  Scheme code: {scheme_code}")
                
                # Fetch current NAV from MF API
                response = requests.get(f"https://api.mfapi.in/mf/{scheme_code}")
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and len(data['data']) > 0:
                        current_nav = float(data['data'][0]['nav'])
                        nav_date = data['data'][0]['date']
                        
                        # Calculate values
                        current_value = quantity * current_nav
                        pnl = current_value - (quantity * avg_price)
                        pnl_percentage = (pnl / (quantity * avg_price) * 100) if avg_price > 0 else 0
                        
                        # Update database
                        conn.execute(text("""
                            UPDATE holdings
                            SET current_price = :current_price,
                                current_value = :current_value,
                                pnl = :pnl,
                                pnl_percentage = :pnl_percentage,
                                last_updated = :last_updated
                            WHERE id = :id
                        """), {
                            "current_price": current_nav,
                            "current_value": current_value,
                            "pnl": pnl,
                            "pnl_percentage": pnl_percentage,
                            "last_updated": datetime.utcnow(),
                            "id": id
                        })
                        
                        print(f"  NAV updated: ₹{avg_price:.2f} → ₹{current_nav:.2f} (as of {nav_date})")
                        print(f"  P&L: ₹{pnl:,.2f} ({pnl_percentage:.2f}%)")
                        updated_count += 1
                    else:
                        print(f"  No NAV data available")
                else:
                    print(f"  API error: {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        conn.commit()
        print(f"\nUpdated {updated_count} mutual fund NAVs")

if __name__ == "__main__":
    update_mutual_fund_navs()