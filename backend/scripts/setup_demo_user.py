#!/usr/bin/env python3
"""
Script to set up demo user with default platform accounts
"""
import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import User, PAN, PlatformAccount
from app.core.config import settings

def setup_demo_user():
    db = SessionLocal()
    try:
        # Find demo user
        user = db.query(User).filter(User.username == "demo").first()
        if not user:
            print("Demo user not found!")
            return
        
        print(f"Found user: {user.username} (ID: {user.id})")
        
        # Check if PAN exists
        pan = db.query(PAN).filter(PAN.user_id == user.id).first()
        if not pan:
            # Create PAN for demo user
            pan = PAN(
                pan_number="DEMOP1234A",
                user_id=user.id
            )
            db.add(pan)
            db.commit()
            print(f"Created PAN: {pan.pan_number}")
        else:
            print(f"PAN already exists: {pan.pan_number}")
        
        # Check if platform accounts exist
        existing_accounts = db.query(PlatformAccount).filter(
            PlatformAccount.pan_id == pan.id
        ).all()
        
        if not existing_accounts:
            # Create default platform accounts
            platforms = [
                {
                    "platform": "ZERODHA",
                    "client_id": "DEMO001",
                    "nickname": "Demo Zerodha Account",
                    "account_type": "DEMAT"
                },
                {
                    "platform": "GROWW",
                    "client_id": "DEMO002",
                    "nickname": "Demo Groww Account",
                    "account_type": "DEMAT"
                }
            ]
            
            for platform_data in platforms:
                account = PlatformAccount(
                    pan_id=pan.id,
                    **platform_data
                )
                db.add(account)
                print(f"Created platform account: {platform_data['platform']} - {platform_data['client_id']}")
            
            db.commit()
        else:
            print(f"Platform accounts already exist: {len(existing_accounts)} accounts")
            for account in existing_accounts:
                print(f"  - {account.platform} ({account.client_id})")
        
        print("\nDemo user setup complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_demo_user()