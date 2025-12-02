# F1 WebApp Setup Script for Windows
# This script automates the setup process for new users

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "F1 WebApp Setup Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "Error: Python 3 is not installed" -ForegroundColor Red
    Write-Host "Please install Python 3.12 or higher from https://www.python.org/downloads/"
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js is not installed" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
}

# Check if uv is installed
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✓ uv already installed" -ForegroundColor Green
} catch {
    Write-Host "uv is not installed. Installing..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    Write-Host "✓ uv installed successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setting up Backend" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Install Python dependencies
Write-Host "Installing Python dependencies..."
uv sync
Write-Host "✓ Backend dependencies installed" -ForegroundColor Green

# Create cache directory
if (-not (Test-Path "f1_cache")) {
    New-Item -ItemType Directory -Path "f1_cache" | Out-Null
    Write-Host "✓ Cache directory created" -ForegroundColor Green
} else {
    Write-Host "✓ Cache directory already exists" -ForegroundColor Green
}

# Check if database exists
if (Test-Path "f1_data.db") {
    Write-Host "Database already exists. Skipping population." -ForegroundColor Yellow
    $response = Read-Host "Do you want to repopulate the database? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Populating database (this may take a few minutes)..."
        uv run python scripts/populate_espn_final.py
        Write-Host "✓ Database populated" -ForegroundColor Green
    }
} else {
    Write-Host "Populating database (this may take a few minutes)..."
    uv run python scripts/populate_espn_final.py
    Write-Host "✓ Database populated" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setting up Frontend" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Set-Location frontend

# Install Node dependencies
Write-Host "Installing Node.js dependencies..."
npm install
Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:"
Write-Host ""
Write-Host "1. Start the backend (in one terminal):" -ForegroundColor Yellow
Write-Host "   uv run python -m src.f1_webapp.api.app" -ForegroundColor Green
Write-Host ""
Write-Host "2. Start the frontend (in another terminal):" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor Green
Write-Host "   npm run dev" -ForegroundColor Green
Write-Host ""
Write-Host "Then open your browser to:"
Write-Host "   Frontend: http://localhost:4321" -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Or use Docker:"
Write-Host "   docker-compose up" -ForegroundColor Green
Write-Host ""
Write-Host "For more information, see README.md"
Write-Host ""
