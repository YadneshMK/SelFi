#!/usr/bin/env python3
"""
Check Excel sheets for Tata mutual fund
"""
import pandas as pd

excel_file = "/Users/yadnesh_kombe/Downloads/holdings-BHB965 (2).xlsx"

# Read Mutual Funds sheet specifically
try:
    df_mf = pd.read_excel(excel_file, sheet_name='Mutual Funds')
    
    print("Mutual Funds sheet shape:", df_mf.shape)
    print("\nFirst 40 rows of Mutual Funds sheet:")
    print(df_mf.head(40).to_string())
    
    # Look for data starting after row 20
    print("\n\nChecking rows 20-30:")
    if len(df_mf) > 20:
        for idx in range(20, min(30, len(df_mf))):
            row_data = df_mf.iloc[idx]
            if any(str(val).strip() for val in row_data if pd.notna(val)):
                print(f"Row {idx}: {row_data.to_dict()}")
                
except Exception as e:
    print(f"Error: {e}")