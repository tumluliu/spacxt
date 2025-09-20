#!/bin/bash

# SpacXT Web Application - Stop All Services

echo "🛑 Stopping SpacXT Web Application..."

# Kill processes by port
echo "🔧 Stopping backend (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Backend not running on port 8000"

echo "🎨 Stopping frontend (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Frontend not running on port 3000"

# Kill any remaining Python/Node processes related to our app
echo "🧹 Cleaning up remaining processes..."
pkill -f "main.py" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "✅ All services stopped!"
echo ""
echo "📄 Logs are preserved in logs/ directory"
echo "🚀 To restart, run: ./start-all.sh"
