from fastapi import APIRouter
from app.api.v1.endpoints import auth, portfolios, uploads, market

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(market.router, prefix="/market", tags=["market"])