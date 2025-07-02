#!/usr/bin/env python3
"""
Script to fix ETF duplicate entries and standardize symbols
"""
import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

# ETF symbol mappings (from broker format to standard symbol)
ETF_MAPPINGS = {
    'MAFSETFINAV': 'MAFSETF',
    'MOM100INAV': 'MOM100',
    'SETFNIF50': 'SETFNN50',
    'LIQUIDBEESINAV': 'LIQUIDBEES',
    'GOLDBEESINAV': 'GOLDBEES',
    'NIFTYBEESINAV': 'NIFTYBEES',
    'BANKBEESINAV': 'BANKBEES',
    'JUNIORBEESINAV': 'JUNIORBEES',
}

def fix_etf_duplicates():
    """Fix ETF duplicates and standardize symbols"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # First, fix symbol names for ETFs with INAV suffix
        for old_symbol, new_symbol in ETF_MAPPINGS.items():
            # Check if the old symbol exists
            result = conn.execute(text("""
                SELECT id, symbol, quantity, average_price, platform_account_id
                FROM holdings
                WHERE symbol = :old_symbol
            """), {"old_symbol": old_symbol})
            
            old_holding = result.fetchone()
            
            if old_holding:
                old_id, _, old_quantity, old_avg_price, platform_account_id = old_holding
                
                # Check if the new symbol already exists for the same account
                result = conn.execute(text("""
                    SELECT id, quantity, average_price
                    FROM holdings
                    WHERE symbol = :new_symbol 
                    AND platform_account_id = :platform_account_id
                """), {"new_symbol": new_symbol, "platform_account_id": platform_account_id})
                
                new_holding = result.fetchone()
                
                if new_holding:
                    # Duplicate exists - consolidate
                    new_id, new_quantity, new_avg_price = new_holding
                    
                    print(f"\nFound duplicate ETF:")
                    print(f"  Old: {old_symbol} (ID={old_id}): {old_quantity} @ ₹{old_avg_price}")
                    print(f"  New: {new_symbol} (ID={new_id}): {new_quantity} @ ₹{new_avg_price}")
                    
                    # Calculate consolidated values
                    total_quantity = old_quantity + new_quantity
                    total_invested = (old_quantity * old_avg_price) + (new_quantity * new_avg_price)
                    weighted_avg_price = total_invested / total_quantity if total_quantity > 0 else 0
                    
                    print(f"  Consolidating to: {total_quantity} @ ₹{weighted_avg_price:.3f}")
                    
                    # Update the correct symbol entry
                    conn.execute(text("""
                        UPDATE holdings
                        SET quantity = :quantity,
                            average_price = :average_price
                        WHERE id = :id
                    """), {
                        "id": new_id,
                        "quantity": total_quantity,
                        "average_price": weighted_avg_price
                    })
                    
                    # Delete the old entry
                    conn.execute(text("DELETE FROM holdings WHERE id = :id"), {"id": old_id})
                    print(f"  Deleted {old_symbol} entry")
                    
                else:
                    # No duplicate - just rename the symbol
                    print(f"\nRenaming {old_symbol} to {new_symbol}")
                    conn.execute(text("""
                        UPDATE holdings
                        SET symbol = :new_symbol
                        WHERE id = :id
                    """), {"new_symbol": new_symbol, "id": old_id})
        
        conn.commit()
        print("\nETF duplicate fix complete!")

if __name__ == "__main__":
    fix_etf_duplicates()