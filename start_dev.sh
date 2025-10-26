#!/bin/bash

# Start script for MOV Report Extraction System
# Starts both backend API and frontend development server

echo "🚀 Starting MOV Report Extraction System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend
echo "🔧 Starting Backend API..."
source venv/bin/activate
python src/api/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend running on http://localhost:8000 (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 2

# Start frontend
echo "🎨 Starting Frontend Dev Server..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"

echo ""
echo "✅ System started successfully!"
echo ""
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:5173"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "To stop both services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or press Ctrl+C to stop this script"

# Save PIDs to file for easy cleanup
mkdir -p logs
echo "$BACKEND_PID $FRONTEND_PID" > logs/pids.txt

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
