# Financial Investment Tracker

A comprehensive web application for tracking financial investments across multiple platforms in the Indian stock market. Built with FastAPI backend and Next.js frontend.

## Features

- **Multi-Platform Support**: Track investments from multiple Zerodha accounts, Groww, and other platforms
- **Portfolio Consolidation**: Link multiple accounts via PAN for unified view
- **CSV Import**: Import holdings and transactions from Zerodha Console exports
- **Free APIs Only**: Uses Yahoo Finance for stocks and MF API for mutual funds
- **Real-time Updates**: Fetch current prices and calculate P&L
- **Investment Analysis**: Portfolio allocation charts and performance metrics

## Tech Stack

### Backend (FastAPI)
- FastAPI with async support
- PostgreSQL database
- SQLAlchemy ORM
- JWT authentication
- Yahoo Finance API (yfinance)
- MF API for mutual funds
- Pandas for CSV processing

### Frontend (Next.js)
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Recharts for data visualization
- React Hook Form
- Zustand for state management

## Project Structure

```
Finance App/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configurations
│   │   ├── db/          # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   └── requirements.txt
│
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # App routes
│   │   ├── components/ # React components
│   │   └── lib/        # Utilities
│   └── package.json
│
└── docs/               # Documentation
    ├── PRD.md
    ├── TODO.md
    └── DATA_RETRIEVAL_METHODS.md
```

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Run the backend:
```bash
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment:
```bash
cp .env.local.example .env.local
```

4. Run the frontend:
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

## Usage

1. **Register/Login**: Create an account or login
2. **Add PAN Details**: Link your PAN for account consolidation
3. **Add Platform Accounts**: Add your Zerodha/other platform accounts
4. **Import Data**: Upload CSV exports from Zerodha Console
5. **View Dashboard**: See portfolio overview and analytics
6. **Update Prices**: Fetch latest prices for all holdings

## Data Sources (Free APIs)

- **Stocks**: Yahoo Finance (via yfinance)
- **Mutual Funds**: MF API (mfapi.in)
- **Portfolio Data**: CSV exports from broker platforms

## Investment Features (Planned)

- Investment philosophy filters (Buffett, Lynch, Pabrai, etc.)
- Technical and fundamental analysis
- Annual report analysis with SWOT
- Custom screening formulas
- News aggregation for holdings

## License

This project is for personal use and educational purposes.