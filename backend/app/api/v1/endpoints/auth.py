from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.database import get_db
from app.db import models
from app.schemas.user import User, UserCreate, Token
from app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/register", response_model=User)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(
        (models.User.email == user_data.email) | 
        (models.User.username == user_data.username)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    db_user = models.User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user