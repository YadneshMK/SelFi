#!/bin/bash

echo "🔧 Setting up Finance Investment Tracker..."
echo ""

# Check Python
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found: $(python3 --version)"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ Python found: $(python --version)"
    PYTHON_CMD="python"
else
    echo "❌ Python is not installed. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
echo "Checking Node.js installation..."
if command -v node &> /dev/null; then
    echo "✅ Node.js found: $(node --version)"
else
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

# Setup Backend
echo ""
echo "Setting up Backend..."
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "Installing backend dependencies (this may take a minute)..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating backend .env file..."
    cp .env.example .env 2>/dev/null || echo "DATABASE_URL=sqlite:///./finance_app.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30" > .env
fi

cd ..

# Setup Frontend
echo ""
echo "Setting up Frontend..."
cd frontend

# Install dependencies
echo "Installing frontend dependencies (this may take a minute)..."
npm install

# Create .env.local file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating frontend .env.local file..."
    cp .env.local.example .env.local 2>/dev/null || echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
fi

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application, run:"
echo "./start_app.sh"
echo ""
echo "Or start services manually:"
echo "Backend: cd backend && uvicorn app.main:app --reload"
echo "Frontend: cd frontend && npm run dev"