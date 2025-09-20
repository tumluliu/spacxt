#!/bin/bash

# SpacXT Web Application - Start All Services

echo "🚀 Starting SpacXT Web Application..."
echo "=================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Prerequisites check passed!"
echo ""

# Create log directory
mkdir -p logs

# Start backend in background
echo "🔧 Starting backend service..."
cd backend
./start.sh > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check logs/backend.log for details."
    exit 1
fi

# Test backend health
echo "🏥 Testing backend health..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend might not be fully ready yet (this is normal)"
fi

# Start frontend in background
echo "🎨 Starting frontend service..."
cd frontend
./start.sh > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo "🎉 SpacXT Web Application is starting!"
echo "=================================="
echo "🔗 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 WebSocket: ws://localhost:8000/ws/default"
echo ""
echo "📋 Process IDs:"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📄 Logs:"
echo "   Backend: logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop all services, run: ./stop-all.sh"
echo ""

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
sleep 10

# Try to open browser (optional)
if command_exists open; then
    echo "🌐 Opening browser..."
    open http://localhost:3000
elif command_exists xdg-open; then
    echo "🌐 Opening browser..."
    xdg-open http://localhost:3000
else
    echo "🌐 Please open http://localhost:3000 in your browser"
fi

echo ""
echo "✨ SpacXT is ready! Try these commands:"
echo "   • 'add a coffee cup on the table'"
echo "   • 'What objects are on the table?'"
echo "   • 'move the cup to the stove'"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Keep script running
while true; do
    sleep 1
done
