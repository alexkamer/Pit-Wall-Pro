# Quick Start Guide

Get F1 WebApp running in 5 minutes!

## Prerequisites

- Python 3.12+
- Node.js 18+
- Git

## Installation Methods

### Method 1: Automated Setup (Recommended)

**macOS/Linux:**
```bash
git clone https://github.com/yourusername/f1_webapp.git
cd f1_webapp
./setup.sh
```

**Windows:**
```powershell
git clone https://github.com/yourusername/f1_webapp.git
cd f1_webapp
.\setup.ps1
```

The script will:
- Install all dependencies
- Set up the database
- Configure the environment

### Method 2: Manual Setup

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/f1_webapp.git
cd f1_webapp
```

**2. Backend setup:**
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install Python dependencies
uv sync

# Populate the database (takes 2-3 minutes)
uv run python scripts/populate_espn_final.py
```

**3. Frontend setup:**
```bash
cd frontend
npm install
cd ..
```

### Method 3: Docker (Easiest)

```bash
git clone https://github.com/yourusername/f1_webapp.git
cd f1_webapp

# Start everything
docker-compose up
```

That's it! Docker handles all the setup.

## Running the Application

### Without Docker

**Terminal 1 - Backend:**
```bash
uv run python -m src.f1_webapp.api.app
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### With Docker

```bash
docker-compose up
```

## Access the Application

Once running, open your browser to:

- **Frontend**: http://localhost:4321
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## What's Next?

### Explore the Data

**View 2024 Championship Standings:**
- Navigate to http://localhost:4321/standings/2024

**Try the API:**
```bash
# Get driver standings
curl http://localhost:8000/espn/standings/2024?type=driver

# Get race results
curl http://localhost:8000/db/races/2024

# Get session data (telemetry)
curl http://localhost:8000/fastf1/session/2024/Monaco/Q
```

### Common Tasks

**Update the database:**
```bash
uv run python scripts/populate_espn_final.py
```

**Update team logos:**
```bash
uv run python scripts/populate_team_logos.py
```

**Clear FastF1 cache:**
```bash
rm -rf f1_cache/*
```

## Troubleshooting

### Backend won't start

**Error: "No module named 'src'"**
```bash
# Make sure you're in the project root directory
pwd  # Should end with /f1_webapp

# Reinstall dependencies
uv sync
```

**Error: "Database is locked"**
```bash
# Stop all running instances and restart
pkill -f "python -m src.f1_webapp"
uv run python -m src.f1_webapp.api.app
```

### Frontend won't start

**Error: "Cannot find module"**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Error: "Port 4321 already in use"**
```bash
# Kill the process using the port
lsof -ti:4321 | xargs kill -9  # macOS/Linux
# or change the port in astro.config.mjs
```

### Docker issues

**Error: "Cannot connect to Docker daemon"**
```bash
# Make sure Docker Desktop is running
# Then try again:
docker-compose up
```

**Rebuild containers after code changes:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## Need Help?

- Check the full [README.md](./README.md)
- Read the [documentation](./docs/)
- Review [Contributing Guide](./CONTRIBUTING.md)
- Open an issue on GitHub

## Performance Note

The first time you request telemetry data (FastF1), it will download and cache the data. This can take 30-60 seconds. Subsequent requests will be instant.

---

**Enjoy exploring F1 data!** 🏎️💨
