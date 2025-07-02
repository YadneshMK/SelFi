# Finance Investment Tracker - Frontend

Next.js frontend for the Financial Investment Tracker application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy `.env.local.example` to `.env.local`:
```bash
cp .env.local.example .env.local
```

3. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Features

- User authentication (register/login)
- Dashboard with portfolio overview
- CSV upload for Zerodha data
- Portfolio analytics with charts
- Multi-account support via PAN linking

## Pages

- `/` - Landing page
- `/login` - User login
- `/register` - User registration
- `/dashboard` - Main dashboard
- `/dashboard/upload` - CSV upload interface
- `/dashboard/holdings` - View holdings (to be implemented)
- `/dashboard/reports` - Analytics reports (to be implemented)
- `/dashboard/settings` - Account settings (to be implemented)

## Tech Stack

- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- React Hook Form
- Recharts for data visualization
- Axios for API calls
- Zustand for state management
