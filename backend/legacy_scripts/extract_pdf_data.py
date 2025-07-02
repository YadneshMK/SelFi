#!/usr/bin/env python3
"""
Extract mutual fund data from PDF and add to holdings
"""
import PyPDF2
import re
import sqlite3
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
                
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_mutual_fund_data(text):
    """Parse mutual fund data from extracted text"""
    # Common patterns in mutual fund statements
    patterns = {
        'scheme_name': [
            r'Scheme\s*Name\s*:\s*([^\n]+)',
            r'Fund\s*Name\s*:\s*([^\n]+)',
            r'Scheme\s*:\s*([^\n]+)',
            r'([A-Za-z\s]+Fund[^\n]+)',
        ],
        'units': [
            r'Units\s*:\s*([\d,]+\.?\d*)',
            r'Balance\s*Units\s*:\s*([\d,]+\.?\d*)',
            r'Total\s*Units\s*:\s*([\d,]+\.?\d*)',
            r'Closing\s*Units?\s*:\s*([\d,]+\.?\d*)',
        ],
        'nav': [
            r'NAV\s*:\s*₹?\s*([\d,]+\.?\d*)',
            r'Current\s*NAV\s*:\s*₹?\s*([\d,]+\.?\d*)',
            r'NAV\s*as\s*on[^:]*:\s*₹?\s*([\d,]+\.?\d*)',
        ],
        'value': [
            r'Current\s*Value\s*:\s*₹?\s*([\d,]+\.?\d*)',
            r'Market\s*Value\s*:\s*₹?\s*([\d,]+\.?\d*)',
            r'Value\s*:\s*₹?\s*([\d,]+\.?\d*)',
        ],
        'folio': [
            r'Folio\s*No\s*\.?\s*:\s*([^\n]+)',
            r'Folio\s*Number\s*:\s*([^\n]+)',
            r'Account\s*No\s*\.?\s*:\s*([^\n]+)',
        ]
    }
    
    extracted_data = {}
    
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean numeric values
                if field in ['units', 'nav', 'value']:
                    value = value.replace(',', '').replace('₹', '').strip()
                    try:
                        value = float(value)
                    except:
                        continue
                extracted_data[field] = value
                break
    
    # Look specifically for Tata fund
    if 'Tata' in text:
        tata_matches = re.findall(r'(Tata[^,\n]{0,100}Fund[^,\n]{0,50})', text, re.IGNORECASE)
        if tata_matches and 'scheme_name' not in extracted_data:
            extracted_data['scheme_name'] = tata_matches[0].strip()
    
    return extracted_data

def add_to_holdings(fund_data):
    """Add mutual fund to holdings database"""
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
        symbol = fund_data.get('scheme_name', 'Unknown Fund')
        # Clean up symbol
        symbol = symbol.replace('\n', ' ').strip()
        if len(symbol) > 50:
            symbol = symbol[:50]
            
        quantity = fund_data.get('units', 0)
        current_price = fund_data.get('nav', 0)
        current_value = fund_data.get('value', quantity * current_price)
        
        # For average price, we'll use current NAV as approximation
        # (unless you have purchase history)
        average_price = current_price
        
        # Check if holding already exists
        cursor.execute("""
            SELECT id FROM holdings 
            WHERE symbol = ? AND platform_account_id = ?
        """, (symbol, platform_account_id))
        
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
                    pnl, pnl_percentage, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                platform_account_id, symbol, 'MF', 'MUTUAL_FUND',
                quantity, average_price, current_price, current_value,
                0, 0, datetime.utcnow()
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

def main():
    print("PDF Mutual Fund Data Extractor")
    print("=" * 50)
    
    pdf_path = input("\nPlease enter the path to your PDF file: ").strip()
    
    # Remove quotes if present
    pdf_path = pdf_path.strip('"').strip("'")
    
    print(f"\nProcessing: {pdf_path}")
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"\nExtracted {len(text)} characters from PDF")
    
    # Parse mutual fund data
    fund_data = parse_mutual_fund_data(text)
    
    if not fund_data:
        print("No mutual fund data found in PDF")
        print("\nShowing first 500 characters of extracted text:")
        print(text[:500])
        return
    
    print("\nExtracted Data:")
    for key, value in fund_data.items():
        print(f"  {key}: {value}")
    
    # Confirm before adding
    confirm = input("\nAdd this fund to your holdings? (y/n): ").lower()
    
    if confirm == 'y':
        if add_to_holdings(fund_data):
            print("\n✅ Successfully added to holdings!")
        else:
            print("\n❌ Failed to add to holdings")
    else:
        print("\nCancelled")

if __name__ == "__main__":
    main()