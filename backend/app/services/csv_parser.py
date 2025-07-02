import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime
from fastapi import UploadFile, HTTPException
import io

class ZerodhaCSVParser:
    """Parser for Zerodha Console CSV exports"""
    
    # Known ETF symbol mappings
    ETF_SYMBOL_MAPPINGS = {
        "MAFSETFINAV": "MAFSETF",
        "MOM100INAV": "MOM100",
        "SETFNIF50": "SETFNN50",
        "NIFTYBEES": "NIFTYBEES",
        "BANKBEES": "BANKBEES",
        "GOLDBEES": "GOLDBEES",
        "JUNIORBEES": "JUNIORBEES",
        "LIQUIDBEES": "LIQUIDBEES",
        "NIFTYIWIN": "NIFTYIWIN",
        "ICICIB22": "ICICIB22",
        "SETFNIFBK": "SETFNIFBK",
        "LIQUIDBEESINAV": "LIQUIDBEES",
        "GOLDBEESINAV": "GOLDBEES",
        "NIFTYBEESINAV": "NIFTYBEES",
        "BANKBEESINAV": "BANKBEES",
        "JUNIORBEESINAV": "JUNIORBEES"
    }
    
    @staticmethod
    async def parse_holdings_csv(file: UploadFile) -> List[Dict[str, Any]]:
        """Parse Zerodha holdings CSV file"""
        try:
            contents = await file.read()
            
            # Check if file is empty
            if not contents or len(contents) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please select a valid CSV file with holdings data."
                )
            
            # First, try to find where the actual data starts
            lines = contents.decode('utf-8').split('\n')
            
            # Check if file has any non-empty lines
            non_empty_lines = [line for line in lines if line.strip()]
            if not non_empty_lines:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file contains no data. Please ensure the CSV file has holdings information."
                )
            
            header_line = None
            for i, line in enumerate(lines):
                if 'Symbol' in line or 'Instrument' in line:
                    header_line = i
                    break
            
            # Read CSV skipping rows until the header
            if header_line is not None:
                df = pd.read_csv(io.BytesIO(contents), skiprows=header_line)
            else:
                df = pd.read_csv(io.BytesIO(contents))
            
            # Check if this is the new Zerodha Console format
            if 'Symbol' in df.columns:
                # New format from Zerodha Console
                required_columns = ['Symbol', 'Quantity Available', 'Average Price', 'Previous Closing Price', 'Unrealized P&L', 'Unrealized P&L Pct.']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    # Try skipping rows to find the header
                    for skip_rows in range(1, 30):
                        df_test = pd.read_csv(io.BytesIO(contents), skiprows=skip_rows)
                        if all(col in df_test.columns for col in required_columns):
                            df = df_test
                            break
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Missing required columns: {missing_columns}"
                        )
            else:
                # Old format check
                required_columns = ['Instrument', 'Qty.', 'Avg. cost', 'LTP', 'Cur. val', 'P&L']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required columns: {missing_columns}"
                    )
            
            holdings = []
            
            # Parse based on format detected
            if 'Symbol' in df.columns:
                # New Zerodha Console format
                for _, row in df.iterrows():
                    # Skip empty rows
                    if pd.isna(row['Symbol']) or str(row['Symbol']).strip() == '':
                        continue
                    
                    quantity = float(row['Quantity Available'])
                    avg_price = float(row['Average Price'])
                    current_price = float(row['Previous Closing Price'])
                    pnl = float(row['Unrealized P&L'])
                    
                    # Determine asset type based on symbol or ISIN
                    symbol = str(row['Symbol']).strip()
                    asset_type = 'stock'  # Default
                    
                    # Check if we have ISIN column
                    isin = None
                    if 'ISIN' in row:
                        isin = str(row['ISIN']).strip() if pd.notna(row['ISIN']) else None
                    
                    # Detect ETFs based on ISIN pattern or symbol patterns
                    if isin:
                        # ETF ISINs typically have specific patterns
                        # Indian ETF ISINs often start with INF followed by specific patterns
                        if (isin.startswith('INF') and len(isin) == 12 and 
                            (isin[9:11] in ['01', 'H1', 'K1', 'L1', 'M1', 'N1', 'P1', 'Q1', 'R1', 'S1', 'T1'])):
                            asset_type = 'etf'
                    
                    # Also check symbol patterns for ETFs
                    etf_keywords = ['ETF', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'LIQUID', 'GILT', 
                                    'CPSE', 'PSU', 'BANK', 'IT', 'PHARMA', 'AUTO', 'FMCG', 'NEXT50',
                                    'MIDCAP', 'SMALLCAP', 'DIVIDEND', 'VALUE', 'MOMENTUM', 'QUALITY',
                                    'LOWVOL', 'ALPHA', 'BHARAT', 'MAFANG', 'NASDAQ', 'HANG']
                    
                    # Special case for known ETFs without ETF in the name
                    known_etfs = ['MAFSETFINAV', 'NIFTYBEES', 'BANKBEES', 'GOLDBEES', 'JUNIORBEES',
                                  'SETFNIF50', 'SETFNIFTY', 'SETFNN50']
                    
                    if (any(keyword in symbol.upper() for keyword in etf_keywords) and 'ETF' in symbol.upper()) or \
                       symbol.upper() in known_etfs or \
                       symbol.upper().endswith('BEES'):
                        asset_type = 'etf'
                    
                    # Check for SGBs
                    if 'SGB' in symbol.upper() or symbol.upper().startswith('SGB'):
                        asset_type = 'sgb'
                    
                    # Check for REITs
                    if 'REIT' in symbol.upper() or symbol.upper().endswith('-RR') or symbol.upper().endswith('-RT'):
                        asset_type = 'reit'
                    
                    # Apply ETF symbol mapping if exists
                    if symbol in ZerodhaCSVParser.ETF_SYMBOL_MAPPINGS:
                        symbol = ZerodhaCSVParser.ETF_SYMBOL_MAPPINGS[symbol]
                    
                    holding = {
                        'symbol': symbol,
                        'exchange': 'NSE',  # Default to NSE
                        'quantity': quantity,
                        'average_price': avg_price,
                        'current_price': current_price,
                        'current_value': quantity * current_price,
                        'pnl': pnl,
                        'pnl_percentage': float(row['Unrealized P&L Pct.']),
                        'asset_type': asset_type,
                        'isin': isin
                    }
                    holdings.append(holding)
            else:
                # Old format
                for _, row in df.iterrows():
                    # Extract exchange from instrument (e.g., "RELIANCE NSE" -> "RELIANCE", "NSE")
                    instrument = str(row['Instrument'])
                    symbol_match = re.match(r'(.+?)\s+(NSE|BSE)', instrument)
                    
                    if symbol_match:
                        symbol = symbol_match.group(1).strip()
                        exchange = symbol_match.group(2)
                    else:
                        symbol = instrument.strip()
                        exchange = 'NSE'  # Default to NSE
                    
                    # Determine asset type based on symbol patterns
                    asset_type = 'stock'  # Default
                    
                    # Check for ETFs
                    etf_keywords = ['ETF', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'LIQUID', 'GILT', 
                                    'CPSE', 'PSU', 'BANK', 'IT', 'PHARMA', 'AUTO', 'FMCG', 'NEXT50',
                                    'MIDCAP', 'SMALLCAP', 'DIVIDEND', 'VALUE', 'MOMENTUM', 'QUALITY',
                                    'LOWVOL', 'ALPHA', 'BHARAT', 'MAFANG', 'NASDAQ', 'HANG']
                    
                    # Special case for known ETFs without ETF in the name
                    known_etfs = ['MAFSETFINAV', 'NIFTYBEES', 'BANKBEES', 'GOLDBEES', 'JUNIORBEES',
                                  'SETFNIF50', 'SETFNIFTY', 'SETFNN50']
                    
                    if (any(keyword in symbol.upper() for keyword in etf_keywords) and 'ETF' in symbol.upper()) or \
                       symbol.upper() in known_etfs or \
                       symbol.upper().endswith('BEES'):
                        asset_type = 'etf'
                    
                    # Check for SGBs
                    if 'SGB' in symbol.upper() or symbol.upper().startswith('SGB'):
                        asset_type = 'sgb'
                    
                    # Check for REITs
                    if 'REIT' in symbol.upper() or symbol.upper().endswith('-RR') or symbol.upper().endswith('-RT'):
                        asset_type = 'reit'
                    
                    holding = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'quantity': float(row['Qty.']),
                        'average_price': float(row['Avg. cost']),
                        'current_price': float(row['LTP']),
                        'current_value': float(row['Cur. val']),
                        'pnl': float(row['P&L']),
                        'asset_type': asset_type
                    }
                    
                    # Calculate P&L percentage
                    investment = holding['quantity'] * holding['average_price']
                    if investment > 0:
                        holding['pnl_percentage'] = (holding['pnl'] / investment) * 100
                    else:
                        holding['pnl_percentage'] = 0
                    
                    holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing holdings CSV: {str(e)}"
            )
    
    @staticmethod
    async def parse_tradebook_csv(file: UploadFile) -> List[Dict[str, Any]]:
        """Parse Zerodha tradebook CSV file"""
        try:
            contents = await file.read()
            df = pd.read_csv(io.BytesIO(contents))
            
            transactions = []
            for _, row in df.iterrows():
                transaction = {
                    'symbol': row['symbol'],
                    'exchange': row.get('exchange', 'NSE'),
                    'transaction_type': row['trade_type'],  # BUY/SELL
                    'quantity': abs(float(row['quantity'])),
                    'price': float(row['price']),
                    'amount': float(row['quantity']) * float(row['price']),
                    'transaction_date': pd.to_datetime(row['trade_date']).isoformat(),
                    'exchange_order_id': str(row.get('order_id', ''))
                }
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing tradebook CSV: {str(e)}"
            )
    
    @staticmethod
    async def parse_pnl_csv(file: UploadFile) -> List[Dict[str, Any]]:
        """Parse Zerodha P&L CSV file"""
        try:
            contents = await file.read()
            df = pd.read_csv(io.BytesIO(contents))
            
            # P&L CSV typically contains realized gains
            pnl_data = []
            for _, row in df.iterrows():
                pnl_entry = {
                    'symbol': row['symbol'],
                    'buy_date': pd.to_datetime(row['buy_date']).isoformat(),
                    'sell_date': pd.to_datetime(row['sell_date']).isoformat(),
                    'buy_quantity': float(row['buy_quantity']),
                    'sell_quantity': float(row['sell_quantity']),
                    'buy_price': float(row['buy_average']),
                    'sell_price': float(row['sell_average']),
                    'realized_pnl': float(row['net_pnl'])
                }
                pnl_data.append(pnl_entry)
            
            return pnl_data
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing P&L CSV: {str(e)}"
            )

class MutualFundCSVParser:
    """Parser for CAMS/KFintech mutual fund statements"""
    
    @staticmethod
    async def parse_cams_csv(file: UploadFile) -> List[Dict[str, Any]]:
        """Parse CAMS consolidated statement"""
        try:
            contents = await file.read()
            # CAMS statements are typically in specific format
            # This is a placeholder - actual implementation would handle CAMS format
            
            mutual_funds = []
            # Parse logic here
            
            return mutual_funds
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing CAMS statement: {str(e)}"
            )

class GenericCSVParser:
    """Generic CSV parser for custom formats"""
    
    @staticmethod
    async def parse_custom_holdings(file: UploadFile, mapping: Dict[str, str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse custom CSV with automatic or user-defined column mapping"""
        try:
            contents = await file.read()
            
            # Check if file is empty
            if not contents or len(contents) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please select a valid CSV file with holdings data."
                )
            
            df = pd.read_csv(io.BytesIO(contents))
            
            if df.empty:
                raise HTTPException(
                    status_code=400,
                    detail="The CSV file contains no data rows."
                )
            
            # If no mapping provided, try to auto-detect columns
            if not mapping:
                mapping = GenericCSVParser._auto_detect_columns(df)
            
            holdings = []
            warnings_list = []
            
            for idx, row in df.iterrows():
                # Skip rows with empty symbol
                if pd.isna(row.get(mapping['symbol'], None)):
                    continue
                
                symbol = str(row[mapping['symbol']]).strip()
                original_symbol = symbol  # Keep original for warning messages
                
                # Clean symbol - remove exchange suffixes and spaces
                symbol = re.sub(r'\.(NS|BO|NSE|BSE)$', '', symbol, flags=re.IGNORECASE)
                # Remove spaces and special characters for better Yahoo Finance compatibility
                symbol = symbol.replace(' ', '').replace('&', '').replace('.', '')
                
                # Apply common symbol mappings
                symbol_mappings = {
                    'ColgatePalmolive': 'COLPAL',
                    'HDFCBank': 'HDFCBANK',
                    'LarsenToubro': 'LT',
                    'Pidilite': 'PIDILITIND',
                    'HCLTechnologies': 'HCLTECH',
                    'APLApolloTubes': 'APLAPOLLO',
                    'AsianPaints': 'ASIANPAINT',
                    'CochinShipyard': 'COCHINSHIP',
                    'CEInfosystem': 'MAPMYINDIA',
                    'SupremeIndustries': 'SUPREMEIND',
                    'AshokLeyland': 'ASHOKLEY',
                    'JioFinancialServices': 'JIOFIN',
                    'IDFCFirstBank': 'IDFCFIRSTB',
                    'DeltaCorp': 'DELTACORP',
                    'Infosys': 'INFY',
                }
                
                if symbol in symbol_mappings:
                    symbol = symbol_mappings[symbol]
                
                # Track missing fields for this holding
                missing_fields = []
                
                # For the custom format you have, we need to handle quantity differently
                # Since it doesn't have quantity, we'll default to 1
                quantity = 1.0
                if 'quantity' in mapping and mapping['quantity'] in row:
                    try:
                        quantity = float(row[mapping['quantity']])
                    except:
                        quantity = 1.0
                else:
                    missing_fields.append('quantity')
                    quantity = 1.0
                
                # Get average price
                avg_price = 0.0
                if 'average_price' in mapping and mapping['average_price'] in row:
                    try:
                        # Remove commas from the price value
                        price_str = str(row[mapping['average_price']]).replace(',', '')
                        avg_price = float(price_str)
                    except:
                        avg_price = 0.0
                        missing_fields.append('average_price (invalid value)')
                else:
                    missing_fields.append('average_price')
                    avg_price = 0.0
                
                # Get current price
                current_price = 0.0
                if 'current_price' in mapping and mapping['current_price'] in row:
                    try:
                        # Remove commas from the price value
                        price_str = str(row[mapping['current_price']]).replace(',', '')
                        current_price = float(price_str)
                    except:
                        current_price = 0.0
                
                # Apply ETF symbol mapping if exists
                if symbol in ZerodhaCSVParser.ETF_SYMBOL_MAPPINGS:
                    symbol = ZerodhaCSVParser.ETF_SYMBOL_MAPPINGS[symbol]
                
                # Detect asset type
                asset_type = 'stock'
                symbol_upper = symbol.upper()
                if 'ETF' in symbol_upper or symbol_upper.endswith('BEES') or symbol_upper.endswith('NAV'):
                    asset_type = 'etf'
                elif 'GOLD' in symbol_upper and 'SGB' in symbol_upper:
                    asset_type = 'sgb'
                elif 'REIT' in symbol_upper or symbol_upper.endswith('-RR') or symbol_upper.endswith('-RT'):
                    asset_type = 'reit'  # REITs are now a separate category
                
                # Calculate values
                current_value = quantity * current_price if current_price > 0 else quantity * avg_price
                pnl = current_value - (quantity * avg_price) if avg_price > 0 else 0
                pnl_percentage = (pnl / (quantity * avg_price) * 100) if avg_price > 0 and quantity > 0 else 0
                
                holding = {
                    'symbol': symbol,
                    'exchange': 'NSE',  # Default to NSE
                    'asset_type': asset_type,
                    'quantity': quantity,
                    'average_price': avg_price,
                    'current_price': current_price,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_percentage': pnl_percentage,
                    'isin': None
                }
                
                holdings.append(holding)
                
                # Add warning if there were missing fields
                if missing_fields:
                    warnings_list.append({
                        'symbol': original_symbol,
                        'missing_fields': missing_fields,
                        'row_number': idx + 2  # +2 because pandas is 0-indexed and Excel has header row
                    })
            
            if not holdings:
                raise HTTPException(
                    status_code=400,
                    detail="No valid holdings data found in the CSV file."
                )
            
            return holdings, warnings_list
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing custom CSV: {str(e)}"
            )
    
    @staticmethod
    def _auto_detect_columns(df: pd.DataFrame) -> Dict[str, str]:
        """Auto-detect column mapping based on column names"""
        mapping = {}
        
        # Define patterns for each field type
        patterns = {
            'symbol': [r'symbol', r'stock.*name', r'instrument', r'scrip', r'ticker', r'equity'],
            'quantity': [r'quantity', r'qty', r'shares', r'units', r'holdings'],
            'average_price': [r'avg.*price', r'average.*price', r'cost.*price', r'buy.*price', 
                             r'purchase.*price', r'owned.*price', r'acquisition.*price'],
            'current_price': [r'current.*price', r'ltp', r'last.*price', r'market.*price', 
                             r'cmp', r'close.*price']
        }
        
        # Find matching columns
        for field, field_patterns in patterns.items():
            for col in df.columns:
                col_lower = col.lower()
                for pattern in field_patterns:
                    if re.search(pattern, col_lower):
                        mapping[field] = col
                        break
                if field in mapping:
                    break
        
        # Check if we found at least the symbol column
        if 'symbol' not in mapping:
            # Show available columns to help user
            available_cols = ', '.join(df.columns[:10])  # Show first 10 columns
            if len(df.columns) > 10:
                available_cols += f'... and {len(df.columns) - 10} more'
                
            raise HTTPException(
                status_code=400,
                detail=f"Could not find a column for stock symbol. Available columns: {available_cols}"
            )
        
        return mapping


class ExcelParser:
    """Parser for Excel files with multiple sheets"""
    
    @staticmethod
    def _clean_mutual_fund_name(name: str) -> str:
        """Clean mutual fund name by removing dates, NAV values, and codes"""
        if not name:
            return name
            
        # Remove date patterns (various formats)
        # Matches: 27-Jun-2025, 27/06/2025, 27-06-2025, Jun 27 2025, etc.
        date_patterns = [
            r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',  # 27-Jun-2025
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # 27/06/2025 or 27-06-2025
            r'\w{3}\s+\d{1,2}\s+\d{2,4}',  # Jun 27 2025
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2025-06-27
        ]
        
        for pattern in date_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Remove NAV values (decimal numbers)
        # Matches: 56.8143, 139.25, etc.
        name = re.sub(r'\b\d+\.\d+\b', '', name)
        
        # Remove standalone numbers (like scheme codes)
        # Matches: 139, 12345, etc.
        name = re.sub(r'\b\d{2,}\b', '', name)
        
        # Clean up extra spaces
        name = ' '.join(name.split())
        
        # Remove trailing spaces and common suffixes that got isolated
        name = name.strip()
        
        return name
    
    @staticmethod
    async def parse_excel_file(file: UploadFile) -> Dict[str, List[Dict[str, Any]]]:
        """Parse Excel file and return data from all sheets"""
        try:
            contents = await file.read()
            
            # Check if file is empty
            if not contents or len(contents) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please select a valid Excel file."
                )
            
            # Read all sheets from Excel file
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            all_data = {}
            
            for sheet_name in excel_file.sheet_names:
                # First read without header to find where data starts
                df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                
                # Find the header row by looking for known column names
                header_row = None
                for i in range(min(50, len(df_raw))):  # Check first 50 rows
                    row = df_raw.iloc[i]
                    row_str = ' '.join([str(val).lower() for val in row if pd.notna(val)])
                    
                    # Look for common header keywords
                    if any(keyword in row_str for keyword in ['symbol', 'quantity', 'price', 'scheme', 'nav', 'units']):
                        header_row = i
                        break
                
                if header_row is None:
                    continue  # Skip sheet if no header found
                
                # Read the sheet again with the correct header
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                
                # Skip empty sheets
                if df.empty or len(df) == 0:
                    continue
                
                # Try to detect what type of data this sheet contains
                sheet_data_type = ExcelParser._detect_sheet_type(df, sheet_name)
                
                if sheet_data_type == 'stocks':
                    # Parse as stock holdings
                    holdings, warnings = ExcelParser._parse_stock_sheet(df, sheet_name)
                    all_data[f"{sheet_name}_stocks"] = {
                        'type': 'stocks',
                        'data': holdings,
                        'warnings': warnings
                    }
                elif sheet_data_type == 'mutual_funds':
                    # Parse as mutual fund holdings
                    holdings, warnings = ExcelParser._parse_mutual_fund_sheet(df, sheet_name)
                    all_data[f"{sheet_name}_mutual_funds"] = {
                        'type': 'mutual_funds',
                        'data': holdings,
                        'warnings': warnings
                    }
                else:
                    # Unknown sheet type, skip
                    continue
            
            if not all_data:
                raise HTTPException(
                    status_code=400,
                    detail="No valid holdings data found in any sheet of the Excel file."
                )
            
            return all_data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing Excel file: {str(e)}"
            )
    
    @staticmethod
    def _detect_sheet_type(df: pd.DataFrame, sheet_name: str) -> Optional[str]:
        """Detect whether sheet contains stocks or mutual funds data"""
        columns_lower = [col.lower() for col in df.columns]
        
        # Check for mutual fund indicators in column names
        mf_indicators = ['scheme', 'nav', 'folio', 'units', 'fund', 'amc']
        mf_count = sum(1 for indicator in mf_indicators if any(indicator in col for col in columns_lower))
        
        # Check for stock indicators
        stock_indicators = ['symbol', 'quantity', 'average price', 'ltp', 'exchange']
        stock_count = sum(1 for indicator in stock_indicators if any(indicator in col for col in columns_lower))
        
        # Also check sheet name
        sheet_name_lower = sheet_name.lower()
        if 'mutual' in sheet_name_lower or 'fund' in sheet_name_lower or 'mf' in sheet_name_lower:
            mf_count += 3  # Give more weight to sheet name
        if 'stock' in sheet_name_lower or 'equity' in sheet_name_lower or 'share' in sheet_name_lower:
            stock_count += 2
        
        # Check data content for mutual fund patterns
        if len(df) > 0 and 'symbol' in columns_lower:
            symbol_col = df.columns[columns_lower.index('symbol')]
            # Check first few non-null values
            sample_values = df[symbol_col].dropna().head(5).astype(str)
            for val in sample_values:
                val_lower = val.lower()
                # Look for mutual fund patterns in the data
                if any(keyword in val_lower for keyword in ['fund', 'scheme', 'elss', 'flexi cap', 'liquid', 'debt', 'equity']):
                    mf_count += 1
                # Check for typical mutual fund name patterns
                if 'direct plan' in val_lower or 'regular plan' in val_lower:
                    mf_count += 2
        
        # Also check for Instrument Type column which might contain fund categories
        if 'instrument type' in columns_lower:
            type_col = df.columns[columns_lower.index('instrument type')]
            sample_types = df[type_col].dropna().head(5).astype(str)
            for val in sample_types:
                if 'equity' in val.lower() and ('elss' in val.lower() or 'flexi' in val.lower()):
                    mf_count += 2
        
        if mf_count > stock_count:
            return 'mutual_funds'
        elif stock_count > 0:
            return 'stocks'
        else:
            return None
    
    @staticmethod
    def _parse_stock_sheet(df: pd.DataFrame, sheet_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse a sheet containing stock data"""
        # Use GenericCSVParser logic for stocks
        mapping = GenericCSVParser._auto_detect_columns(df)
        
        holdings = []
        warnings_list = []
        
        for idx, row in df.iterrows():
            # Skip rows with empty symbol
            if pd.isna(row.get(mapping.get('symbol'), None)):
                continue
            
            symbol = str(row[mapping['symbol']]).strip()
            original_symbol = symbol
            
            # Clean symbol
            symbol = re.sub(r'\.(NS|BO|NSE|BSE)$', '', symbol, flags=re.IGNORECASE)
            symbol = symbol.replace(' ', '').replace('&', '').replace('.', '')
            
            # Track missing fields
            missing_fields = []
            
            # Get quantity
            quantity = 1.0
            if 'quantity' in mapping and mapping['quantity'] in row:
                try:
                    quantity = float(row[mapping['quantity']])
                except:
                    quantity = 1.0
                    missing_fields.append('quantity (invalid value)')
            else:
                missing_fields.append('quantity')
            
            # Get average price
            avg_price = 0.0
            if 'average_price' in mapping and mapping['average_price'] in row:
                try:
                    price_str = str(row[mapping['average_price']]).replace(',', '')
                    avg_price = float(price_str)
                except:
                    avg_price = 0.0
                    missing_fields.append('average_price (invalid value)')
            else:
                missing_fields.append('average_price')
            
            # Get current price
            current_price = 0.0
            if 'current_price' in mapping and mapping['current_price'] in row:
                try:
                    price_str = str(row[mapping['current_price']]).replace(',', '')
                    current_price = float(price_str)
                except:
                    current_price = 0.0
            
            holding = {
                'symbol': symbol,
                'exchange': 'NSE',
                'asset_type': 'stock',
                'quantity': quantity,
                'average_price': avg_price,
                'current_price': current_price,
                'current_value': quantity * current_price if current_price > 0 else quantity * avg_price,
                'pnl': 0,
                'pnl_percentage': 0,
                'isin': None
            }
            
            # Calculate P&L
            if avg_price > 0 and current_price > 0:
                holding['pnl'] = (current_price - avg_price) * quantity
                holding['pnl_percentage'] = ((current_price - avg_price) / avg_price) * 100
            
            holdings.append(holding)
            
            if missing_fields:
                warnings_list.append({
                    'symbol': original_symbol,
                    'missing_fields': missing_fields,
                    'row_number': idx + 2,
                    'sheet': sheet_name
                })
        
        return holdings, warnings_list
    
    @staticmethod
    def _parse_mutual_fund_sheet(df: pd.DataFrame, sheet_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse a sheet containing mutual fund data"""
        # Define patterns for mutual fund columns
        patterns = {
            'scheme_name': [r'scheme.*name', r'fund.*name', r'scheme', r'fund', r'symbol'],  # Added symbol
            'folio_number': [r'folio', r'account.*no'],
            'units': [r'units', r'quantity.*available', r'quantity', r'balance.*units'],  # Added quantity available
            'nav': [r'nav', r'net.*asset.*value', r'previous.*closing.*price', r'price'],  # Added previous closing price
            'current_value': [r'current.*value', r'market.*value', r'value'],
            'invested_value': [r'invested.*value', r'cost.*value', r'purchase.*value', r'average.*price'],  # Added average price
            'scheme_code': [r'scheme.*code', r'fund.*code', r'amfi.*code', r'isin']  # Added ISIN
        }
        
        # Find matching columns
        mapping = {}
        for field, field_patterns in patterns.items():
            for col in df.columns:
                col_lower = col.lower()
                for pattern in field_patterns:
                    if re.search(pattern, col_lower):
                        mapping[field] = col
                        break
                if field in mapping:
                    break
        
        holdings = []
        warnings_list = []
        
        for idx, row in df.iterrows():
            # Skip rows with empty scheme name
            if 'scheme_name' not in mapping or pd.isna(row.get(mapping.get('scheme_name'), None)):
                continue
            
            scheme_name = str(row[mapping['scheme_name']]).strip()
            # Clean the scheme name to remove dates, NAV values, etc.
            scheme_name = ExcelParser._clean_mutual_fund_name(scheme_name)
            missing_fields = []
            
            # Get units
            units = 0.0
            if 'units' in mapping and mapping['units'] in row:
                try:
                    units = float(str(row[mapping['units']]).replace(',', ''))
                except:
                    units = 0.0
                    missing_fields.append('units (invalid value)')
            else:
                missing_fields.append('units')
            
            # Get NAV
            nav = 0.0
            if 'nav' in mapping and mapping['nav'] in row:
                try:
                    nav = float(str(row[mapping['nav']]).replace(',', ''))
                except:
                    nav = 0.0
                    missing_fields.append('nav (invalid value)')
            else:
                missing_fields.append('nav')
            
            # Get invested value or average price
            invested_value = 0.0
            avg_price = 0.0
            if 'invested_value' in mapping and mapping['invested_value'] in row:
                try:
                    value = float(str(row[mapping['invested_value']]).replace(',', ''))
                    # If this looks like a per-unit price (less than 1000), it's average price
                    if value < 1000:
                        avg_price = value
                        invested_value = avg_price * units if units > 0 else 0
                    else:
                        invested_value = value
                        avg_price = invested_value / units if units > 0 else nav
                except:
                    invested_value = 0.0
                    avg_price = nav
            
            # Get current value
            current_value = units * nav if nav > 0 else 0.0
            if 'current_value' in mapping and mapping['current_value'] in row:
                try:
                    parsed_value = float(str(row[mapping['current_value']]).replace(',', ''))
                    if parsed_value > 0:
                        current_value = parsed_value
                except:
                    pass
            
            # Get scheme code if available
            scheme_code = None
            if 'scheme_code' in mapping and mapping['scheme_code'] in row:
                scheme_code = str(row[mapping['scheme_code']]).strip()
            
            # Create holding
            holding = {
                'symbol': scheme_name[:50],  # Truncate long names
                'exchange': 'MF',  # Mutual Fund
                'asset_type': 'mutual_fund',
                'quantity': units,
                'average_price': avg_price,
                'current_price': nav,
                'current_value': current_value,
                'pnl': current_value - invested_value if invested_value > 0 else 0,
                'pnl_percentage': ((current_value - invested_value) / invested_value * 100) if invested_value > 0 else 0,
                'isin': None,
                'scheme_code': scheme_code
            }
            
            holdings.append(holding)
            
            if missing_fields:
                warnings_list.append({
                    'symbol': scheme_name,
                    'missing_fields': missing_fields,
                    'row_number': idx + 2,
                    'sheet': sheet_name
                })
        
        return holdings, warnings_list