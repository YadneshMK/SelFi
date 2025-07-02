#!/usr/bin/env python3
"""
Check for Tata mutual fund in the Excel file
"""
import pandas as pd
import sys

excel_file = "/Users/yadnesh_kombe/Downloads/holdings-BHB965 (2).xlsx"

try:
    # Read all sheets
    excel_data = pd.ExcelFile(excel_file)
    
    print(f"Sheets in the file: {excel_data.sheet_names}")
    
    # Search for Tata in all sheets
    for sheet_name in excel_data.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Search for Tata in all columns
        for col in df.columns:
            tata_rows = df[df[col].astype(str).str.contains('tata|TATA', case=False, na=False)]
            if not tata_rows.empty:
                print(f"\nFound Tata-related entries in sheet '{sheet_name}', column '{col}':")
                for idx, row in tata_rows.iterrows():
                    print(f"  Row {idx}: {row[col]}")
                    # Print the entire row for context
                    print(f"  Full row: {row.to_dict()}")
                    
except Exception as e:
    print(f"Error reading file: {e}")