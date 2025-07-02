#!/usr/bin/env python3
"""
Fix holdings assigned to wrong user
"""
import sqlite3

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Fixing Holdings User Assignment ===\n")

# Show current situation
print("Current holdings distribution by user:")
cursor.execute("""
    SELECT pa.user_id, COUNT(*) as holdings_count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    GROUP BY pa.user_id
""")
for row in cursor.fetchall():
    print(f"  User {row[0]}: {row[1]} holdings")

# Get all holdings from user 2's accounts
cursor.execute("""
    SELECT h.id, h.symbol, h.asset_type, h.platform_account_id, pa.nickname
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 2
""")
user2_holdings = cursor.fetchall()

print(f"\nFound {len(user2_holdings)} holdings in User 2's accounts that need to be moved")

# Map each holding to the correct account for user 1
account_mapping = {
    'STOCK': 1,        # Main Account
    'ETF': 5,          # ETF Account
    'MUTUAL_FUND': 4,  # Mutual Funds Account
    'SGB': 1,          # Main Account
    'REIT': 8          # REITs Account
}

# Move holdings to user 1's accounts
moved_count = 0
for holding_id, symbol, asset_type, old_account_id, old_account_name in user2_holdings:
    new_account_id = account_mapping.get(asset_type, 1)
    cursor.execute("""
        UPDATE holdings
        SET platform_account_id = ?
        WHERE id = ?
    """, (new_account_id, holding_id))
    moved_count += 1
    print(f"  Moved {symbol} ({asset_type}) from '{old_account_name}' to account {new_account_id}")

print(f"\nMoved {moved_count} holdings to User 1's accounts")

# Commit changes
conn.commit()

# Show final distribution
print("\nFinal holdings distribution by user:")
cursor.execute("""
    SELECT pa.user_id, COUNT(*) as holdings_count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    GROUP BY pa.user_id
""")
for row in cursor.fetchall():
    print(f"  User {row[0]}: {row[1]} holdings")

print("\nHoldings by platform account (User 1 only):")
cursor.execute("""
    SELECT pa.nickname, h.asset_type, COUNT(*) as count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 1
    GROUP BY pa.nickname, h.asset_type
    ORDER BY pa.nickname, h.asset_type
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} - {row[2]} holdings")

conn.close()
print("\nDone! All holdings are now assigned to User 1's accounts.")