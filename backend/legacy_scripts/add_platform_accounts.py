#!/usr/bin/env python3
"""
Script to add platform accounts for different portfolios
"""
import sqlite3

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing accounts
print("Existing platform accounts:")
cursor.execute("SELECT id, user_id, platform, client_id, nickname FROM platform_accounts")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, User: {row[1]}, Platform: {row[2]}, Client: {row[3]}, Nickname: {row[4]}")

# Add new platform accounts for user_id 1
new_accounts = [
    (1, 1, 'ZERODHA', 'BHB965-MF', 'Mutual Funds Account', 'DEMAT', True),
    (1, 1, 'ZERODHA', 'BHB965-ETF', 'ETF Account', 'DEMAT', True),
    (1, 1, 'GROWW', 'GROWW001', 'Groww Account', 'DEMAT', True),
    (1, 1, 'UPSTOX', 'UPSTOX001', 'Upstox Account', 'DEMAT', True),
]

print("\nAdding new platform accounts...")
for user_id, pan_id, platform, client_id, nickname, account_type, is_active in new_accounts:
    # Check if account already exists
    cursor.execute("""
        SELECT id FROM platform_accounts 
        WHERE user_id = ? AND client_id = ?
    """, (user_id, client_id))
    
    if cursor.fetchone():
        print(f"  Account {client_id} already exists, skipping...")
        continue
    
    cursor.execute("""
        INSERT INTO platform_accounts (user_id, pan_id, platform, client_id, nickname, account_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, pan_id, platform, client_id, nickname, account_type, is_active))
    print(f"  Added: {nickname} ({platform} - {client_id})")

conn.commit()

# Show all accounts after addition
print("\nAll platform accounts after addition:")
cursor.execute("SELECT id, user_id, platform, client_id, nickname FROM platform_accounts WHERE user_id = 1")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Platform: {row[2]}, Client: {row[3]}, Nickname: {row[4]}")

conn.close()
print("\nDone! You can now select different accounts when uploading holdings.")