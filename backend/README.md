# Finance Investment Tracker - Backend

FastAPI backend for tracking financial investments across multiple platforms.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database

3. Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Features

- JWT Authentication
- Multi-account support via PAN linking
- CSV import for Zerodha Console exports
- Portfolio tracking across platforms
- RESTful API with automatic documentation

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user

### Portfolio Management
- `POST /api/v1/portfolios/pan` - Add PAN details
- `GET /api/v1/portfolios/pan` - Get user's PAN details
- `POST /api/v1/portfolios/platform-accounts` - Add platform account
- `GET /api/v1/portfolios/platform-accounts` - Get platform accounts
- `GET /api/v1/portfolios/summary` - Get portfolio summary

### Data Import
- `POST /api/v1/uploads/zerodha/holdings` - Upload Zerodha holdings CSV
- `POST /api/v1/uploads/zerodha/transactions` - Upload Zerodha transactions CSV
- `GET /api/v1/uploads/import-history` - Get import history