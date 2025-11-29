from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings
from .api import schedule, standings, session, drivers
from .db.database import init_db
import fastf1

settings = get_settings()

# Configure FastF1 cache
if settings.fastf1_cache_enabled:
    fastf1.Cache.enable_cache(settings.fastf1_cache_dir)

# Initialize SQLite database
init_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Formula 1 Web Application API with FastF1 and ESPN integration"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schedule.router, prefix="/api", tags=["schedule"])
app.include_router(standings.router, prefix="/api", tags=["standings"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(drivers.router, prefix="/api", tags=["drivers"])


@app.get("/")
async def root():
    return {
        "message": "F1 WebApp API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "fastf1_cache_enabled": settings.fastf1_cache_enabled
    }
