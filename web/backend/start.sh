#!/bin/bash

# SpacXT Web Backend Startup Script

echo "🚀 Starting SpacXT Spatial Context API..."

# Navigate to project root (where pyproject.toml is)
PROJECT_ROOT="$(dirname "$0")/../.."
cd "$PROJECT_ROOT"

# Check if we can run poetry commands
POETRY_PATH="/Users/luliu/.local/bin/poetry"
if ! $POETRY_PATH --version &> /dev/null; then
    echo "❌ Cannot access Poetry at $POETRY_PATH. Please make sure Poetry is installed."
    exit 1
fi

# Install dependencies with web extras (if not already installed)
echo "📦 Ensuring web dependencies are installed..."
$POETRY_PATH install --extras web --no-dev

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo "🔌 WebSocket endpoint: ws://localhost:8000/ws/default"

# Run from web/backend directory but with Poetry from root
cd web/backend
$POETRY_PATH run python main.py
