#!/usr/bin/env python3
"""
Extract Tata mutual fund data from PDF and add to holdings
"""
import PyPDF2
import re
import sqlite3
from datetime import datetime
import sys
import os

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Reading {num_pages} pages from PDF...")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
                
                # Show Tata-related content from this page
                if 'Tata' in page_text or 'TATA' in page_text:
                    print(f"\nFound Tata content on page {page_num + 1}")
                    
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_tata_fund_data(text):
    """Parse Tata mutual fund data from extracted text"""
    extracted_data = {}
    
    # Look for Tata Digital India Fund specifically
    tata_fund_patterns = [
        r'(Tata\s+Digital\s+India\s+Fund[^,\n]*)',
        r'(TATA\s+DIGITAL\s+INDIA\s+FUND[^,\n]*)',
        r'Scheme\s*:\s*(Tata[^,\n]+Fund[^,\n]*)',
    ]
    
    for pattern in tata_fund_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['scheme_name'] = match.group(1).strip()
            break
    
    # Extract units/balance
    units_patterns = [
        r'Balance\s*Units?\s*:\s*([\d,]+\.?\d*)',
        r'Units\s*:\s*([\d,]+\.?\d*)',
        r'Total\s*Units?\s*:\s*([\d,]+\.?\d*)',
        r'Closing\s*Balance\s*:\s*([\d,]+\.?\d*)',
        r'No\.\s*of\s*Units\s*:\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in units_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            units = match.group(1).replace(',', '').strip()
            try:
                extracted_data['units'] = float(units)
                break
            except:
                continue
    
    # Extract NAV
    nav_patterns = [
        r'NAV\s*(?:as\s*on[^:]*)?:\s*₹?\s*([\d,]+\.?\d*)',
        r'Net\s*Asset\s*Value.*?:\s*₹?\s*([\d,]+\.?\d*)',
        r'NAV\s*₹?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in nav_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nav = match.group(1).replace(',', '').replace('₹', '').strip()
            try:
                extracted_data['nav'] = float(nav)
                break
            except:
                continue
    
    # Extract current value
    value_patterns = [
        r'Current\s*Value\s*:\s*₹?\s*([\d,]+\.?\d*)',
        r'Market\s*Value\s*:\s*₹?\s*([\d,]+\.?\d*)',
        r'Value\s*as\s*on[^:]*:\s*₹?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in value_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '').replace('₹', '').strip()
            try:
                extracted_data['value'] = float(value)
                break
            except:
                continue
    
    # Try to extract from table format
    if 'units' not in extracted_data:
        # Look for Tata fund line and extract data
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Tata Digital' in line or 'TATA DIGITAL' in line:
                # Check this line and next few lines for numbers
                combined_text = ' '.join(lines[i:i+3])
                numbers = re.findall(r'[\d,]+\.?\d*', combined_text)
                
                if numbers:
                    # Try to identify units (usually first large number)
                    for num in numbers:
                        num_float = float(num.replace(',', ''))
                        if num_float > 10 and num_float < 100000:  # Reasonable range for units
                            extracted_data['units'] = num_float
                            break
                        elif num_float > 0 and num_float < 1000:  # Could be NAV
                            extracted_data['nav'] = num_float
    
    return extracted_data

def add_to_holdings(fund_data):
    """Add Tata mutual fund to holdings database"""
    db_path = "/Users/yadnesh_kombe/hackathon/Finance App/backend/finance_app.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get user's mutual fund account
        cursor.execute("""
            SELECT id FROM platform_accounts 
            WHERE user_id = 1 AND nickname = 'Mutual Funds Account'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("Error: Mutual Funds Account not found")
            return False
            
        platform_account_id = result[0]
        
        # Prepare holding data
        symbol = fund_data.get('scheme_name', 'Tata Digital India Fund - Direct Plan')
        symbol = symbol.replace('\n', ' ').strip()
        
        # Use known NAV from account statement if not found
        quantity = fund_data.get('units', 0)
        current_price = fund_data.get('nav', 56.8143)  # From account statement
        current_value = quantity * current_price
        average_price = current_price  # Approximation
        
        # Check if holding already exists
        cursor.execute("""
            SELECT id FROM holdings 
            WHERE symbol LIKE ? AND platform_account_id = ?
        """, (f'%Tata Digital%', platform_account_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing holding
            cursor.execute("""
                UPDATE holdings
                SET quantity = ?, current_price = ?, current_value = ?,
                    average_price = ?, last_updated = ?
                WHERE id = ?
            """, (quantity, current_price, current_value, average_price, 
                  datetime.utcnow(), existing[0]))
            print(f"Updated existing holding: {symbol}")
        else:
            # Insert new holding
            cursor.execute("""
                INSERT INTO holdings (
                    platform_account_id, symbol, exchange, asset_type,
                    quantity, average_price, current_price, current_value,
                    pnl, pnl_percentage, last_updated, isin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                platform_account_id, symbol, 'MF', 'MUTUAL_FUND',
                quantity, average_price, current_price, current_value,
                0, 0, datetime.utcnow(), 'INF277K01Z77'
            ))
            print(f"Added new holding: {symbol}")
        
        conn.commit()
        print(f"\nSuccessfully added/updated:")
        print(f"  Fund: {symbol}")
        print(f"  Units: {quantity}")
        print(f"  NAV: ₹{current_price}")
        print(f"  Value: ₹{current_value}")
        
        return True
        
    except Exception as e:
        print(f"Error adding to database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_tata_fund_from_pdf.py <path_to_pdf>")
        print("\nPlease provide the path to your PDF file as an argument")
        sys.exit(1)
    
    pdf_path = sys.argv[1].strip('"').strip("'")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Processing PDF: {pdf_path}")
    print("=" * 50)
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        sys.exit(1)
    
    print(f"\nExtracted {len(text)} characters from PDF")
    
    # Parse Tata fund data
    fund_data = parse_tata_fund_data(text)
    
    print("\nExtracted Data:")
    for key, value in fund_data.items():
        print(f"  {key}: {value}")
    
    if not fund_data or 'units' not in fund_data:
        print("\n⚠️  Could not extract units/quantity from PDF")
        print("Showing sample of extracted text to help identify the format:")
        print("-" * 50)
        # Show text around Tata mentions
        tata_index = text.lower().find('tata')
        if tata_index > -1:
            start = max(0, tata_index - 200)
            end = min(len(text), tata_index + 500)
            print(text[start:end])
        else:
            print(text[:1000])
        print("-" * 50)
        
        # Ask for manual input
        try:
            units = float(input("\nPlease enter the number of units manually: "))
            fund_data['units'] = units
        except:
            print("Invalid input. Exiting.")
            sys.exit(1)
    
    # Add to holdings
    if add_to_holdings(fund_data):
        print("\n✅ Successfully added Tata Digital India Fund to your holdings!")
        print("Refresh your holdings page to see the update.")
    else:
        print("\n❌ Failed to add to holdings")