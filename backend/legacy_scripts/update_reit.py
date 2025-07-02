#!/usr/bin/env python3
"""
Update MINDSPACE-RR to REIT asset type
"""
import sqlite3

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Updating REIT Asset Type ===\n")

# Check current status of MINDSPACE-RR
cursor.execute("""
    SELECT id, symbol, asset_type, platform_account_id 
    FROM holdings 
    WHERE symbol LIKE '%MINDSPACE%'
""")
results = cursor.fetchall()

print("Current MINDSPACE holdings:")
for row in results:
    print(f"  ID: {row[0]}, Symbol: {row[1]}, Type: {row[2]}, Account: {row[3]}")

# Update to REIT
cursor.execute("""
    UPDATE holdings
    SET asset_type = 'REIT'
    WHERE symbol LIKE '%MINDSPACE%'
""")

affected = cursor.rowcount
print(f"\nUpdated {affected} MINDSPACE holdings to REIT type")

# Also create a REITs account for better organization
cursor.execute("""
    SELECT COUNT(*) FROM platform_accounts 
    WHERE nickname = 'REITs Account' AND user_id = 1
""")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO platform_accounts (user_id, pan_id, platform, client_id, nickname, account_type, is_active)
        VALUES (1, 1, 'ZERODHA', 'BHB965-REIT', 'REITs Account', 'DEMAT', 1)
    """)
    print("\nCreated 'REITs Account' platform account")
    
    # Get the new account ID
    cursor.execute("SELECT id FROM platform_accounts WHERE nickname = 'REITs Account' AND user_id = 1")
    reit_account_id = cursor.fetchone()[0]
    
    # Move REITs to the new account
    cursor.execute("""
        UPDATE holdings
        SET platform_account_id = ?
        WHERE asset_type = 'REIT'
        AND platform_account_id IN (
            SELECT id FROM platform_accounts WHERE user_id = 1
        )
    """, (reit_account_id,))
    print(f"Moved REITs to REITs Account (ID: {reit_account_id})")

# Commit changes
conn.commit()

# Show final distribution
print("\nFinal asset type distribution:")
cursor.execute("""
    SELECT asset_type, COUNT(*) as count
    FROM holdings h
    JOIN platform_accounts pa ON h.platform_account_id = pa.id
    WHERE pa.user_id = 1
    GROUP BY asset_type
    ORDER BY asset_type
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} holdings")

conn.close()
print("\nDone! MINDSPACE-RR is now classified as a REIT.")