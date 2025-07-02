import PyPDF2
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException
import io

class PDFParser:
    """Parser for PDF statements - mutual funds, demat statements, etc."""
    
    @staticmethod
    async def parse_pdf_file(file: UploadFile) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse PDF file and extract holdings data"""
        try:
            contents = await file.read()
            
            if not contents or len(contents) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please select a valid PDF file."
                )
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            # Detect PDF type and parse accordingly
            if PDFParser._is_mutual_fund_statement(text):
                return PDFParser._parse_mutual_fund_statement(text)
            elif PDFParser._is_demat_statement(text):
                return PDFParser._parse_demat_statement(text)
            else:
                # Try generic parsing
                return PDFParser._parse_generic_pdf(text)
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing PDF file: {str(e)}"
            )
    
    @staticmethod
    def _is_mutual_fund_statement(text: str) -> bool:
        """Check if PDF is a mutual fund statement"""
        mf_keywords = ['mutual fund', 'scheme', 'nav', 'folio', 'units', 'redemption', 'amc', 'fund house']
        text_lower = text.lower()
        matches = sum(1 for keyword in mf_keywords if keyword in text_lower)
        return matches >= 3
    
    @staticmethod
    def _is_demat_statement(text: str) -> bool:
        """Check if PDF is a demat statement"""
        demat_keywords = ['demat', 'cdsl', 'nsdl', 'isin', 'depository', 'securities', 'shares']
        text_lower = text.lower()
        matches = sum(1 for keyword in demat_keywords if keyword in text_lower)
        return matches >= 3
    
    @staticmethod
    def _parse_mutual_fund_statement(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse mutual fund statement"""
        holdings = []
        warnings = []
        
        # Common patterns for mutual fund data
        patterns = {
            'scheme_pattern': r'([A-Za-z\s]+(?:Fund|Scheme)[^\n]*)',
            'units_pattern': r'(?:Balance|Units|Closing)\s*:?\s*([\d,]+\.?\d*)',
            'nav_pattern': r'NAV\s*(?:as\s*on[^:]*)?:?\s*₹?\s*([\d,]+\.?\d*)',
            'value_pattern': r'(?:Current|Market)\s*Value\s*:?\s*₹?\s*([\d,]+\.?\d*)',
        }
        
        # Extract schemes
        schemes = re.findall(patterns['scheme_pattern'], text, re.IGNORECASE)
        
        # For each scheme found, try to extract associated data
        for scheme in schemes:
            scheme_data = {
                'symbol': scheme.strip()[:50],  # Limit length
                'exchange': 'MF',
                'asset_type': 'mutual_fund',
                'quantity': 0,
                'average_price': 0,
                'current_price': 0,
                'current_value': 0,
                'pnl': 0,
                'pnl_percentage': 0
            }
            
            # Find the position of this scheme in text
            scheme_pos = text.find(scheme)
            if scheme_pos == -1:
                continue
                
            # Look for data near this scheme (within 500 characters)
            nearby_text = text[scheme_pos:scheme_pos + 500]
            
            # Extract units
            units_match = re.search(patterns['units_pattern'], nearby_text)
            if units_match:
                try:
                    scheme_data['quantity'] = float(units_match.group(1).replace(',', ''))
                except:
                    warnings.append({
                        'symbol': scheme,
                        'missing_fields': ['quantity'],
                        'message': 'Could not parse units value'
                    })
            
            # Extract NAV
            nav_match = re.search(patterns['nav_pattern'], nearby_text)
            if nav_match:
                try:
                    nav = float(nav_match.group(1).replace(',', ''))
                    scheme_data['current_price'] = nav
                    scheme_data['average_price'] = nav  # Approximation
                except:
                    warnings.append({
                        'symbol': scheme,
                        'missing_fields': ['nav'],
                        'message': 'Could not parse NAV value'
                    })
            
            # Calculate current value
            if scheme_data['quantity'] > 0 and scheme_data['current_price'] > 0:
                scheme_data['current_value'] = scheme_data['quantity'] * scheme_data['current_price']
            
            # Only add if we have meaningful data
            if scheme_data['quantity'] > 0:
                holdings.append(scheme_data)
        
        # Special handling for common fund houses
        if not holdings:
            # Try table-based extraction
            holdings, warnings = PDFParser._extract_mf_table_data(text)
        
        return holdings, warnings
    
    @staticmethod
    def _extract_mf_table_data(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract mutual fund data from table format"""
        holdings = []
        warnings = []
        
        # Split by lines and look for patterns
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for fund names (usually contain 'Fund' or specific keywords)
            if re.search(r'(Fund|ELSS|Liquid|Debt|Equity|Growth|Dividend)', line, re.IGNORECASE):
                # Try to extract numbers from this line and next few lines
                combined_text = ' '.join(lines[i:i+5])
                
                # Extract all numbers
                numbers = re.findall(r'[\d,]+\.?\d*', combined_text)
                
                if len(numbers) >= 2:
                    try:
                        # Usually: units, nav, value
                        units = float(numbers[0].replace(',', ''))
                        nav = float(numbers[1].replace(',', '')) if len(numbers) > 1 else 0
                        
                        # Create holding
                        holding = {
                            'symbol': line.strip()[:50],
                            'exchange': 'MF',
                            'asset_type': 'mutual_fund',
                            'quantity': units,
                            'average_price': nav,
                            'current_price': nav,
                            'current_value': units * nav,
                            'pnl': 0,
                            'pnl_percentage': 0
                        }
                        
                        if units > 0 and units < 1000000:  # Sanity check
                            holdings.append(holding)
                    except:
                        continue
        
        return holdings, warnings
    
    @staticmethod
    def _parse_demat_statement(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse demat statement"""
        holdings = []
        warnings = []
        
        # Pattern for ISIN and company names
        isin_pattern = r'(IN[A-Z0-9]{9})\s+([A-Za-z\s&\.\-]+)'
        quantity_pattern = r'([\d,]+)\s*(?:shares?|units?)'
        
        # Find all ISIN matches
        isin_matches = re.findall(isin_pattern, text)
        
        for isin, company_name in isin_matches:
            holding_data = {
                'symbol': company_name.strip().upper().replace(' LTD', '').replace(' LIMITED', ''),
                'exchange': 'NSE',
                'asset_type': 'stock',
                'quantity': 0,
                'average_price': 0,
                'current_price': 0,
                'current_value': 0,
                'pnl': 0,
                'pnl_percentage': 0,
                'isin': isin
            }
            
            # Look for quantity near this ISIN
            isin_pos = text.find(isin)
            if isin_pos > -1:
                nearby_text = text[isin_pos:isin_pos + 200]
                qty_match = re.search(quantity_pattern, nearby_text)
                if qty_match:
                    try:
                        holding_data['quantity'] = float(qty_match.group(1).replace(',', ''))
                    except:
                        warnings.append({
                            'symbol': company_name,
                            'missing_fields': ['quantity'],
                            'message': 'Could not parse quantity'
                        })
            
            if holding_data['quantity'] > 0:
                holdings.append(holding_data)
                warnings.append({
                    'symbol': holding_data['symbol'],
                    'missing_fields': ['average_price', 'current_price'],
                    'message': 'Prices will be fetched from market data'
                })
        
        return holdings, warnings
    
    @staticmethod
    def _parse_generic_pdf(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generic PDF parsing for various formats"""
        holdings = []
        warnings = []
        
        # Try to identify holdings data
        # Look for common patterns
        
        # Pattern 1: Symbol followed by numbers
        pattern1 = r'([A-Z]{2,}[A-Z0-9\-]*)\s+([\d,]+)\s+([\d,]+\.?\d*)'
        matches = re.findall(pattern1, text)
        
        for match in matches:
            symbol, quantity, price = match
            try:
                holding = {
                    'symbol': symbol,
                    'exchange': 'NSE',
                    'asset_type': 'stock',
                    'quantity': float(quantity.replace(',', '')),
                    'average_price': float(price.replace(',', '')),
                    'current_price': 0,
                    'current_value': 0,
                    'pnl': 0,
                    'pnl_percentage': 0
                }
                
                if holding['quantity'] > 0 and holding['quantity'] < 1000000:
                    holdings.append(holding)
            except:
                continue
        
        if not holdings:
            warnings.append({
                'symbol': 'PDF',
                'missing_fields': ['all'],
                'message': 'Could not parse PDF format. Please check if this is a valid holdings statement.'
            })
        
        return holdings, warnings