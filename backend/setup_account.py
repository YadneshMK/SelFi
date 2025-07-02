#!/usr/bin/env python3
"""
Quick setup script to add PAN and platform account for testing
"""
import requests
import json

API_URL = "http://localhost:8001/api/v1"
TOKEN = input("Enter your JWT token (from login): ").strip()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Add PAN details
print("\n1. Adding PAN details...")
pan_data = {
    "pan_number": input("Enter your PAN number: ").strip().upper(),
    "holder_name": input("Enter PAN holder name: ").strip()
}

response = requests.post(f"{API_URL}/portfolios/pan", json=pan_data, headers=headers)
if response.status_code == 200:
    pan_detail = response.json()
    print(f"✅ PAN added successfully! ID: {pan_detail['id']}")
else:
    print(f"❌ Error adding PAN: {response.text}")
    exit(1)

# Step 2: Add platform account
print("\n2. Adding Zerodha platform account...")
account_data = {
    "pan_id": pan_detail['id'],
    "platform": "zerodha",
    "client_id": input("Enter your Zerodha Client ID: ").strip(),
    "nickname": input("Enter a nickname for this account (e.g., 'Main Account'): ").strip(),
    "account_type": "trading"
}

response = requests.post(f"{API_URL}/portfolios/platform-accounts", json=account_data, headers=headers)
if response.status_code == 200:
    account = response.json()
    print(f"✅ Platform account added successfully! ID: {account['id']}")
    print(f"\nYou can now upload CSV files using platform_account_id: {account['id']}")
else:
    print(f"❌ Error adding platform account: {response.text}")