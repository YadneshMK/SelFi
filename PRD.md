# Product Requirements Document - Financial Investment Tracker

## Overview

A comprehensive web application to track and analyze financial investments across multiple platforms in the Indian stock market. The application consolidates holdings from various brokers, provides real-time portfolio analytics, and offers investment insights based on proven philosophies.

## Problem Statement

Indian investors often have:
- Multiple demat accounts across different brokers (especially multiple Zerodha accounts)
- No unified view of their complete portfolio
- Difficulty tracking performance across platforms
- Limited access to consolidated analytics without expensive tools
- No easy way to apply investment philosophies to their portfolio

## Solution

A web-based platform that:
1. Consolidates investments across multiple accounts using PAN-based linking
2. Provides real-time portfolio tracking using FREE APIs only
3. Offers investment analysis based on renowned philosophies
4. Generates comprehensive reports for tax and investment planning

## Target Users

1. **Primary Users**: Individual investors with multiple broker accounts
2. **Secondary Users**: Financial advisors managing multiple client portfolios
3. **Tertiary Users**: Investors seeking to apply systematic investment strategies

## Core Features

### 1. Multi-Account Consolidation
- **PAN-based Linking**: Link multiple accounts using PAN number
- **Platform Support**: 
  - Multiple Zerodha accounts (Kite & Coin)
  - Groww
  - Upstox
  - Paytm Money
- **Account Nicknames**: Custom names for easy identification

### 2. Data Import Methods
- **CSV Upload**: 
  - Zerodha Console exports (Holdings, Tradebook, P&L)
    - Auto-detects new Zerodha Console format (2025)
    - Handles empty rows and different column names
    - Backward compatible with old format
    - Smart header detection (finds actual data start)
    - ETF symbol mapping for consistency
  - Generic CSV support for non-Zerodha brokers
    - Auto-detects column mappings
    - Symbol cleanup and normalization
    - Comprehensive symbol mappings (e.g., Larsen & Toubro → LT)
  - File validation:
    - Type checking (.csv and .xlsx/.xls)
    - Size limits (10MB max)
    - Empty file detection
    - Duplicate prevention by platform_account_id
  - Import features:
    - Progress tracking
    - Auto price fetching post-import
    - Import history tracking
    - Error handling with detailed messages
    - Warning system for missing fields
- **Excel Upload**:
  - Multi-sheet support (.xlsx and .xls files)
  - Automatic sheet type detection:
    - Stock sheets (based on column names)
    - Mutual fund sheets (NAV, Units, Scheme Name)
  - Sheet-by-sheet processing and summaries
  - Handles missing data with warnings
- **Statement Parsing**: (Phase 2)
  - CAMS/KFintech consolidated statements
  - CDSL/NSDL e-CAS
- **Email Integration**: Contract note parsing (Phase 2)

### 3. Portfolio Analytics
- **Real-time Valuation**: Current prices from free APIs
- **Performance Metrics**:
  - Total P&L (absolute and percentage)
  - XIRR calculations
  - Asset allocation charts (stocks, ETFs, mutual funds, SGBs, REITs)
  - Platform-wise distribution
- **Historical Tracking**: Performance over time
- **Asset Categorization**: 
  - Automatic detection of ETFs based on ISIN and symbol patterns
  - REIT detection (symbols ending with -RR, -RT, or containing 'REIT')
  - Smart asset type classification during import

### 4. Investment Philosophy Filters

#### Warren Buffett Criteria
- Consistent earnings growth
- High ROE (>15%)
- Low debt-to-equity
- Strong moat indicators

#### Peter Lynch Approach
- PEG ratio analysis
- Growth at reasonable price
- Sector diversification
- Small-cap opportunities

#### Mohnish Pabrai Checklist
- Margin of safety
- Business quality metrics
- Management integrity indicators
- Competitive advantages

#### Parag Parikh Philosophy
- Behavioral finance principles
- Contrarian opportunities
- Quality over momentum
- Long-term focus

#### Coffee Can Investing
- Buy and forget approach
- 10+ year holding criteria
- Quality filters
- Minimal churn

### 5. Screening & Analysis

**Custom Screening Formula**:
```
CFO To Net Profit Ratio > 1 AND 
Dividend Payout Ratio < 40 AND 
Sales growth 7Years > 11 AND 
Profit growth 7Years > 11 AND 
Interest Coverage Ratio > 4 AND 
Debt To Profit <= 2 AND 
Market Capitalization > 30000
```

### 6. Technical Analysis
- Price charts with indicators
- Moving averages (SMA, EMA)
- RSI, MACD, Bollinger Bands
- Volume analysis
- User confirmation on signal interpretation

### 7. Fundamental Analysis
- Financial ratios from annual reports
- Peer comparison
- Industry benchmarking
- SWOT analysis from reports
- Chairman's letter sentiment analysis

### 8. News & Updates
- Aggregated news for portfolio companies
- Corporate actions tracking
- Regulatory filings alerts
- Sentiment analysis
- Custom alerts

### 9. Reporting
- Capital gains reports (LTCG/STCG)
- Tax harvesting suggestions
- Portfolio performance reports
- Asset allocation analysis
- Export to PDF/Excel

## Technical Requirements

### Technology Stack
- **Backend**: 
  - FastAPI (Python 3.9+)
  - SQLAlchemy ORM with SQLite database
  - Pandas for CSV parsing
  - yfinance for stock data
  - JWT tokens with bcrypt password hashing
  - CORS middleware for API access
- **Frontend**: 
  - Next.js 15 with App Router
  - TypeScript for type safety
  - Tailwind CSS for styling
  - Recharts for data visualization
  - react-dropzone for file uploads
  - Lucide React for icons
- **State Management**: 
  - Zustand for global state
  - Axios with interceptors for API calls
- **Development**:
  - Hot reload for both frontend and backend
  - Environment variables for configuration
  - Comprehensive error logging

### APIs (FREE Only)
1. **Yahoo Finance**: Stock prices and historical data
2. **MF API**: All mutual fund NAVs
3. **Alpha Vantage**: Additional market data (free tier)
4. **News APIs**: Financial news aggregation

### Data Sources
1. Broker CSV exports (primary source)
2. Email contract notes
3. Consolidated account statements
4. Public company filings

### Security
- JWT-based authentication
- Encrypted data storage
- No storage of broker credentials
- PAN used only for linking
- Regular security audits

## User Journey

### New User Flow
1. Register with email/username
2. Add PAN details
3. Link broker accounts (client ID + nickname)
4. Upload CSV exports
5. View consolidated portfolio
6. Explore analytics

### Returning User Flow
1. Login
2. Update holdings via CSV
3. View updated analytics
4. Apply investment filters
5. Generate reports

## UI/UX Requirements

### Design Principles
- Clean, professional interface
- Mobile-responsive design
- Data visualization focus
- Minimal cognitive load
- Fast load times

### Key Screens
1. **Dashboard**: 
   - Portfolio overview with total value, investment, P&L
   - Asset allocation pie chart
   - Platform allocation pie chart
   - Auto-refresh every 30 seconds
   - Manual refresh button
   - Error handling with retry
   - Get started prompt for new users
2. **Holdings**: 
   - Detailed list with filters (All, Stocks, ETFs, Mutual Funds, SGBs, REITs)
   - Filter tabs with count badges showing number of holdings in each category
   - Real-time price updates with progress indicators
   - P&L visualization with up/down arrows
   - Inline editing for quantity and average price
   - Bulk selection and delete
   - Individual delete with confirmation
   - Current value calculations
   - Multiple platform account support:
     - Separate accounts for different asset types
     - Platform column showing account nickname
     - Automatic account assignment based on asset type
   - Warning indicators for missing data:
     - Visual alerts for quantity = 1 (likely missing)
     - Visual alerts for average price = 0
     - Row highlighting for holdings with issues
     - Banner notification with action prompts
     - Hover tooltips explaining the issues
3. **Analytics**: Charts and insights (Phase 2)
4. **Upload**: 
   - Drag-drop CSV/Excel interface with validation
   - Dynamic platform instructions
   - File size limits (10MB)
   - Selected file preview
   - Upload progress tracking
   - Cancel upload option
   - Recent upload history
   - Success navigation to holdings
   - Warning display for missing fields:
     - Symbol-wise missing field list
     - Row number references
     - Default value explanations
   - Excel-specific features:
     - Multi-sheet processing
     - Sheet summaries in success message
     - Automatic type detection per sheet
5. **Reports**: Document generation (Phase 2)
6. **Settings**: Account management (Phase 2)

## Success Metrics

1. **User Engagement**
   - Daily active users
   - CSV uploads per user
   - Features used per session

2. **Portfolio Metrics**
   - Total AUM tracked
   - Number of accounts linked
   - Holdings per user

3. **Performance**
   - Page load time < 2s
   - API response time < 500ms
   - 99.9% uptime

## Constraints

1. **Must use FREE APIs only** - No paid data subscriptions
2. **No automated broker login** - Manual CSV upload only
3. **Indian markets focus** - NSE/BSE stocks, Indian MFs
4. **Data privacy** - No sharing of user data
5. **Regulatory compliance** - No investment advice

## Future Enhancements

1. **Mobile Apps**: iOS and Android native apps
2. **AI Insights**: ML-based recommendations
3. **Social Features**: Investment clubs, idea sharing
4. **Automated Imports**: Browser extensions for auto-download
5. **Global Markets**: US stocks, international funds
6. **Robo-Advisory**: Automated rebalancing suggestions

## Competitive Analysis

### Existing Solutions
1. **Broker Apps**: Limited to single platform
2. **Paid Tools**: Expensive (₹1000-5000/month)
3. **Excel Tracking**: Manual and error-prone
4. **Other Apps**: Limited features or paid APIs

### Our Differentiators
1. **FREE Forever**: No paid APIs or subscriptions
2. **Multi-Account**: Unlimited account linking
3. **Philosophy-Based**: Systematic investment approach
4. **Privacy-First**: No data selling
5. **Indian Market Focus**: Tailored for Indian investors

## Development Phases

### Phase 1 (MVP) - Completed
- User authentication (JWT-based with bcrypt password hashing)
- Multi-account setup with PAN linking
- CSV import with auto-format detection
  - Handles new Zerodha Console format (2025)
  - Generic CSV parser for non-Zerodha sources
  - File validation (type, size limits, empty file checks)
  - Progress tracking during upload
  - Auto-fetch prices after import
  - Comprehensive symbol mapping (36+ mappings)
- Excel import with multi-sheet support
  - Automatic sheet type detection
  - Separate processing for stocks and mutual funds
  - Sheet-by-sheet summaries
- ETF detection and categorization
  - Symbol mapping (MAFSETFINAV -> MAFSETF)
  - ISIN-based detection
- Basic analytics (P&L, allocation charts)
- Portfolio dashboard with:
  - Real-time prices with auto-refresh (30s)
  - Error handling and retry mechanisms
  - Last updated timestamp
  - Asset type and platform formatting
  - Loading states for charts
- Holdings view with:
  - Filtering tabs (All, Stocks, ETFs, Mutual Funds, SGBs, REITs)
  - Count badges on each tab showing number of holdings
  - REIT support as a separate asset class
  - Multiple platform accounts for organization:
    - Main Account (stocks)
    - ETF Account
    - Mutual Funds Account
    - REITs Account
    - Custom accounts for different brokers
  - Inline editing with validation
  - Bulk delete functionality
  - Real-time price updates with progress
  - Checkbox selection
  - Warning system for missing data:
    - Visual indicators (icons, colors)
    - Row highlighting
    - Banner notifications
    - Hover tooltips
  - Responsive table with horizontal scroll
  - Minimum column widths to prevent overlapping
- Upload page with:
  - Dynamic platform account loading
  - Platform-specific instructions
  - CSV/Excel file support
  - File preview and validation
  - Upload history tracking
  - Cancel upload functionality
  - Keyboard shortcuts (Ctrl+U)
  - Warning display for missing fields
- Responsive UI with:
  - Visible logout functionality
  - Focus indicators and ARIA labels
  - Error states and loading indicators
  - Success navigation flows

### Phase 2 (Current)
- Advanced analytics
- Investment filters
- Report generation
- Email parsing

### Phase 3 (Future)
- Mobile apps
- AI features
- Social features
- Advanced automation

## Risk Mitigation

1. **API Dependency**: Multiple fallback APIs
2. **Data Accuracy**: User verification prompts
3. **Scalability**: Cloud-native architecture
4. **Security**: Regular audits and updates
5. **Compliance**: Legal review of features