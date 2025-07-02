#!/usr/bin/env python3
"""
Clean up junk data and duplicates from holdings table
"""
import sqlite3
import re
from datetime import datetime

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Holdings Data Cleanup Script ===\n")

# 1. First, let's see what we're dealing with
cursor.execute("SELECT COUNT(*) FROM holdings")
total_before = cursor.fetchone()[0]
print(f"Total holdings before cleanup: {total_before}")

# 2. Delete obvious junk entries (Excel metadata, headers, etc.)
junk_patterns = [
    'REDEMPTION DETAILS',
    'SWITCH DETAILS',
    'Bank Name',
    'A/c No',
    'Amount ( )',
    'From Scheme',
    'To Scheme',
    'Note:',
    'If the bank',
    'Date /',
    'Units /',
    'I/We wish to',
    'Sign of'
]

print("\n--- Removing junk entries ---")
for pattern in junk_patterns:
    cursor.execute("""
        DELETE FROM holdings 
        WHERE symbol LIKE ? 
        OR symbol LIKE ?
    """, (f'%{pattern}%', f'{pattern}%'))
    if cursor.rowcount > 0:
        print(f"Removed {cursor.rowcount} entries containing '{pattern}'")

# 3. Remove entries with symbols that are clearly not valid
# (too long, contain newlines, etc.)
cursor.execute("""
    DELETE FROM holdings 
    WHERE length(symbol) > 50
    OR symbol LIKE '%\n%'
    OR symbol LIKE '%/%'
    OR symbol = ''
    OR symbol IS NULL
""")
print(f"\nRemoved {cursor.rowcount} entries with invalid symbol format")

# 4. Remove entries with zero quantity AND zero price
cursor.execute("""
    DELETE FROM holdings 
    WHERE quantity = 0 AND average_price = 0
""")
print(f"Removed {cursor.rowcount} entries with zero quantity and price")

# 5. Handle duplicates - keep the one with better data
print("\n--- Handling duplicates ---")

# Find duplicates
cursor.execute("""
    SELECT symbol, platform_account_id, COUNT(*) as count
    FROM holdings
    GROUP BY symbol, platform_account_id
    HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()

for symbol, account_id, count in duplicates:
    print(f"\nProcessing {count} duplicates for {symbol} in account {account_id}")
    
    # Get all entries for this duplicate
    cursor.execute("""
        SELECT id, quantity, average_price, current_price
        FROM holdings
        WHERE symbol = ? AND platform_account_id = ?
        ORDER BY 
            CASE WHEN average_price > 0 THEN 0 ELSE 1 END,  -- Prefer non-zero price
            CASE WHEN quantity > 0 THEN 0 ELSE 1 END,       -- Prefer non-zero quantity
            id DESC  -- Prefer newer entries
    """, (symbol, account_id))
    
    entries = cursor.fetchall()
    
    # Keep the first (best) entry, delete the rest
    keep_id = entries[0][0]
    delete_ids = [entry[0] for entry in entries[1:]]
    
    if delete_ids:
        cursor.execute(f"""
            DELETE FROM holdings 
            WHERE id IN ({','.join('?' * len(delete_ids))})
        """, delete_ids)
        print(f"  Kept entry {keep_id}, deleted {len(delete_ids)} duplicates")

# 6. Clean up symbols (remove extra spaces, standardize)
print("\n--- Cleaning up symbol names ---")
cursor.execute("""
    UPDATE holdings
    SET symbol = TRIM(symbol)
    WHERE symbol != TRIM(symbol)
""")
print(f"Trimmed whitespace from {cursor.rowcount} symbols")

# 7. Final check
cursor.execute("SELECT COUNT(*) FROM holdings")
total_after = cursor.fetchone()[0]

print(f"\n=== Cleanup Complete ===")
print(f"Holdings before: {total_before}")
print(f"Holdings after: {total_after}")
print(f"Removed: {total_before - total_after} entries")

# Show remaining holdings
print("\n--- Remaining holdings preview ---")
cursor.execute("""
    SELECT symbol, asset_type, quantity, average_price
    FROM holdings
    ORDER BY asset_type, symbol
    LIMIT 20
""")

for row in cursor.fetchall():
    symbol, asset_type, qty, price = row
    print(f"{asset_type:12} | {symbol:40} | Qty: {qty:8.2f} | Price: {price:10.2f}")

# Commit changes
conn.commit()
conn.close()

print("\nDatabase cleaned successfully!")