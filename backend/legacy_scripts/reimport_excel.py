#!/usr/bin/env python3
"""
Re-import the Excel file to check mutual funds
"""
import asyncio
import sys
sys.path.append('/Users/yadnesh_kombe/hackathon/Finance App/backend')

from app.services.csv_parser import ExcelParser
from fastapi import UploadFile
import io

async def check_excel():
    # Read the file
    excel_file = "/Users/yadnesh_kombe/Downloads/holdings-BHB965 (2).xlsx"
    
    with open(excel_file, 'rb') as f:
        contents = f.read()
    
    # Create a mock UploadFile
    file = type('obj', (object,), {
        'filename': 'holdings-BHB965 (2).xlsx',
        'read': lambda: asyncio.coroutine(lambda: contents)()
    })()
    
    # Parse it
    try:
        result = await ExcelParser.parse_excel_file(file)
        
        for sheet_name, data in result.items():
            print(f"\n{sheet_name}:")
            print(f"  Type: {data['type']}")
            print(f"  Holdings count: {len(data['data'])}")
            if data['type'] == 'mutual_funds':
                print("  Mutual Funds found:")
                for holding in data['data']:
                    print(f"    - {holding['symbol']}")
            elif data['data']:
                # Show first few entries
                print("  First few entries:")
                for holding in data['data'][:5]:
                    print(f"    - {holding['symbol']} ({holding['asset_type']})")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Run it
asyncio.run(check_excel())