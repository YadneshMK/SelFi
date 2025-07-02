#!/usr/bin/env python3
"""
Script to consolidate duplicate holdings for the same symbol
"""
import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings

def consolidate_duplicate_holdings():
    """Consolidate holdings with the same symbol and platform account"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Find duplicate holdings (same symbol, same platform account)
        result = conn.execute(text("""
            SELECT symbol, platform_account_id, COUNT(*) as count
            FROM holdings
            GROUP BY symbol, platform_account_id
            HAVING COUNT(*) > 1
            ORDER BY symbol
        """))
        
        duplicates = result.fetchall()
        print(f"Found {len(duplicates)} symbols with duplicate holdings")
        
        for symbol, platform_account_id, count in duplicates:
            print(f"\nProcessing {count} holdings for: {symbol}")
            
            # Get all holdings for this symbol and account
            holdings_result = conn.execute(text("""
                SELECT id, quantity, average_price, current_price
                FROM holdings
                WHERE symbol = :symbol AND platform_account_id = :platform_account_id
                ORDER BY id
            """), {"symbol": symbol, "platform_account_id": platform_account_id})
            
            holdings = holdings_result.fetchall()
            
            # Calculate consolidated values
            total_quantity = 0
            total_invested = 0
            latest_price = 0
            
            for holding in holdings:
                id, quantity, avg_price, current_price = holding
                total_quantity += quantity
                total_invested += quantity * avg_price
                if current_price:
                    latest_price = current_price
                print(f"  - ID {id}: {quantity} units @ ₹{avg_price:.2f}")
            
            # Calculate weighted average price
            weighted_avg_price = total_invested / total_quantity if total_quantity > 0 else 0
            
            print(f"  Total: {total_quantity} units @ ₹{weighted_avg_price:.2f} (invested: ₹{total_invested:.2f})")
            
            # Keep the first holding and update it with consolidated values
            first_id = holdings[0][0]
            
            # Update the first holding
            conn.execute(text("""
                UPDATE holdings
                SET quantity = :quantity,
                    average_price = :average_price,
                    current_price = :current_price,
                    current_value = :current_value,
                    pnl = :pnl,
                    pnl_percentage = :pnl_percentage
                WHERE id = :id
            """), {
                "id": first_id,
                "quantity": total_quantity,
                "average_price": weighted_avg_price,
                "current_price": latest_price,
                "current_value": total_quantity * latest_price if latest_price else None,
                "pnl": (total_quantity * latest_price - total_invested) if latest_price else None,
                "pnl_percentage": ((total_quantity * latest_price - total_invested) / total_invested * 100) if latest_price and total_invested > 0 else None
            })
            
            # Delete the duplicate holdings
            for i in range(1, len(holdings)):
                holding_id = holdings[i][0]
                conn.execute(text("DELETE FROM holdings WHERE id = :id"), {"id": holding_id})
                print(f"  Deleted duplicate holding ID {holding_id}")
        
        conn.commit()
        print(f"\nConsolidation complete!")

if __name__ == "__main__":
    consolidate_duplicate_holdings()