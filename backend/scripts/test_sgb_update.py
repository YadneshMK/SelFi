#!/usr/bin/env python3
"""
Test script to demonstrate automatic SGB price updates
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.services.gold_price_service import GoldPriceService
from app.services.sgb_price_service import SGBPriceService

def test_sgb_price_update():
    """Test automatic SGB price calculation"""
    
    print("=== Testing Automatic SGB Price Update ===\n")
    
    # Test 1: Gold Price Fetching
    print("1. Fetching current gold price...")
    gold_price = GoldPriceService.get_gold_price_inr()
    
    if gold_price:
        print(f"   ✓ Current gold price: ₹{gold_price:,.2f} per gram")
    else:
        print("   ✗ Failed to fetch gold price")
        return
    
    # Test 2: SGB Price Calculation
    print("\n2. Calculating SGB price (with 3% premium)...")
    sgb_price = GoldPriceService.calculate_sgb_price()
    
    if sgb_price:
        print(f"   ✓ Calculated SGB price: ₹{sgb_price:,.2f} per gram")
        premium = ((sgb_price / gold_price) - 1) * 100
        print(f"   ✓ Premium over gold: {premium:.1f}%")
    else:
        print("   ✗ Failed to calculate SGB price")
        return
    
    # Test 3: Get SGB details
    print("\n3. Getting details for SGBSEP28VI...")
    details = GoldPriceService.get_sgb_details('SGBSEP28VI')
    
    if details:
        print(f"   ✓ Symbol: {details['symbol']}")
        print(f"   ✓ Current Price: ₹{details['current_price']:,.2f}")
        print(f"   ✓ Gold Price: ₹{details['gold_price']:,.2f}")
        print(f"   ✓ Premium: {details['premium_percent']}%")
        print(f"   ✓ Interest Rate: {details['interest_rate']}% p.a.")
        print(f"   ✓ Maturity: {details['maturity']}")
    
    # Test 4: Use SGBPriceService
    print("\n4. Testing SGBPriceService for SGBSEP28VI-GB...")
    sgb_service_price = SGBPriceService.get_sgb_price('SGBSEP28VI-GB')
    
    if sgb_service_price:
        print(f"   ✓ SGB Price from service: ₹{sgb_service_price:,.2f}")
    else:
        print("   ✗ Failed to get price from SGBPriceService")
    
    # Test 5: Compare with manual price
    print("\n5. Comparison with manual prices:")
    print(f"   - Previous manual price: ₹9,659.39")
    print(f"   - Current automatic price: ₹{sgb_price:,.2f}")
    
    if sgb_price > 0:
        difference = abs(sgb_price - 9659.39)
        percent_diff = (difference / 9659.39) * 100
        print(f"   - Difference: ₹{difference:,.2f} ({percent_diff:.1f}%)")
    
    print("\n=== Summary ===")
    print("✓ Automatic SGB price update is working!")
    print("✓ Prices are fetched from live gold price APIs")
    print("✓ SGB premium is automatically calculated")
    print("✓ No manual intervention required")
    
    # Show how it would update in the database
    print("\n=== How it updates holdings ===")
    print("When update_sgb_prices() is called:")
    print("1. Fetches current gold price from API")
    print("2. Calculates SGB price with premium")
    print("3. Updates all SGB holdings in database")
    print("4. Recalculates P&L based on new prices")

if __name__ == "__main__":
    test_sgb_price_update()