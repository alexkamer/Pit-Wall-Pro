# F1 WebApp - Project Structure

This document provides a complete overview of the project organization.

## 📁 Directory Structure

```
f1_webapp/
│
├── 📄 README.md                    # Main project documentation
├── 📄 QUICKSTART.md                # 5-minute setup guide
├── 📄 CONTRIBUTING.md              # Contribution guidelines
├── 📄 LICENSE                      # MIT License
├── 📄 PROJECT_STRUCTURE.md         # This file
│
├── 🐍 Backend Files
│   ├── pyproject.toml              # Python dependencies (uv)
│   ├── uv.lock                     # Locked dependency versions
│   ├── .python-version             # Python version requirement
│   └── f1_data.db                  # SQLite database (generated)
│
├── 🐳 Docker Files
│   ├── docker-compose.yml          # Multi-container orchestration
│   ├── Dockerfile.backend          # Backend container definition
│   ├── .dockerignore               # Docker build exclusions
│
├── 🛠️ Setup Scripts
│   ├── setup.sh                    # Automated setup (macOS/Linux)
│   └── setup.ps1                   # Automated setup (Windows)
│
├── 🗂️ Source Code
│   └── src/
│       └── f1_webapp/
│           ├── __init__.py
│           ├── api/                # FastAPI backend
│           │   ├── app.py          # Main API application
│           │   ├── routes/         # API endpoints
│           │   └── models/         # Database models
│           ├── espn/               # ESPN API client
│           │   ├── client.py       # ESPN API wrapper
│           │   └── models.py       # Data models
│           └── fastf1/             # FastF1 wrapper
│               └── client.py       # FastF1 client
│
├── 📜 Database Scripts
│   └── scripts/
│       ├── README.md               # Scripts documentation
│       ├── populate_espn_final.py  # Main database population
│       ├── populate_team_logos.py  # Team logo scraper
│       ├── populate_drivers.py     # Driver data updater
│       ├── populate_races.py       # Race data population
│       ├── update_db.py            # Incremental updates
│       └── migrate_to_espn_ids.py  # Data migration tool
│
├── 🎨 Frontend
│   └── frontend/
│       ├── package.json            # Node.js dependencies
│       ├── astro.config.mjs        # Astro configuration
│       ├── tsconfig.json           # TypeScript config
│       ├── Dockerfile              # Frontend container
│       ├── src/
│       │   ├── pages/              # Astro pages (routes)
│       │   │   ├── index.astro     # Home page
│       │   │   └── standings/      # Standings pages
│       │   ├── components/         # React components
│       │   │   ├── StandingsTable.tsx
│       │   │   ├── RaceResults.tsx
│       │   │   └── TelemetryChart.tsx
│       │   ├── layouts/            # Page layouts
│       │   └── styles/             # CSS/Tailwind
│       ├── public/                 # Static assets
│       │   ├── flags/              # Country flags
│       │   └── logos/              # Team logos
│       └── dist/                   # Build output (generated)
│
├── 📚 Documentation
│   └── docs/
│       ├── ARCHITECTURE.md         # System architecture
│       ├── DATABASE_SCHEMA.md      # Database design
│       ├── API.md                  # API endpoint reference
│       ├── API_INTEGRATION_STRATEGY.md  # Integration guide
│       ├── ESPN_F1_API_MAPPING.md  # ESPN API docs
│       ├── FASTF1_API_REFERENCE.md # FastF1 library guide
│       ├── FASTF1_API_MAPPING.md   # FastF1 data mapping
│       ├── FRONTEND_SETUP.md       # Frontend setup guide
│       └── GETTING_STARTED.md      # Detailed getting started
│
├── 💾 Cache & Data (generated/ignored)
│   ├── f1_cache/                   # FastF1 session cache
│   ├── .venv/                      # Python virtual environment
│   └── node_modules/               # Node.js dependencies
│
└── 🔧 Configuration
    ├── .gitignore                  # Git exclusions
    ├── .env                        # Environment variables (not in git)
    └── .claude/                    # Claude Code settings
```

## 📖 Documentation Guide

### For New Users
1. **README.md** - Start here for project overview
2. **QUICKSTART.md** - Get running in 5 minutes
3. **docs/GETTING_STARTED.md** - Detailed setup guide

### For Developers
1. **CONTRIBUTING.md** - How to contribute
2. **docs/ARCHITECTURE.md** - System design
3. **docs/DATABASE_SCHEMA.md** - Database structure
4. **docs/API.md** - API reference

### For API Integration
1. **docs/ESPN_F1_API_MAPPING.md** - ESPN API details
2. **docs/FASTF1_API_REFERENCE.md** - FastF1 usage
3. **docs/API_INTEGRATION_STRATEGY.md** - Integration patterns

## 🚀 Quick Commands

### Setup
```bash
# Automated setup
./setup.sh                          # macOS/Linux
.\setup.ps1                         # Windows

# Or with Docker
docker-compose up
```

### Development
```bash
# Backend
uv run python -m src.f1_webapp.api.app

# Frontend
cd frontend && npm run dev

# Database update
uv run python scripts/populate_espn_final.py
```

### Testing
```bash
# Backend tests
uv run pytest

# Frontend tests
cd frontend && npm test

# Type checking
cd frontend && npm run check
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Run backend (production)
uv run uvicorn src.f1_webapp.api.app:app --host 0.0.0.0 --port 8000

# Docker (production)
docker-compose -f docker-compose.yml up -d
```

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `src/f1_webapp/api/app.py` | Main FastAPI application entry point |
| `frontend/src/pages/index.astro` | Home page |
| `scripts/populate_espn_final.py` | Initial database setup |
| `docs/ARCHITECTURE.md` | System design documentation |
| `docker-compose.yml` | Complete deployment configuration |

## 📦 Dependencies

### Backend (Python)
- **FastAPI** - Web framework
- **FastF1** - F1 telemetry data
- **SQLite** - Database
- **Pandas** - Data processing
- **Requests** - HTTP client

### Frontend (JavaScript/TypeScript)
- **Astro** - Static site framework
- **React** - UI library
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization

## 🔄 Typical Workflows

### Adding a New Feature

1. Create feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. Implement in appropriate location:
   - Backend API: `src/f1_webapp/api/routes/`
   - Frontend component: `frontend/src/components/`
   - Database script: `scripts/`

3. Update documentation in `docs/`

4. Test and submit PR

### Updating Database Schema

1. Modify schema in `src/f1_webapp/api/models/`
2. Create migration in `scripts/`
3. Update `docs/DATABASE_SCHEMA.md`
4. Test with `scripts/populate_espn_final.py`

### Adding API Endpoint

1. Add route in `src/f1_webapp/api/routes/`
2. Update `docs/API.md`
3. Test with `curl` or API docs at `/docs`
4. Update frontend to consume endpoint

## 🌍 Environment Variables

Create `.env` files as needed:

**Backend (.env):**
```env
DATABASE_URL=sqlite:///./f1_data.db
FASTF1_CACHE_DIR=./f1_cache
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend (frontend/.env):**
```env
PUBLIC_API_URL=http://localhost:8000
```

## 📊 Data Flow

```
User Request
    ↓
Frontend (Astro + React)
    ↓ HTTP/REST
Backend API (FastAPI)
    ↓
├─→ SQLite Database (cached data)
├─→ ESPN API (historical data)
└─→ FastF1 Library (telemetry data)
```

## 🎯 Project Goals

1. **Accessibility** - Make F1 data easy to access and understand
2. **Performance** - Fast load times and responsive UI
3. **Accuracy** - Historical accuracy for championship points systems
4. **Extensibility** - Easy to add new features and data sources
5. **Documentation** - Well-documented for contributors

## 📝 Notes

- Database file (`f1_data.db`) is ignored by git
- FastF1 cache (`f1_cache/`) is ignored by git
- Environment files (`.env`) are ignored by git
- Built files (`dist/`, `build/`) are ignored by git

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Development setup

## 📧 Support

- 📖 Check documentation in `/docs`
- 🐛 Report issues on GitHub
- 💬 Ask questions in Discussions
- 📧 Contact maintainers

---

Last updated: 2024-12-01
