from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db import models
from app.schemas.portfolio import (
    Portfolio, PortfolioCreate, PortfolioSummary,
    PlatformAccount, PlatformAccountCreate,
    HoldingWithDetails, HoldingCreate
)
from app.schemas.user import PANDetail, PANDetailCreate

router = APIRouter()

@router.post("/pan", response_model=PANDetail)
def add_pan_detail(
    pan_data: PANDetailCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if PAN already exists
    existing_pan = db.query(models.PANDetail).filter(
        models.PANDetail.pan_number == pan_data.pan_number
    ).first()
    
    if existing_pan:
        if existing_pan.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="PAN already registered to another user")
        return existing_pan
    
    # Create new PAN detail
    db_pan = models.PANDetail(
        user_id=current_user.id,
        pan_number=pan_data.pan_number,
        holder_name=pan_data.holder_name
    )
    db.add(db_pan)
    db.commit()
    db.refresh(db_pan)
    
    return db_pan

@router.get("/pan", response_model=List[PANDetail])
def get_pan_details(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(models.PANDetail).filter(
        models.PANDetail.user_id == current_user.id
    ).all()

@router.post("/platform-accounts", response_model=PlatformAccount)
def add_platform_account(
    account_data: PlatformAccountCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify PAN belongs to user
    pan_detail = db.query(models.PANDetail).filter(
        models.PANDetail.id == account_data.pan_id,
        models.PANDetail.user_id == current_user.id
    ).first()
    
    if not pan_detail:
        raise HTTPException(status_code=404, detail="PAN detail not found")
    
    # Create platform account
    db_account = models.PlatformAccount(
        user_id=current_user.id,
        pan_id=account_data.pan_id,
        platform=account_data.platform,
        client_id=account_data.client_id,
        nickname=account_data.nickname,
        account_type=account_data.account_type
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account

@router.get("/platform-accounts", response_model=List[PlatformAccount])
def get_platform_accounts(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(models.PlatformAccount).filter(
        models.PlatformAccount.user_id == current_user.id,
        models.PlatformAccount.is_active == True
    ).all()

@router.post("/portfolios", response_model=Portfolio)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_portfolio = models.Portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        description=portfolio_data.description
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    
    return db_portfolio

@router.get("/portfolios", response_model=List[Portfolio])
def get_portfolios(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Portfolio).filter(
        models.Portfolio.user_id == current_user.id
    ).all()

@router.get("/summary")
def get_portfolio_summary(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get all holdings across all platform accounts
    holdings = db.query(models.Holding).join(
        models.PlatformAccount
    ).filter(
        models.PlatformAccount.user_id == current_user.id
    ).all()
    
    if not holdings:
        return PortfolioSummary(
            total_value=0,
            total_investment=0,
            total_pnl=0,
            total_pnl_percentage=0,
            holdings_count=0,
            asset_allocation={},
            platform_allocation={}
        )
    
    total_value = sum(h.current_value or 0 for h in holdings)
    total_investment = sum(h.quantity * h.average_price for h in holdings)
    total_pnl = sum(h.pnl or 0 for h in holdings)
    
    # Calculate asset allocation
    asset_allocation = {}
    for holding in holdings:
        asset_type = holding.asset_type.value
        if asset_type not in asset_allocation:
            asset_allocation[asset_type] = 0
        asset_allocation[asset_type] += holding.current_value or 0
    
    # Calculate platform allocation
    platform_allocation = {}
    for holding in holdings:
        platform = holding.platform_account.platform.value
        if platform not in platform_allocation:
            platform_allocation[platform] = 0
        platform_allocation[platform] += holding.current_value or 0
    
    # Convert to percentages
    if total_value > 0:
        asset_allocation = {k: (v/total_value)*100 for k, v in asset_allocation.items()}
        platform_allocation = {k: (v/total_value)*100 for k, v in platform_allocation.items()}
    
    return PortfolioSummary(
        total_value=total_value,
        total_investment=total_investment,
        total_pnl=total_pnl,
        total_pnl_percentage=(total_pnl/total_investment)*100 if total_investment > 0 else 0,
        holdings_count=len(holdings),
        asset_allocation=asset_allocation,
        platform_allocation=platform_allocation
    )

@router.get("/holdings", response_model=List[HoldingWithDetails])
def get_holdings(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    holdings = db.query(models.Holding).join(
        models.PlatformAccount
    ).filter(
        models.PlatformAccount.user_id == current_user.id
    ).all()
    
    return holdings

@router.post("/holdings", response_model=HoldingWithDetails)
def create_holding(
    holding_data: HoldingCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify platform account belongs to user
    platform_account = db.query(models.PlatformAccount).filter(
        models.PlatformAccount.id == holding_data.platform_account_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not platform_account:
        raise HTTPException(status_code=404, detail="Platform account not found")
    
    # Create new holding
    db_holding = models.Holding(
        symbol=holding_data.symbol,
        exchange=holding_data.exchange,
        asset_type=holding_data.asset_type,
        quantity=holding_data.quantity,
        average_price=holding_data.average_price,
        platform_account_id=holding_data.platform_account_id,
        portfolio_id=holding_data.portfolio_id,
        isin=holding_data.isin
    )
    
    # Calculate current value and P&L if current price is provided
    if holding_data.current_price:
        db_holding.current_price = holding_data.current_price
        db_holding.current_value = holding_data.quantity * holding_data.current_price
        db_holding.pnl = (holding_data.current_price - holding_data.average_price) * holding_data.quantity
        db_holding.pnl_percentage = ((holding_data.current_price - holding_data.average_price) / holding_data.average_price) * 100
    
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    
    return db_holding

@router.delete("/holdings/{holding_id}")
def delete_holding(
    holding_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify holding belongs to user
    holding = db.query(models.Holding).join(
        models.PlatformAccount
    ).filter(
        models.Holding.id == holding_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    db.delete(holding)
    db.commit()
    
    return {"message": "Holding deleted successfully"}

@router.put("/holdings/{holding_id}")
def update_holding(
    holding_id: int,
    quantity: float = None,
    average_price: float = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify holding belongs to user
    holding = db.query(models.Holding).join(
        models.PlatformAccount
    ).filter(
        models.Holding.id == holding_id,
        models.PlatformAccount.user_id == current_user.id
    ).first()
    
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    if quantity is not None:
        holding.quantity = quantity
    if average_price is not None:
        holding.average_price = average_price
    
    # Update current value and P&L
    if holding.current_price:
        holding.current_value = holding.quantity * holding.current_price
        holding.pnl = (holding.current_price - holding.average_price) * holding.quantity
        holding.pnl_percentage = ((holding.current_price - holding.average_price) / holding.average_price) * 100
    
    db.commit()
    db.refresh(holding)
    
    return holding