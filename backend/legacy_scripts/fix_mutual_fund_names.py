#!/usr/bin/env python3
"""
Script to fix malformed mutual fund names in the database
"""
import sys
import os
import re

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

def clean_mutual_fund_name(name):
    """Clean mutual fund name by removing dates, NAV values, and codes"""
    if not name:
        return name
        
    # Remove date patterns (various formats)
    date_patterns = [
        r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',  # 27-Jun-2025
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # 27/06/2025 or 27-06-2025
        r'\w{3}\s+\d{1,2}\s+\d{2,4}',  # Jun 27 2025
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2025-06-27
    ]
    
    for pattern in date_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove NAV values (decimal numbers)
    name = re.sub(r'\b\d+\.\d+\b', '', name)
    
    # Remove standalone numbers (like scheme codes)
    name = re.sub(r'\b\d{2,}\b', '', name)
    
    # Clean up extra spaces
    name = ' '.join(name.split())
    
    # Remove trailing spaces
    name = name.strip()
    
    return name

def fix_mutual_fund_names():
    """Fix all mutual fund names in the database"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all mutual fund holdings
        result = conn.execute(text("""
            SELECT id, symbol 
            FROM holdings 
            WHERE asset_type = 'MUTUAL_FUND' OR asset_type = 'mutual_fund'
        """))
        
        holdings = result.fetchall()
        print(f"Found {len(holdings)} mutual fund holdings")
        
        fixed_count = 0
        for holding in holdings:
            id, symbol = holding
            cleaned_name = clean_mutual_fund_name(symbol)
            
            if cleaned_name != symbol:
                print(f"\nFixing holding {id}:")
                print(f"  Original: {symbol}")
                print(f"  Cleaned:  {cleaned_name}")
                
                # Update the database
                conn.execute(text("""
                    UPDATE holdings 
                    SET symbol = :symbol 
                    WHERE id = :id
                """), {"symbol": cleaned_name, "id": id})
                
                fixed_count += 1
        
        conn.commit()
        print(f"\nFixed {fixed_count} mutual fund names")

if __name__ == "__main__":
    fix_mutual_fund_names()