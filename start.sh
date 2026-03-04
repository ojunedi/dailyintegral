#!/bin/bash

# Daily Integral Challenge Startup Script
# Starts both backend Flask server and frontend Vite dev server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}   Daily Integral Challenge Launcher    ${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

# Check if virtual environment exists
if [ ! -d ".env" ]; then
    echo -e "${RED}Error: Virtual environment '.env' not found!${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .env
    echo -e "${YELLOW}Installing dependencies...${NC}"
    ./.env/bin/pip install -r requirements.txt
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend && npm install && cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

# Parse arguments
USE_SEPARATE_TERMINALS=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
    case $arg in
        --separate|-s)
            USE_SEPARATE_TERMINALS=true
            ;;
        --backend|-b)
            BACKEND_ONLY=true
            ;;
        --frontend|-f)
            FRONTEND_ONLY=true
            ;;
        --help|-h)
            echo ""
            echo "Usage: ./start.sh [options]"
            echo ""
            echo "Options:"
            echo "  --separate, -s    Open backend and frontend in separate Terminal windows"
            echo "  --backend, -b     Start only the backend server"
            echo "  --frontend, -f    Start only the frontend server"
            echo "  --help, -h        Show this help message"
            echo ""
            exit 0
            ;;
    esac
done

# Function to start backend
start_backend() {
    echo -e "${GREEN}Starting Flask backend on http://localhost:5000${NC}"
    cd "$PROJECT_DIR"
    ./.env/bin/python run.py
}

# Function to start frontend
start_frontend() {
    echo -e "${GREEN}Starting Vite frontend on http://localhost:3000${NC}"
    cd "$PROJECT_DIR/frontend"
    npm run dev
}

# Backend only mode
if [ "$BACKEND_ONLY" = true ]; then
    start_backend
    exit 0
fi

# Frontend only mode
if [ "$FRONTEND_ONLY" = true ]; then
    start_frontend
    exit 0
fi

# Separate terminals mode (macOS)
if [ "$USE_SEPARATE_TERMINALS" = true ]; then
    echo -e "${YELLOW}Opening separate terminal windows...${NC}"

    # Open backend in new Terminal window
    osascript -e "tell application \"Terminal\"
        do script \"cd '$PROJECT_DIR' && echo -e '${GREEN}[Backend Server]${NC}' && ./.env/bin/python run.py\"
        set custom title of front window to \"Daily Integral - Backend\"
    end tell"

    sleep 1

    # Open frontend in new Terminal window
    osascript -e "tell application \"Terminal\"
        do script \"cd '$PROJECT_DIR/frontend' && echo -e '${GREEN}[Frontend Server]${NC}' && npm run dev\"
        set custom title of front window to \"Daily Integral - Frontend\"
    end tell"

    echo ""
    echo -e "${GREEN}✓ Backend server: http://localhost:5000${NC}"
    echo -e "${GREEN}✓ Frontend server: http://localhost:3000${NC}"
    echo ""
    echo -e "${YELLOW}Servers started in separate Terminal windows.${NC}"
    echo -e "${YELLOW}Close those windows to stop the servers.${NC}"
    exit 0
fi

# Default: Run both in same terminal with background processes
echo ""

# Function to handle cleanup on script exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    # Kill any remaining child processes
    jobs -p | xargs -r kill 2>/dev/null || true
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start backend in background
echo -e "${GREEN}[Backend]${NC} Starting on http://localhost:5000"
./.env/bin/python run.py &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 2

# Start frontend in background
echo -e "${GREEN}[Frontend]${NC} Starting on http://localhost:3000"
cd frontend && npm run dev &
FRONTEND_PID=$!

cd "$PROJECT_DIR"

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Backend:  http://localhost:5000${NC}"
echo -e "${GREEN}✓ Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for background processes
wait
