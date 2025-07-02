#!/bin/bash

echo "🚀 Starting Finance Investment Tracker..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT

# Start Backend
echo -e "${BLUE}Starting Backend (FastAPI)...${NC}"
cd backend
echo "Creating Python virtual environment..."
python3 -m venv venv 2>/dev/null || python -m venv venv
source venv/bin/activate 2>/dev/null || venv\Scripts\activate

echo "Installing backend dependencies..."
pip install -r requirements.txt --quiet

echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start Frontend
echo ""
echo -e "${BLUE}Starting Frontend (Next.js)...${NC}"
cd frontend
echo "Installing frontend dependencies..."
npm install --silent

echo "Starting Next.js development server..."
npm run dev &
FRONTEND_PID=$!
cd ..

# Display access information
echo ""
echo -e "${GREEN}✅ Application is starting!${NC}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user to stop
wait