#!/bin/bash

# SpacXT Web Frontend Startup Script

echo "🚀 Starting SpacXT Web Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start development server
echo "🌐 Starting Vite development server..."
echo "📖 Frontend will be available at http://localhost:3000"
echo "🔗 Make sure the backend is running at http://localhost:8000"

npm run dev
