# Data Retrieval Methods - FREE APIs Only

## Overview

This document outlines all the FREE methods available for retrieving financial data for the Investment Tracker application. All methods listed here are completely free and do not require any paid subscriptions.

## 1. Stock Market Data

### Yahoo Finance (yfinance)
- **What**: Real-time and historical stock prices
- **Coverage**: NSE, BSE, and global markets
- **Data Available**:
  - Current price, day change
  - 52-week high/low
  - Market cap, P/E ratio, dividend yield
  - Historical OHLCV data
  - Financial statements (limited)
- **Implementation**: Python yfinance library
- **Limits**: No official rate limits, but respectful usage recommended

```python
import yfinance as yf
ticker = yf.Ticker("RELIANCE.NS")  # .NS for NSE, .BO for BSE
info = ticker.info  # Current data
history = ticker.history(period="1mo")  # Historical data
```

### Alpha Vantage (Free Tier)
- **What**: Alternative source for market data
- **API Key**: Free with registration
- **Limits**: 5 API calls/minute, 500 calls/day
- **Best For**: Backup when Yahoo Finance is down

## 2. Mutual Fund Data

### MF API (mfapi.in)
- **What**: Complete mutual fund NAV data
- **Coverage**: All Indian mutual funds
- **Data Available**:
  - Current and historical NAV
  - Fund house, category, type
  - Complete fund list
- **No Registration Required**
- **No Rate Limits**

```python
import requests

# Get fund info
response = requests.get("https://api.mfapi.in/mf/118550")

# Search funds
response = requests.get("https://api.mfapi.in/mf/search?q=axis")
```

## 3. Portfolio Data Import

### CSV Exports (Primary Method)

#### Zerodha Console
1. **Holdings Export**:
   - Login to console.zerodha.com
   - Portfolio → Holdings → Download
   - Contains: Symbol, Qty, Avg Cost, LTP, P&L

2. **Tradebook Export**:
   - Reports → Tradebook
   - Select date range → Download
   - Contains: All transactions

3. **P&L Report**:
   - Reports → P&L
   - Tax P&L for realized gains
   - Contains: Buy/sell dates, quantities, P&L

#### Other Brokers
- **Groww**: Account → Reports → Export
- **Upstox**: Reports → Holdings/Transactions
- **Paytm Money**: Portfolio → Download Statement

### CAMS/KFintech Statements
- **What**: Consolidated mutual fund statements
- **How**: Email request or online generation
- **Contains**: All MF holdings across AMCs
- **Format**: PDF (requires parsing)

### CDSL/NSDL e-CAS
- **What**: Consolidated demat holdings
- **How**: Monthly email or on-demand
- **Contains**: All stocks, bonds, ETFs
- **Format**: PDF password-protected

## 4. Email Integration

### Contract Note Parsing
- **Method**: IMAP email access
- **Process**:
  1. Connect to email via IMAP
  2. Filter contract note emails
  3. Download PDF attachments
  4. Parse transaction details
- **Data**: Individual trades with charges

```python
import imaplib
import email

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(email_user, email_pass)
mail.select('inbox')
```

## 5. Financial Statements

### Annual Reports
- **BSE/NSE Websites**: Direct PDF downloads
- **Company Websites**: Investor relations section
- **Purpose**: SWOT analysis, financial ratios

### Screener.in (Web Scraping)
- **What**: Financial data aggregator
- **Method**: BeautifulSoup scraping
- **Data**: Ratios, peer comparison
- **Note**: Respectful scraping with delays

## 6. News and Updates

### Google News RSS
- **What**: Company-specific news
- **Method**: RSS feed parsing
- **No API Key Required**

```python
import feedparser
feed = feedparser.parse(f'https://news.google.com/rss/search?q={company_name}')
```

### BSE/NSE Announcements
- **What**: Official corporate announcements
- **Method**: Website API/scraping
- **Data**: Board meetings, results, corporate actions

## 7. Implementation Priority

### Phase 1 (Completed)
1. ✅ Zerodha CSV parsing
2. ✅ Yahoo Finance integration
3. ✅ MF API integration

### Phase 2 (In Progress)
1. ⏳ Email contract note parsing
2. ⏳ Other broker CSV formats
3. ⏳ CAMS statement parsing

### Phase 3 (Planned)
1. 📋 e-CAS integration
2. 📋 News aggregation
3. 📋 Annual report analysis

## 8. Data Storage Strategy

### Local Caching
- Cache API responses for 15 minutes
- Store historical data permanently
- Update prices on-demand

### Database Schema
- Flexible to handle multiple sources
- Source tracking for data lineage
- Conflict resolution rules

## 9. Error Handling

### API Failures
- Fallback to cached data
- Try alternative sources
- User notification

### Parsing Errors
- Manual mapping option
- Error reporting
- Partial import support

## 10. Best Practices

1. **Rate Limiting**: Implement delays between API calls
2. **Caching**: Reduce API load with smart caching
3. **User Consent**: Clear data usage disclosure
4. **Error Recovery**: Graceful degradation
5. **Data Validation**: Verify imported data accuracy

## 11. Legal Considerations

- All methods use publicly available data
- No broker API credentials stored
- User uploads their own data
- No automated trading capabilities
- Educational/informational use only

## 12. Alternative Free Sources

### For Future Exploration
1. **Quandl Free Tier**: Limited historical data
2. **IEX Cloud Free**: US markets (for future)
3. **Twelve Data Free**: Another backup option
4. **RapidAPI Free Tiers**: Various financial APIs

## Summary

The application relies primarily on:
1. **User-uploaded CSVs** for portfolio data (most reliable)
2. **Yahoo Finance** for real-time stock prices (primary)
3. **MF API** for mutual fund NAVs (comprehensive)
4. **Email parsing** for automated updates (convenient)

This combination ensures:
- ✅ Zero API costs
- ✅ Reliable data access
- ✅ Complete portfolio coverage
- ✅ Real-time updates
- ✅ Historical tracking