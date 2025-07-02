#!/usr/bin/env python3
"""
Fix misclassified asset types in holdings
"""
import sqlite3
import re

# Connect to database
db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Fixing Asset Type Classifications ===\n")

# Show current misclassified holdings
print("Current misclassified holdings in Stocks tab:")
cursor.execute("""
    SELECT id, symbol, asset_type, platform_account_id
    FROM holdings
    WHERE asset_type = 'STOCK'
    AND (
        symbol LIKE '%FUND%' OR 
        symbol LIKE '%NAV' OR 
        symbol LIKE '%ETF%' OR
        symbol LIKE 'SGB%' OR
        symbol LIKE '%ELSS%' OR
        symbol LIKE '%FLEXI%CAP%' OR
        symbol LIKE '%LIQUID%' OR
        symbol LIKE '%BEES'
    )
""")
misclassified = cursor.fetchall()
for row in misclassified:
    print(f"  ID: {row[0]}, Symbol: {row[1]}, Current Type: {row[2]}")

# Define classification rules
def classify_asset(symbol):
    symbol_upper = symbol.upper()
    
    # Mutual Funds
    if any(keyword in symbol_upper for keyword in ['FUND', 'ELSS', 'FLEXICAP', 'FLEXI CAP', 'LIQUID', 'DEBT', 'EQUITY']):
        return 'MUTUAL_FUND'
    
    # ETFs - check for common ETF patterns
    if symbol_upper.endswith('NAV') or symbol_upper.endswith('INAV'):
        return 'ETF'
    if symbol_upper.endswith('BEES'):
        return 'ETF'
    if 'ETF' in symbol_upper:
        return 'ETF'
    # Specific ETF symbols
    if symbol_upper in ['MAFSETF', 'MAFSETFINAV', 'MOM100', 'MOM100INAV', 'SETFNIF50', 'SETFNN50']:
        return 'ETF'
    
    # SGBs
    if symbol_upper.startswith('SGB') or 'SGB' in symbol_upper:
        return 'SGB'
    
    # Default to stock
    return 'STOCK'

# Fix classifications
fixes = []
print("\nApplying fixes:")
for holding_id, symbol, current_type, account_id in misclassified:
    new_type = classify_asset(symbol)
    if new_type != current_type:
        fixes.append((holding_id, symbol, current_type, new_type))
        cursor.execute("""
            UPDATE holdings
            SET asset_type = ?
            WHERE id = ?
        """, (new_type, holding_id))
        print(f"  {symbol}: {current_type} → {new_type}")

# Also fix any other misclassified assets not caught by the initial query
print("\nChecking all holdings for proper classification...")
cursor.execute("SELECT id, symbol, asset_type FROM holdings")
all_holdings = cursor.fetchall()
additional_fixes = 0

for holding_id, symbol, current_type in all_holdings:
    correct_type = classify_asset(symbol)
    if correct_type != current_type:
        cursor.execute("""
            UPDATE holdings
            SET asset_type = ?
            WHERE id = ?
        """, (correct_type, holding_id))
        additional_fixes += 1
        print(f"  Additional fix: {symbol}: {current_type} → {correct_type}")

# Now reassign to correct platform accounts based on updated asset types
print("\nReassigning to correct platform accounts...")
reassignments = [
    ('MUTUAL_FUND', 4),  # Mutual Funds Account
    ('ETF', 5),          # ETF Account
]

for asset_type, account_id in reassignments:
    cursor.execute("""
        UPDATE holdings
        SET platform_account_id = ?
        WHERE asset_type = ?
        AND platform_account_id IN (
            SELECT id FROM platform_accounts WHERE user_id = 1
        )
    """, (account_id, asset_type))
    affected = cursor.rowcount
    if affected > 0:
        print(f"  Moved {affected} {asset_type} holdings to account {account_id}")

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

# Show holdings by tab
print("\nHoldings that will appear in each tab:")
for tab_type in ['STOCK', 'ETF', 'MUTUAL_FUND', 'SGB']:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM holdings h
        JOIN platform_accounts pa ON h.platform_account_id = pa.id
        WHERE pa.user_id = 1 AND h.asset_type = ?
    """, (tab_type,))
    count = cursor.fetchone()[0]
    print(f"  {tab_type} tab: {count} holdings")

conn.close()
print("\nAsset types fixed! Refresh your holdings page to see properly categorized assets.")