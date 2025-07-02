#!/usr/bin/env python3
"""
Consolidate duplicate holdings
"""
import sqlite3

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Consolidating Duplicate Holdings ===\n")

# Find all duplicates
cursor.execute("""
    SELECT symbol, asset_type, COUNT(*) as count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 1
    GROUP BY symbol, asset_type
    HAVING COUNT(*) > 1
    ORDER BY count DESC, symbol
""")
duplicates = cursor.fetchall()

print(f"Found {len(duplicates)} symbols with duplicates")

total_removed = 0
for symbol, asset_type, count in duplicates:
    print(f"\nProcessing {symbol} ({asset_type}) - {count} entries")
    
    # Get all entries for this symbol
    cursor.execute("""
        SELECT id, quantity, average_price, current_price
        FROM holdings
        WHERE symbol = ? AND asset_type = ?
        AND platform_account_id IN (
            SELECT id FROM platform_accounts WHERE user_id = 1
        )
        ORDER BY 
            CASE WHEN quantity > 1 THEN 0 ELSE 1 END,  -- Prefer entries with quantity > 1
            CASE WHEN average_price > 0 THEN 0 ELSE 1 END,  -- Prefer non-zero price
            id DESC  -- Prefer newer entries
    """, (symbol, asset_type))
    
    entries = cursor.fetchall()
    
    # Consolidate quantities and calculate weighted average price
    total_quantity = 0
    total_value = 0
    best_current_price = 0
    
    for entry_id, qty, avg_price, curr_price in entries:
        total_quantity += qty
        total_value += qty * avg_price
        if curr_price > best_current_price:
            best_current_price = curr_price
    
    weighted_avg_price = total_value / total_quantity if total_quantity > 0 else entries[0][2]
    
    # Keep the first (best) entry and update it with consolidated values
    keep_id = entries[0][0]
    cursor.execute("""
        UPDATE holdings
        SET quantity = ?,
            average_price = ?,
            current_price = ?,
            current_value = ? * ?,
            pnl = (? - ?) * ?,
            pnl_percentage = CASE 
                WHEN ? > 0 THEN ((? - ?) / ? * 100)
                ELSE 0
            END
        WHERE id = ?
    """, (total_quantity, weighted_avg_price, best_current_price,
          total_quantity, best_current_price,
          best_current_price, weighted_avg_price, total_quantity,
          weighted_avg_price, best_current_price, weighted_avg_price, weighted_avg_price,
          keep_id))
    
    # Delete the rest
    delete_ids = [entry[0] for entry in entries[1:]]
    if delete_ids:
        placeholders = ','.join('?' * len(delete_ids))
        cursor.execute(f"DELETE FROM holdings WHERE id IN ({placeholders})", delete_ids)
        removed = len(delete_ids)
        total_removed += removed
        print(f"  Consolidated into holding {keep_id}: Qty={total_quantity:.2f}, Avg Price={weighted_avg_price:.2f}")
        print(f"  Removed {removed} duplicate entries")

# Commit changes
conn.commit()

print(f"\n=== Consolidation Complete ===")
print(f"Total duplicate entries removed: {total_removed}")

# Show final counts
cursor.execute("""
    SELECT asset_type, COUNT(*) as count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 1
    GROUP BY asset_type
    ORDER BY asset_type
""")
print("\nFinal holdings count by type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} holdings")

cursor.execute("SELECT COUNT(*) FROM holdings h JOIN platform_accounts pa ON h.platform_account_id = pa.id WHERE pa.user_id = 1")
total = cursor.fetchone()[0]
print(f"\nTotal holdings: {total}")

conn.close()
print("\nDone! All duplicates have been consolidated.")