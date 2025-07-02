#!/usr/bin/env python3
"""
Script to update SGB prices manually
Since SGBs are not available on Yahoo Finance, we need to update them manually
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

# SGB prices (as of June 2025)
# These need to be updated manually based on market prices
# SGBs trade based on gold prices + interest benefits
SGB_PRICES = {
    'SGBSEP28VI-GB': 9659.39,  # Current market price as of June 2025
    'SGBAUG28': 9625.00,  # Update with actual prices
    'SGBMAR29': 9700.00,  # Update with actual prices
    # Add more SGBs as needed
}

def update_sgb_prices():
    """Update SGB prices manually"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all SGB holdings
        result = conn.execute(text("""
            SELECT id, symbol, quantity, average_price
            FROM holdings
            WHERE asset_type IN ('SGB', 'sgb')
            ORDER BY symbol
        """))
        
        holdings = result.fetchall()
        print(f"Found {len(holdings)} SGB holdings")
        
        updated_count = 0
        
        for holding in holdings:
            id, symbol, quantity, avg_price = holding
            
            # Check if we have a price for this SGB
            current_price = SGB_PRICES.get(symbol)
            
            if current_price:
                print(f"\nUpdating {symbol}:")
                print(f"  Current Price: ₹{current_price}")
                
                # Calculate values
                current_value = quantity * current_price
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
                    "current_price": current_price,
                    "current_value": current_value,
                    "pnl": pnl,
                    "pnl_percentage": pnl_percentage,
                    "last_updated": datetime.utcnow(),
                    "id": id
                })
                
                print(f"  Average Price: ₹{avg_price}")
                print(f"  P&L: ₹{pnl:,.2f} ({pnl_percentage:.2f}%)")
                updated_count += 1
            else:
                print(f"\nNo price available for {symbol}")
                print("  Please add the current market price to SGB_PRICES dictionary")
        
        conn.commit()
        print(f"\nUpdated {updated_count} SGB prices")

if __name__ == "__main__":
    update_sgb_prices()