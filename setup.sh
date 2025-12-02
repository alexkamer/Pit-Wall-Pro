#!/bin/bash

# F1 WebApp Setup Script
# This script automates the setup process for new users

set -e  # Exit on error

echo "======================================"
echo "F1 WebApp Setup Script"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.12 or higher from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓${NC} Node.js ${NODE_VERSION} found"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✓${NC} uv installed successfully"
else
    echo -e "${GREEN}✓${NC} uv already installed"
fi

echo ""
echo "======================================"
echo "Setting up Backend"
echo "======================================"

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync
echo -e "${GREEN}✓${NC} Backend dependencies installed"

# Create cache directory
mkdir -p f1_cache
echo -e "${GREEN}✓${NC} Cache directory created"

# Check if database exists
if [ -f "f1_data.db" ]; then
    echo -e "${YELLOW}Database already exists. Skipping population.${NC}"
    read -p "Do you want to repopulate the database? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Populating database (this may take a few minutes)..."
        uv run python scripts/populate_espn_final.py
        echo -e "${GREEN}✓${NC} Database populated"
    fi
else
    echo "Populating database (this may take a few minutes)..."
    uv run python scripts/populate_espn_final.py
    echo -e "${GREEN}✓${NC} Database populated"
fi

echo ""
echo "======================================"
echo "Setting up Frontend"
echo "======================================"

cd frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install
echo -e "${GREEN}✓${NC} Frontend dependencies installed"

cd ..

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend (in one terminal):"
echo "   ${GREEN}uv run python -m src.f1_webapp.api.app${NC}"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   ${GREEN}cd frontend && npm run dev${NC}"
echo ""
echo "Then open your browser to:"
echo "   Frontend: ${GREEN}http://localhost:4321${NC}"
echo "   API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "Or use Docker:"
echo "   ${GREEN}docker-compose up${NC}"
echo ""
echo "For more information, see README.md"
echo ""
