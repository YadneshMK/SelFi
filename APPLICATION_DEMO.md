# Finance Investment Tracker - Application Demo

## Application Overview

The Finance Investment Tracker is a full-stack web application built with:
- **Backend**: FastAPI (Python) running on http://localhost:8000
- **Frontend**: Next.js (React/TypeScript) running on http://localhost:3000

## Key Features Implemented

### 1. Landing Page (/)
- Clean, professional design with gradient background
- Clear value proposition
- Features overview (Multi-Platform Support, Investment Analysis, Free APIs)
- Call-to-action buttons for Sign Up and Sign In
- Responsive design for mobile devices

### 2. User Authentication

#### Registration Page (/register)
- Form fields:
  - Email address
  - Username  
  - Password (min 6 characters)
  - Full name (optional)
- Form validation with error messages
- Redirects to login on success

#### Login Page (/login)
- Simple username/password form
- JWT token authentication
- Redirects to dashboard on success
- "Remember me" functionality via localStorage

### 3. Dashboard (/dashboard)

#### Portfolio Summary Cards
- **Total Value**: Current portfolio value in INR
- **Total Investment**: Amount invested
- **Total P&L**: Profit/Loss with percentage
- **Holdings Count**: Number of securities

#### Visual Analytics
- **Asset Allocation Pie Chart**: Shows distribution across Stocks, Mutual Funds, SGBs
- **Platform Allocation Pie Chart**: Shows distribution across different platforms (Zerodha accounts)

#### Quick Actions
- For new users: Prompt to upload data
- Update prices button

### 4. Upload Data (/dashboard/upload)

#### Instructions Section
- Step-by-step guide for Zerodha Console export
- Clear instructions for Holdings and Transactions

#### Upload Interface
- Platform account selector (for multiple Zerodha accounts)
- Upload type selector (Holdings/Transactions)
- Drag-and-drop CSV upload area
- Visual feedback for upload status
- Error handling with clear messages

### 5. Holdings View (/dashboard/holdings)

#### Features
- Comprehensive table with columns:
  - Symbol & Exchange
  - Platform/Account
  - Quantity
  - Average Price
  - Current Price
  - Current Value
  - P&L (with color coding: green for profit, red for loss)
  
#### Filters
- All Holdings
- Stocks only
- Mutual Funds only
- SGBs only

#### Actions
- "Update Prices" button to fetch latest prices from Yahoo Finance/MF API
- Real-time loading states

### 6. Responsive Sidebar Navigation
- Dashboard
- Upload Data
- Holdings
- Reports (planned)
- Settings (planned)
- User profile with logout

## API Endpoints Available

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Portfolio Management
- `POST /api/v1/portfolios/pan` - Add PAN details
- `GET /api/v1/portfolios/pan` - List PAN details
- `POST /api/v1/portfolios/platform-accounts` - Add platform account
- `GET /api/v1/portfolios/platform-accounts` - List platform accounts
- `GET /api/v1/portfolios/summary` - Portfolio summary
- `GET /api/v1/portfolios/holdings` - List all holdings

### Data Import
- `POST /api/v1/uploads/zerodha/holdings` - Upload holdings CSV
- `POST /api/v1/uploads/zerodha/transactions` - Upload transactions CSV
- `GET /api/v1/uploads/import-history` - Import history

### Market Data
- `GET /api/v1/market/stock/{symbol}` - Get stock info
- `GET /api/v1/market/stock/{symbol}/history` - Stock history
- `POST /api/v1/market/stock/bulk-quotes` - Bulk stock quotes
- `GET /api/v1/market/mutual-fund/search` - Search mutual funds
- `GET /api/v1/market/mutual-fund/{scheme_code}` - MF info
- `POST /api/v1/market/update-holdings-prices` - Update all prices

## How to Run the Application

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Set up PostgreSQL and update .env file
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Default Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## User Flow

1. **New User Journey**:
   - Land on homepage → Click "Get Started"
   - Register with email/username/password
   - Login with credentials
   - See empty dashboard with prompt to upload data
   - Add PAN details (Settings - pending)
   - Add platform accounts (Settings - pending)
   - Upload Zerodha CSV from Console
   - View consolidated portfolio
   - Update prices to see current values

2. **Returning User Journey**:
   - Login → Dashboard shows portfolio summary
   - Upload new CSV to update holdings
   - View holdings with filters
   - Check real-time P&L
   - Generate reports (pending)

## Data Sources

- **Portfolio Data**: User-uploaded CSV files from Zerodha Console
- **Stock Prices**: Yahoo Finance API (free)
- **Mutual Fund NAVs**: MF API (free)
- **No broker credentials required** - fully secure

## Key Design Decisions

1. **Privacy First**: No broker login credentials stored
2. **Free Forever**: Only free APIs used
3. **Multi-Account**: PAN-based consolidation
4. **User Control**: Manual CSV uploads for data accuracy
5. **Real-time Updates**: On-demand price refresh

## Current Limitations

1. Manual CSV upload required (no auto-sync)
2. Limited to Zerodha CSV format currently
3. Reports section under development
4. Investment philosophy filters pending
5. Email parsing not yet implemented

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Protected API routes
- No storage of sensitive broker data
- Secure session management

The application provides a solid foundation for tracking investments across multiple accounts with real-time valuations, all using free data sources.