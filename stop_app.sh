#!/bin/bash

echo "🛑 Stopping Finance Investment Tracker..."

# Kill backend
pkill -f "uvicorn app.main:app" 2>/dev/null

# Kill frontend
pkill -f "next dev" 2>/dev/null

echo "✅ All services stopped"