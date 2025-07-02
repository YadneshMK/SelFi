from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db import models
from app.services.csv_parser import ZerodhaCSVParser, MutualFundCSVParser, GenericCSVParser, ExcelParser
from app.services.pdf_parser import PDFParser
from app.services.market_data import StockDataService, MutualFundService
from app.schemas.portfolio import Holding, HoldingCreate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def validate_file_account_match(filename: str, platform_account: models.PlatformAccount) -> tuple[bool, str]:
    """
    Validate that the uploaded file matches the selected account.
    Returns (is_valid, error_message)
    """
    # Extract account ID from filename if present
    filename_lower = filename.lower()
    
    # Common patterns: holdings-YG7227.xlsx, YG7227_holdings.csv, etc.
    import re
    # Pattern to match account IDs in filenames
    account_pattern = r'(?:holdings[-_])?([A-Z0-9]{6})(?:[-_]|\.)'
    matches = re.findall(account_pattern, filename.upper())
    
    if matches:
        file_account_id = matches[0]
        # Check if it matches the selected account's client_id
        if file_account_id != platform_account.client_id.upper():
            return False, f"File appears to be for account {file_account_id}, but you selected account {platform_account.client_id}"
    
    # If no account ID in filename, show a warning but allow upload
    return True, ""

@router.post("/zerodha/holdings")
async def upload_zerodha_holdings(
    platform_account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="The selected account could not be found. Please refresh the page and try again.")
    
    # Validate file matches account
    is_valid, error_msg = validate_file_account_match(file.filename, platform_account)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Parse the CSV file
    holdings_data = await ZerodhaCSVParser.parse_holdings_csv(file)
    
    # Create import history record
    import_record = models.ImportHistory(
        user_id=current_user.id,
        platform_account_id=platform_account_id,
        file_name=file.filename,
        file_type="holdings_csv",
        import_status="processing"
    )
    db.add(import_record)
    db.commit()
    
    imported_count = 0
    updated_count = 0
    duplicate_holdings = []
    
    try:
        # Process each holding
        for holding_data in holdings_data:
            # Determine asset type from parsed data
            asset_type_str = holding_data.get('asset_type', 'stock').upper()
            asset_type_map = {
                'STOCK': models.AssetType.STOCK,
                'ETF': models.AssetType.ETF,
                'MUTUAL_FUND': models.AssetType.MUTUAL_FUND,
                'SGB': models.AssetType.SGB,
                'REIT': models.AssetType.REIT
            }
            asset_type = asset_type_map.get(asset_type_str, models.AssetType.STOCK)
            
            # Check if holding already exists
            existing_holding = db.query(models.Holding).filter(
                models.Holding.platform_account_id == platform_account_id,
                models.Holding.symbol == holding_data['symbol'],
                models.Holding.asset_type == asset_type
            ).first()
            
            if existing_holding:
                # Store duplicate info
                duplicate_holdings.append({
                    'symbol': holding_data['symbol'],
                    'old_quantity': existing_holding.quantity,
                    'new_quantity': holding_data['quantity'],
                    'old_avg_price': existing_holding.average_price,
                    'new_avg_price': holding_data['average_price']
                })
                
                # Update existing holding
                existing_holding.quantity = holding_data['quantity']
                existing_holding.average_price = holding_data['average_price']
                existing_holding.current_price = holding_data['current_price']
                existing_holding.current_value = holding_data['current_value']
                existing_holding.pnl = holding_data['pnl']
                existing_holding.pnl_percentage = holding_data['pnl_percentage']
                if 'isin' in holding_data and holding_data['isin']:
                    existing_holding.isin = holding_data['isin']
                    
                updated_count += 1
            else:
                # Create new holding
                new_holding = models.Holding(
                    platform_account_id=platform_account_id,
                    symbol=holding_data['symbol'],
                    exchange=holding_data['exchange'],
                    asset_type=asset_type,
                    quantity=holding_data['quantity'],
                    average_price=holding_data['average_price'],
                    current_price=holding_data['current_price'],
                    current_value=holding_data['current_value'],
                    pnl=holding_data['pnl'],
                    pnl_percentage=holding_data['pnl_percentage'],
                    isin=holding_data.get('isin')
                )
                db.add(new_holding)
            
            imported_count += 1
        
        db.commit()
        
        # Auto-fetch current prices for newly imported holdings
        logger.info(f"Auto-fetching prices for {imported_count} imported holdings")
        price_update_count = 0
        
        # Get all holdings that were just imported
        new_holdings = db.query(models.Holding).filter(
            models.Holding.platform_account_id == platform_account_id,
            models.Holding.current_price == 0  # Only update holdings without prices
        ).all()
        
        for holding in new_holdings:
            try:
                if holding.asset_type in [models.AssetType.STOCK, models.AssetType.ETF]:
                    # Convert exchange name to suffix
                    exchange_suffix = "NS"
                    if holding.exchange:
                        if holding.exchange.upper() == "NSE":
                            exchange_suffix = "NS"
                        elif holding.exchange.upper() == "BSE":
                            exchange_suffix = "BO"
                    
                    info = StockDataService.get_stock_info(holding.symbol, exchange_suffix)
                    if info and info.get("current_price"):
                        holding.current_price = info["current_price"]
                        holding.current_value = holding.quantity * info["current_price"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        logger.info(f"Updated price for {holding.symbol}: ₹{info['current_price']}")
                    
                elif holding.asset_type == models.AssetType.MUTUAL_FUND and holding.scheme_code:
                    info = MutualFundService.get_mutual_fund_info(holding.scheme_code)
                    if info:
                        holding.current_price = info["nav"]
                        holding.current_value = holding.quantity * info["nav"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        
            except Exception as e:
                logger.error(f"Error updating price for {holding.symbol}: {str(e)}")
                # Continue with other holdings even if one fails
        
        db.commit()
        
        # Update import record
        import_record.import_status = "success"
        import_record.records_imported = imported_count
        db.commit()
        
        response_data = {
            "message": f"Successfully imported {imported_count} new holdings",
            "imported_count": imported_count,
            "updated_count": updated_count,
            "prices_updated": price_update_count,
            "has_duplicates": len(duplicate_holdings) > 0,
            "duplicate_holdings": duplicate_holdings
        }
        
        if updated_count > 0:
            response_data["message"] = f"Successfully imported {imported_count} new holdings and updated {updated_count} existing holdings"
        
        return response_data
        
    except Exception as e:
        db.rollback()
        import_record.import_status = "failed"
        import_record.error_message = str(e)
        db.commit()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to process the uploaded file. Please check the file format and try again.")

@router.post("/zerodha/transactions")
async def upload_zerodha_transactions(
    platform_account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="The selected account could not be found. Please refresh the page and try again.")
    
    # Parse the CSV file
    transactions_data = await ZerodhaCSVParser.parse_tradebook_csv(file)
    
    imported_count = 0
    for transaction_data in transactions_data:
        # Create transaction record
        new_transaction = models.Transaction(
            platform_account_id=platform_account_id,
            transaction_type=transaction_data['transaction_type'],
            symbol=transaction_data['symbol'],
            quantity=transaction_data['quantity'],
            price=transaction_data['price'],
            amount=transaction_data['amount'],
            transaction_date=transaction_data['transaction_date'],
            exchange_order_id=transaction_data.get('exchange_order_id', '')
        )
        db.add(new_transaction)
        imported_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully imported {imported_count} transactions",
        "imported_count": imported_count
    }

@router.post("/generic/holdings")
async def upload_generic_holdings(
    platform_account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload holdings from any source (non-Zerodha CSV formats)"""
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="The selected account could not be found. Please refresh the page and try again.")
    
    # Validate file matches account
    is_valid, error_msg = validate_file_account_match(file.filename, platform_account)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Initialize counters and warnings list
    imported_count = 0
    updated_count = 0
    skipped_count = 0
    warnings = []
    
    # Parse the CSV file using generic parser
    holdings_data, parse_warnings = await GenericCSVParser.parse_custom_holdings(file)
    
    # Add parse warnings to the warnings list
    if parse_warnings:
        warnings.extend(parse_warnings)
    
    # Create import history record
    import_record = models.ImportHistory(
        user_id=current_user.id,
        platform_account_id=platform_account_id,
        file_name=file.filename,
        file_type="generic_holdings_csv",
        import_status="processing"
    )
    db.add(import_record)
    db.commit()
    
    try:
        # Process each holding
        for holding_data in holdings_data:
            # Determine asset type from parsed data
            asset_type_str = holding_data.get('asset_type', 'stock').upper()
            asset_type_map = {
                'STOCK': models.AssetType.STOCK,
                'ETF': models.AssetType.ETF,
                'MUTUAL_FUND': models.AssetType.MUTUAL_FUND,
                'SGB': models.AssetType.SGB,
                'REIT': models.AssetType.REIT
            }
            asset_type = asset_type_map.get(asset_type_str, models.AssetType.STOCK)
            
            # Check if holding already exists
            existing_holding = db.query(models.Holding).filter(
                models.Holding.platform_account_id == platform_account_id,
                models.Holding.symbol == holding_data['symbol'],
                models.Holding.asset_type == asset_type
            ).first()
            
            if existing_holding:
                # Check if data has changed
                if (existing_holding.quantity == holding_data['quantity'] and 
                    existing_holding.average_price == holding_data['average_price']):
                    # Skip if no changes
                    skipped_count += 1
                    logger.info(f"Skipping {holding_data['symbol']} - no changes detected")
                else:
                    # Update existing holding
                    existing_holding.quantity = holding_data['quantity']
                    existing_holding.average_price = holding_data['average_price']
                    existing_holding.current_price = holding_data['current_price']
                    existing_holding.current_value = holding_data['current_value']
                    existing_holding.pnl = holding_data['pnl']
                    existing_holding.pnl_percentage = holding_data['pnl_percentage']
                    updated_count += 1
                    logger.info(f"Updated existing holding: {holding_data['symbol']}")
            else:
                # Create new holding
                new_holding = models.Holding(
                    platform_account_id=platform_account_id,
                    symbol=holding_data['symbol'],
                    exchange=holding_data['exchange'],
                    asset_type=asset_type,
                    quantity=holding_data['quantity'],
                    average_price=holding_data['average_price'],
                    current_price=holding_data['current_price'],
                    current_value=holding_data['current_value'],
                    pnl=holding_data['pnl'],
                    pnl_percentage=holding_data['pnl_percentage'],
                    isin=holding_data.get('isin')
                )
                db.add(new_holding)
                imported_count += 1
                logger.info(f"Added new holding: {holding_data['symbol']}")
        
        db.commit()
        
        # Auto-fetch current prices for newly imported holdings
        logger.info(f"Auto-fetching prices for {imported_count} imported holdings")
        price_update_count = 0
        
        # Get all holdings that were just imported
        new_holdings = db.query(models.Holding).filter(
            models.Holding.platform_account_id == platform_account_id,
            models.Holding.current_price == 0  # Only update holdings without prices
        ).all()
        
        for holding in new_holdings:
            try:
                if holding.asset_type in [models.AssetType.STOCK, models.AssetType.ETF]:
                    # Convert exchange name to suffix
                    exchange_suffix = "NS"
                    if holding.exchange:
                        if holding.exchange.upper() == "NSE":
                            exchange_suffix = "NS"
                        elif holding.exchange.upper() == "BSE":
                            exchange_suffix = "BO"
                    
                    info = StockDataService.get_stock_info(holding.symbol, exchange_suffix)
                    if info and info.get("current_price"):
                        holding.current_price = info["current_price"]
                        holding.current_value = holding.quantity * info["current_price"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        logger.info(f"Updated price for {holding.symbol}: ₹{info['current_price']}")
                    
            except Exception as e:
                logger.error(f"Error updating price for {holding.symbol}: {str(e)}")
                # Continue with other holdings even if one fails
        
        db.commit()
        
        # Update import record
        import_record.import_status = "success"
        import_record.records_imported = imported_count
        db.commit()
        
        summary_parts = []
        if imported_count > 0:
            summary_parts.append(f"imported {imported_count} new")
        if updated_count > 0:
            summary_parts.append(f"updated {updated_count} existing")
        if skipped_count > 0:
            summary_parts.append(f"skipped {skipped_count} unchanged")
        
        summary = " holdings, ".join(summary_parts) + " holdings" if summary_parts else "No holdings processed"
        
        return {
            "message": f"Successfully {summary}. Updated {price_update_count} prices.",
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "prices_updated": price_update_count,
            "warnings": warnings
        }
        
    except Exception as e:
        db.rollback()
        import_record.import_status = "failed"
        import_record.error_message = str(e)
        db.commit()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to process the uploaded file. Please check the file format and try again.")

@router.post("/excel/holdings")
async def upload_excel_holdings(
    platform_account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload Excel file with multiple sheets containing holdings data"""
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="The selected account could not be found. Please refresh the page and try again.")
    
    # Validate file matches account
    is_valid, error_msg = validate_file_account_match(file.filename, platform_account)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check file extension
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Parse Excel file
    all_sheet_data = await ExcelParser.parse_excel_file(file)
    
    # Create import history record
    import_record = models.ImportHistory(
        user_id=current_user.id,
        platform_account_id=platform_account_id,
        file_name=file.filename,
        file_type="excel_holdings",
        import_status="processing"
    )
    db.add(import_record)
    db.commit()
    
    total_imported = 0
    total_updated = 0
    total_skipped = 0
    all_warnings = []
    sheet_summaries = []
    
    try:
        # Process each sheet's data
        for sheet_key, sheet_data in all_sheet_data.items():
            sheet_type = sheet_data['type']
            holdings_data = sheet_data['data']
            warnings = sheet_data['warnings']
            
            # Add sheet name to warnings
            for warning in warnings:
                all_warnings.append(warning)
            
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            # Process each holding
            for holding_data in holdings_data:
                # Determine asset type from parsed data
                asset_type_str = holding_data.get('asset_type', 'stock').upper()
                asset_type_map = {
                    'STOCK': models.AssetType.STOCK,
                    'ETF': models.AssetType.ETF,
                    'MUTUAL_FUND': models.AssetType.MUTUAL_FUND,
                    'SGB': models.AssetType.SGB
                }
                asset_type = asset_type_map.get(asset_type_str, models.AssetType.STOCK)
                
                # Check if holding already exists
                existing_holding = db.query(models.Holding).filter(
                    models.Holding.platform_account_id == platform_account_id,
                    models.Holding.symbol == holding_data['symbol'],
                    models.Holding.asset_type == asset_type
                ).first()
                
                if existing_holding:
                    # Check if data has changed
                    if (existing_holding.quantity == holding_data['quantity'] and 
                        existing_holding.average_price == holding_data['average_price']):
                        skipped_count += 1
                    else:
                        # Update existing holding
                        existing_holding.quantity = holding_data['quantity']
                        existing_holding.average_price = holding_data['average_price']
                        existing_holding.current_price = holding_data['current_price']
                        existing_holding.current_value = holding_data['current_value']
                        existing_holding.pnl = holding_data['pnl']
                        existing_holding.pnl_percentage = holding_data['pnl_percentage']
                        if 'scheme_code' in holding_data and holding_data['scheme_code']:
                            existing_holding.scheme_code = holding_data['scheme_code']
                        updated_count += 1
                else:
                    # Create new holding
                    new_holding = models.Holding(
                        platform_account_id=platform_account_id,
                        symbol=holding_data['symbol'],
                        exchange=holding_data['exchange'],
                        asset_type=asset_type,
                        quantity=holding_data['quantity'],
                        average_price=holding_data['average_price'],
                        current_price=holding_data['current_price'],
                        current_value=holding_data['current_value'],
                        pnl=holding_data['pnl'],
                        pnl_percentage=holding_data['pnl_percentage'],
                        isin=holding_data.get('isin'),
                        scheme_code=holding_data.get('scheme_code')
                    )
                    db.add(new_holding)
                    imported_count += 1
            
            total_imported += imported_count
            total_updated += updated_count
            total_skipped += skipped_count
            
            sheet_summaries.append({
                'sheet': sheet_key,
                'type': sheet_type,
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count
            })
        
        db.commit()
        
        # Auto-fetch current prices for newly imported holdings
        logger.info(f"Auto-fetching prices for holdings from Excel")
        price_update_count = 0
        
        # Get all holdings that need price updates
        holdings_to_update = db.query(models.Holding).filter(
            models.Holding.platform_account_id == platform_account_id,
            models.Holding.current_price == 0
        ).all()
        
        for holding in holdings_to_update:
            try:
                if holding.asset_type in [models.AssetType.STOCK, models.AssetType.ETF]:
                    # Convert exchange name to suffix
                    exchange_suffix = "NS"
                    if holding.exchange:
                        if holding.exchange.upper() == "NSE":
                            exchange_suffix = "NS"
                        elif holding.exchange.upper() == "BSE":
                            exchange_suffix = "BO"
                    
                    info = StockDataService.get_stock_info(holding.symbol, exchange_suffix)
                    if info and info.get("current_price"):
                        holding.current_price = info["current_price"]
                        holding.current_value = holding.quantity * info["current_price"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        logger.info(f"Updated price for {holding.symbol}: ₹{info['current_price']}")
                    
                elif holding.asset_type == models.AssetType.MUTUAL_FUND and holding.scheme_code:
                    info = MutualFundService.get_mutual_fund_info(holding.scheme_code)
                    if info:
                        holding.current_price = info["nav"]
                        holding.current_value = holding.quantity * info["nav"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        
            except Exception as e:
                logger.error(f"Error updating price for {holding.symbol}: {str(e)}")
        
        db.commit()
        
        # Update import record
        import_record.import_status = "success"
        import_record.records_imported = total_imported
        db.commit()
        
        message_parts = []
        if total_imported > 0:
            message_parts.append(f"imported {total_imported} new")
        if total_updated > 0:
            message_parts.append(f"updated {total_updated} existing")
        if total_skipped > 0:
            message_parts.append(f"skipped {total_skipped} unchanged")
        
        summary = " holdings, ".join(message_parts) + " holdings" if message_parts else "No holdings processed"
        
        return {
            "message": f"Successfully {summary} from {len(all_sheet_data)} sheets. Updated {price_update_count} prices.",
            "imported_count": total_imported,
            "updated_count": total_updated,
            "skipped_count": total_skipped,
            "prices_updated": price_update_count,
            "warnings": all_warnings,
            "sheet_summaries": sheet_summaries
        }
        
    except Exception as e:
        db.rollback()
        import_record.import_status = "failed"
        import_record.error_message = str(e)
        db.commit()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to process the uploaded file. Please check the file format and try again.")

@router.get("/import-history")
def get_import_history(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    history = db.query(models.ImportHistory).filter(
        models.ImportHistory.user_id == current_user.id
    ).order_by(models.ImportHistory.imported_at.desc()).limit(limit).all()
    
    return history

@router.post("/pdf/holdings")
async def upload_pdf_holdings(
    platform_account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload PDF file containing holdings data (mutual funds, demat statements, etc.)"""
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="The selected account could not be found. Please refresh the page and try again.")
    
    # Validate file matches account - PDF files might not have account IDs, so we'll be lenient
    is_valid, error_msg = validate_file_account_match(file.filename, platform_account)
    if not is_valid and "appears to be for account" in error_msg:
        # For PDFs, convert to a warning instead of error
        warnings = [{"message": error_msg}]
    else:
        warnings = []
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file (.pdf)"
        )
    
    # Parse PDF file
    holdings_data, warnings = await PDFParser.parse_pdf_file(file)
    
    # Create import history record
    import_record = models.ImportHistory(
        user_id=current_user.id,
        platform_account_id=platform_account_id,
        file_name=file.filename,
        file_type="pdf_holdings",
        import_status="processing"
    )
    db.add(import_record)
    db.commit()
    
    total_imported = 0
    total_updated = 0
    total_skipped = 0
    
    try:
        # Process each holding
        for holding_data in holdings_data:
            # Determine asset type from parsed data
            asset_type_str = holding_data.get('asset_type', 'stock').upper()
            asset_type_map = {
                'STOCK': models.AssetType.STOCK,
                'ETF': models.AssetType.ETF,
                'MUTUAL_FUND': models.AssetType.MUTUAL_FUND,
                'SGB': models.AssetType.SGB,
                'REIT': models.AssetType.REIT
            }
            asset_type = asset_type_map.get(asset_type_str, models.AssetType.STOCK)
            
            # Check if holding already exists
            existing_holding = db.query(models.Holding).filter(
                models.Holding.platform_account_id == platform_account_id,
                models.Holding.symbol == holding_data['symbol'],
                models.Holding.asset_type == asset_type
            ).first()
            
            if existing_holding:
                # Check if data has changed
                if (existing_holding.quantity == holding_data['quantity'] and 
                    existing_holding.average_price == holding_data['average_price']):
                    total_skipped += 1
                    logger.info(f"Skipping {holding_data['symbol']} - no changes detected")
                else:
                    # Update existing holding
                    existing_holding.quantity = holding_data['quantity']
                    existing_holding.average_price = holding_data['average_price']
                    existing_holding.current_price = holding_data['current_price']
                    existing_holding.current_value = holding_data['current_value']
                    existing_holding.pnl = holding_data['pnl']
                    existing_holding.pnl_percentage = holding_data['pnl_percentage']
                    if 'isin' in holding_data and holding_data['isin']:
                        existing_holding.isin = holding_data['isin']
                    total_updated += 1
                    logger.info(f"Updated existing holding: {holding_data['symbol']}")
            else:
                # Create new holding
                new_holding = models.Holding(
                    platform_account_id=platform_account_id,
                    symbol=holding_data['symbol'],
                    exchange=holding_data['exchange'],
                    asset_type=asset_type,
                    quantity=holding_data['quantity'],
                    average_price=holding_data['average_price'],
                    current_price=holding_data['current_price'],
                    current_value=holding_data['current_value'],
                    pnl=holding_data['pnl'],
                    pnl_percentage=holding_data['pnl_percentage'],
                    isin=holding_data.get('isin')
                )
                db.add(new_holding)
                total_imported += 1
                logger.info(f"Added new holding: {holding_data['symbol']}")
        
        db.commit()
        
        # Auto-fetch current prices for newly imported holdings
        logger.info(f"Auto-fetching prices for holdings from PDF")
        price_update_count = 0
        
        # Get all holdings that need price updates
        holdings_to_update = db.query(models.Holding).filter(
            models.Holding.platform_account_id == platform_account_id,
            models.Holding.current_price == 0
        ).all()
        
        for holding in holdings_to_update:
            try:
                if holding.asset_type in [models.AssetType.STOCK, models.AssetType.ETF]:
                    # Convert exchange name to suffix
                    exchange_suffix = "NS"
                    if holding.exchange:
                        if holding.exchange.upper() == "NSE":
                            exchange_suffix = "NS"
                        elif holding.exchange.upper() == "BSE":
                            exchange_suffix = "BO"
                    
                    info = StockDataService.get_stock_info(holding.symbol, exchange_suffix)
                    if info and info.get("current_price"):
                        holding.current_price = info["current_price"]
                        holding.current_value = holding.quantity * info["current_price"]
                        holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                        holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                        holding.last_updated = datetime.utcnow()
                        price_update_count += 1
                        logger.info(f"Updated price for {holding.symbol}: ₹{info['current_price']}")
                    
                elif holding.asset_type == models.AssetType.MUTUAL_FUND:
                    # For mutual funds, try to get NAV if we don't have current price
                    info = MutualFundService.search_mutual_fund(holding.symbol)
                    if info and len(info) > 0:
                        # Use the first matching fund
                        fund_info = MutualFundService.get_mutual_fund_info(info[0]['schemeCode'])
                        if fund_info:
                            holding.current_price = fund_info["nav"]
                            holding.current_value = holding.quantity * fund_info["nav"]
                            holding.pnl = holding.current_value - (holding.quantity * holding.average_price)
                            holding.pnl_percentage = (holding.pnl / (holding.quantity * holding.average_price)) * 100
                            holding.last_updated = datetime.utcnow()
                            holding.scheme_code = info[0]['schemeCode']
                            price_update_count += 1
                            
            except Exception as e:
                logger.error(f"Error updating price for {holding.symbol}: {str(e)}")
        
        db.commit()
        
        # Update import record
        import_record.import_status = "success"
        import_record.records_imported = total_imported
        db.commit()
        
        message_parts = []
        if total_imported > 0:
            message_parts.append(f"imported {total_imported} new")
        if total_updated > 0:
            message_parts.append(f"updated {total_updated} existing")
        if total_skipped > 0:
            message_parts.append(f"skipped {total_skipped} unchanged")
        
        summary = " holdings, ".join(message_parts) + " holdings" if message_parts else "No holdings processed"
        
        return {
            "message": f"Successfully {summary} from PDF. Updated {price_update_count} prices.",
            "imported_count": total_imported,
            "updated_count": total_updated,
            "skipped_count": total_skipped,
            "prices_updated": price_update_count,
            "warnings": warnings
        }
        
    except Exception as e:
        db.rollback()
        import_record.import_status = "failed"
        import_record.error_message = str(e)
        db.commit()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to process the uploaded file. Please check the file format and try again.")