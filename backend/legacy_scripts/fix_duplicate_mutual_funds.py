#!/usr/bin/env python3
"""
Script to fix duplicate mutual fund entries that were incorrectly imported
"""
import sys
import os
import re

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

def find_and_fix_duplicates():
    """Find and remove duplicate mutual fund entries"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Find mutual funds that have exchange='NSE' (these are incorrect)
        result = conn.execute(text("""
            SELECT id, symbol, asset_type, exchange, quantity, average_price, platform_account_id
            FROM holdings 
            WHERE asset_type IN ('MUTUAL_FUND', 'mutual_fund') 
            AND exchange = 'NSE'
            ORDER BY symbol
        """))
        
        incorrect_holdings = result.fetchall()
        print(f"Found {len(incorrect_holdings)} mutual funds incorrectly marked as NSE stocks")
        
        duplicates_to_remove = []
        
        for holding in incorrect_holdings:
            id, symbol, asset_type, exchange, quantity, avg_price, platform_account_id = holding
            
            # Try to find a matching correct entry
            # First, clean the symbol to create a searchable pattern
            # Remove all non-alphanumeric characters for comparison
            clean_symbol = re.sub(r'[^A-Za-z0-9]', '', symbol)
            
            # Look for the correct version with proper formatting
            correct_result = conn.execute(text("""
                SELECT id, symbol, quantity, average_price
                FROM holdings 
                WHERE asset_type IN ('MUTUAL_FUND', 'mutual_fund')
                AND exchange = 'MF'
                AND platform_account_id = :platform_account_id
                AND REPLACE(REPLACE(REPLACE(REPLACE(UPPER(symbol), ' ', ''), '-', ''), '.', ''), '&', '') = :clean_symbol
            """), {
                "platform_account_id": platform_account_id,
                "clean_symbol": clean_symbol.upper()
            })
            
            correct_holding = correct_result.fetchone()
            
            if correct_holding:
                correct_id, correct_symbol, correct_quantity, correct_avg_price = correct_holding
                print(f"\nFound duplicate:")
                print(f"  Incorrect: ID={id}, Symbol='{symbol}', Exchange={exchange}")
                print(f"  Correct:   ID={correct_id}, Symbol='{correct_symbol}', Exchange=MF")
                
                # If quantities match, it's definitely a duplicate
                if abs(quantity - correct_quantity) < 0.001:
                    print(f"  -> Quantities match ({quantity}), marking for removal")
                    duplicates_to_remove.append(id)
                else:
                    print(f"  -> Different quantities ({quantity} vs {correct_quantity}), keeping both")
            else:
                # No matching correct entry found, just fix the exchange
                print(f"\nNo correct version found for: {symbol}")
                print(f"  -> Updating exchange from NSE to MF")
                conn.execute(text("""
                    UPDATE holdings 
                    SET exchange = 'MF'
                    WHERE id = :id
                """), {"id": id})
        
        # Remove duplicates
        if duplicates_to_remove:
            print(f"\nRemoving {len(duplicates_to_remove)} duplicate entries...")
            for holding_id in duplicates_to_remove:
                conn.execute(text("""
                    DELETE FROM holdings 
                    WHERE id = :id
                """), {"id": holding_id})
        
        conn.commit()
        print(f"\nFixed {len(incorrect_holdings)} mutual fund entries")
        print(f"Removed {len(duplicates_to_remove)} duplicates")

if __name__ == "__main__":
    find_and_fix_duplicates()