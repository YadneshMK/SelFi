#!/usr/bin/env python3
"""
Script to reassign existing holdings to appropriate platform accounts based on asset type
"""
import sqlite3

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Reassigning Holdings to Appropriate Platform Accounts ===\n")

# First, let's see the current distribution
print("Current holdings distribution:")
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

# Get the platform account IDs
account_mapping = {}
cursor.execute("SELECT id, nickname FROM platform_accounts WHERE user_id = 1")
for row in cursor.fetchall():
    account_mapping[row[1]] = row[0]

print(f"\nAvailable accounts: {list(account_mapping.keys())}")

# Define reassignment rules
reassignment_rules = {
    'MUTUAL_FUND': account_mapping.get('Mutual Funds Account', 4),
    'ETF': account_mapping.get('ETF Account', 5),
    'STOCK': account_mapping.get('Main Account', 1),
    'SGB': account_mapping.get('Main Account', 1)  # Keep SGBs in main account
}

print("\nReassignment plan:")
for asset_type, account_id in reassignment_rules.items():
    account_name = next((k for k, v in account_mapping.items() if v == account_id), 'Unknown')
    print(f"  {asset_type} → {account_name} (ID: {account_id})")

# Perform reassignment
print("\nReassigning holdings...")
for asset_type, new_account_id in reassignment_rules.items():
    cursor.execute("""
        UPDATE holdings
        SET platform_account_id = ?
        WHERE asset_type = ? 
        AND platform_account_id IN (
            SELECT id FROM platform_accounts WHERE user_id = 1
        )
    """, (new_account_id, asset_type))
    
    affected_rows = cursor.rowcount
    if affected_rows > 0:
        print(f"  Moved {affected_rows} {asset_type} holdings to account {new_account_id}")

# Commit changes
conn.commit()

# Show final distribution
print("\nFinal holdings distribution:")
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

# Show summary by platform account
print("\nSummary by platform account:")
cursor.execute("""
    SELECT pa.nickname, COUNT(*) as total_holdings
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 1
    GROUP BY pa.nickname
    ORDER BY pa.nickname
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} total holdings")

conn.close()
print("\nReassignment complete! Refresh your holdings page to see the changes.")