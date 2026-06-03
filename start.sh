#!/bin/bash

# Daily Integral Challenge Startup Script
# Starts both backend Flask server and frontend Vite dev server

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}   Daily Integral Challenge Launcher    ${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

# Sync dependencies
uv sync --quiet
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend && npm install --silent && cd ..
fi

# Parse arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
    case $arg in
        --backend|-b)  BACKEND_ONLY=true ;;
        --frontend|-f) FRONTEND_ONLY=true ;;
        --debug|-d)
            export FLASK_ENV=dev
            echo -e "${YELLOW}Debug mode enabled${NC}"
            ;;
        --help|-h)
            echo ""
            echo "Usage: ./start.sh [options]"
            echo ""
            echo "  -b, --backend     Start only the backend server"
            echo "  -f, --frontend    Start only the frontend server"
            echo "  -d, --debug       Enable debug mode (random problems)"
            echo "  -h, --help        Show this help message"
            echo ""
            exit 0
            ;;
    esac
done

if [ "$BACKEND_ONLY" = true ]; then
    echo -e "${GREEN}Starting Flask backend on http://localhost:5000${NC}"
    uv run python run.py
    exit 0
fi

if [ "$FRONTEND_ONLY" = true ]; then
    echo -e "${GREEN}Starting Vite frontend on http://localhost:3000${NC}"
    cd frontend && npm run dev
    exit 0
fi

# Default: run both, clean up on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}Stopped${NC}"
}
trap cleanup SIGINT SIGTERM EXIT

uv run python run.py &
BACKEND_PID=$!
sleep 1
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Backend:  http://localhost:5000${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

wait
