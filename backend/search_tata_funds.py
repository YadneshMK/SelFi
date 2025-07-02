#!/usr/bin/env python3
"""
Search for Tata mutual funds in various uploaded files
"""
import pandas as pd
import os
import glob

# List of files to check based on import history
files_to_check = [
    "/Users/yadnesh_kombe/Downloads/account-statement.xlsx",
    "/Users/yadnesh_kombe/Downloads/holdings-ANX616.xlsx",
    "/Users/yadnesh_kombe/Downloads/holdings-YG7227.xlsx",
    "/Users/yadnesh_kombe/Downloads/holdings-BHB965 (1).csv",
    "/Users/yadnesh_kombe/Downloads/holdings-BHB965.csv",
    "/Users/yadnesh_kombe/Downloads/holdings-BHB965 (2).xlsx"
]

# Also search for any other holdings files
additional_files = glob.glob("/Users/yadnesh_kombe/Downloads/holdings*.csv") + \
                  glob.glob("/Users/yadnesh_kombe/Downloads/holdings*.xlsx") + \
                  glob.glob("/Users/yadnesh_kombe/Downloads/*statement*.xlsx") + \
                  glob.glob("/Users/yadnesh_kombe/Downloads/*statement*.csv")

all_files = list(set(files_to_check + additional_files))

print("Searching for Tata mutual funds in the following files:\n")

for file_path in all_files:
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        continue
        
    print(f"\n📄 Checking: {os.path.basename(file_path)}")
    
    try:
        if file_path.endswith('.csv'):
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Search for Tata in all columns
            found = False
            for col in df.columns:
                tata_rows = df[df[col].astype(str).str.contains('tata|TATA', case=False, na=False)]
                if not tata_rows.empty:
                    found = True
                    print(f"  ✅ Found Tata entries in column '{col}':")
                    for idx, row in tata_rows.iterrows():
                        value = row[col]
                        # Check if it's a mutual fund
                        row_str = str(row.to_dict()).lower()
                        if 'fund' in row_str or 'mutual' in row_str or 'nav' in row_str:
                            print(f"    🎯 MUTUAL FUND: {value}")
                            print(f"       Full row: {row.to_dict()}")
                        else:
                            print(f"    - {value} (likely a stock)")
                            
            if not found:
                print(f"  ❌ No Tata entries found")
                
        elif file_path.endswith(('.xlsx', '.xls')):
            # Read Excel file - all sheets
            excel_file = pd.ExcelFile(file_path)
            
            found_in_file = False
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Search for Tata in all columns
                found_in_sheet = False
                for col in df.columns:
                    tata_rows = df[df[col].astype(str).str.contains('tata|TATA', case=False, na=False)]
                    if not tata_rows.empty:
                        if not found_in_sheet:
                            print(f"  📋 Sheet: {sheet_name}")
                            found_in_sheet = True
                            found_in_file = True
                            
                        print(f"    ✅ Found Tata entries in column '{col}':")
                        for idx, row in tata_rows.iterrows():
                            value = row[col]
                            # Check if it's a mutual fund
                            row_str = str(row.to_dict()).lower()
                            if 'fund' in row_str or 'mutual' in row_str or 'nav' in row_str or 'scheme' in row_str:
                                print(f"      🎯 MUTUAL FUND: {value}")
                                print(f"         Row data: {row.to_dict()}")
                            else:
                                print(f"      - {value} (likely a stock)")
                                
            if not found_in_file:
                print(f"  ❌ No Tata entries found in any sheet")
                
    except Exception as e:
        print(f"  ⚠️ Error reading file: {e}")

print("\n\n=== SUMMARY ===")
print("Search complete. Check above for any Tata mutual fund entries marked with 🎯")