#!/usr/bin/env python3
"""
Script to fix concatenated mutual fund symbols
"""
import sys
import os
import re

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_spaces_to_symbol(symbol):
    """Add spaces to concatenated symbol names"""
    # Add space before capital letters (except the first one)
    spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', symbol)
    
    # Fix common patterns
    spaced = spaced.replace('ELSS TAX SAVER FUND', 'ELSS TAX SAVER FUND')
    spaced = spaced.replace('FLEXI CAP FUND', 'FLEXI CAP FUND')
    spaced = spaced.replace('DIRECT PLAN', 'DIRECT PLAN')
    
    # Clean up any double spaces
    spaced = ' '.join(spaced.split())
    
    # Fix specific cases
    if 'PARAGPARIKH' in symbol:
        spaced = spaced.replace('PARAGPARIKH', 'PARAG PARIKH')
    if 'DIRECTPLAN' in symbol:
        spaced = spaced.replace('DIRECTPLAN', 'DIRECT PLAN')
    if 'FLEXICAP' in symbol:
        spaced = spaced.replace('FLEXICAP', 'FLEXI CAP')
    if 'ELSSTAXSAVER' in symbol:
        spaced = spaced.replace('ELSSTAXSAVER', 'ELSS TAX SAVER')
        
    # Add hyphens where appropriate
    spaced = re.sub(r'(FUND)\s+(DIRECT)', r'\1 - \2', spaced)
    
    return spaced

def fix_concatenated_symbols():
    """Fix all concatenated mutual fund symbols"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all mutual funds with concatenated symbols (no spaces)
        result = conn.execute(text("""
            SELECT id, symbol 
            FROM holdings 
            WHERE asset_type IN ('MUTUAL_FUND', 'mutual_fund')
            AND symbol NOT LIKE '% %'
            AND LENGTH(symbol) > 15
        """))
        
        holdings = result.fetchall()
        print(f"Found {len(holdings)} mutual funds with concatenated symbols")
        
        fixed_count = 0
        for holding in holdings:
            id, symbol = holding
            fixed_symbol = add_spaces_to_symbol(symbol)
            
            if fixed_symbol != symbol:
                print(f"\nFixing holding {id}:")
                print(f"  Original: {symbol}")
                print(f"  Fixed:    {fixed_symbol}")
                
                # Update the database
                conn.execute(text("""
                    UPDATE holdings 
                    SET symbol = :symbol 
                    WHERE id = :id
                """), {"symbol": fixed_symbol, "id": id})
                
                fixed_count += 1
        
        conn.commit()
        print(f"\nFixed {fixed_count} concatenated symbols")

if __name__ == "__main__":
    fix_concatenated_symbols()