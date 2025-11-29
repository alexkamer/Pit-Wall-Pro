# Getting Started with F1 WebApp

## Quick Start

The backend API is now running and fully functional! Here's what you can do right now:

### 1. Explore the API Documentation

Open your browser and visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

You can try out any endpoint directly from the browser!

### 2. Try Some Example Requests

#### Get the 2025 Race Calendar
```bash
curl "http://localhost:8000/api/schedule?year=2025" | python3 -m json.tool
```

#### Get Current Driver Standings
```bash
curl "http://localhost:8000/api/standings/drivers" | python3 -m json.tool
```

#### Get Constructor Standings
```bash
curl "http://localhost:8000/api/standings/constructors" | python3 -m json.tool
```

#### Get 2024 Abu Dhabi Race Results
```bash
curl "http://localhost:8000/api/session/2024/Abu%20Dhabi/R/results" | python3 -m json.tool
```

#### Get Max Verstappen's Lap Times
```bash
curl "http://localhost:8000/api/session/2024/Abu%20Dhabi/R/laps?driver=VER" | python3 -m json.tool
```

#### Get Telemetry for a Specific Lap
```bash
curl "http://localhost:8000/api/session/2024/Abu%20Dhabi/Q/telemetry?driver=VER&lap=1" | python3 -m json.tool
```

### 3. Understanding the Data

#### Session Types
- `FP1`, `FP2`, `FP3` - Free Practice sessions
- `Q` - Qualifying
- `S` - Sprint race
- `R` - Main race

#### Driver Abbreviations (examples)
- `VER` - Max Verstappen
- `HAM` - Lewis Hamilton
- `NOR` - Lando Norris
- `LEC` - Charles Leclerc
- `PER` - Sergio Perez
- `SAI` - Carlos Sainz

#### Race Names
You can use:
- Full race names: "Monaco", "Bahrain", "Abu Dhabi", "Las Vegas"
- Round numbers: 1, 2, 3, etc.

### 4. What's Available

#### ESPN API Data
- ✅ Race calendar and schedule
- ✅ Live race results
- ✅ Driver championship standings
- ✅ Constructor championship standings
- ✅ Event details

#### FastF1 Data
- ✅ Session results (finishing positions)
- ✅ Lap times with sector breakdowns
- ✅ Tire compound information
- ✅ Fastest lap information
- ✅ Full telemetry data (speed, RPM, gear, throttle, brake, DRS)
- ✅ Historical data from 2018+

### 5. Next Steps

Now that the backend is working, you can:

1. **Build a Frontend**: Create a React/Next.js frontend to visualize this data
2. **Add More Endpoints**: Extend the API with additional features from the project plan
3. **Implement Caching**: Add Redis caching for better performance
4. **Add Live Timing**: Implement real-time session updates
5. **Create Visualizations**: Build charts for lap times, telemetry, and standings

### 6. Testing Tips

- First time loading FastF1 data takes 30-60 seconds (downloading + caching)
- Subsequent requests are much faster (uses local cache)
- Try different races: 2024 season has complete data
- Experiment with different drivers and session types

### 7. Troubleshooting

#### Server not starting?
```bash
# Kill any existing server
pkill -f uvicorn

# Restart
uv run uvicorn backend.app.main:app --reload --port 8000
```

#### Cache issues?
```bash
# Clear the cache
rm -rf cache/fastf1/*
```

#### Want to see server logs?
Check the terminal where you ran the uvicorn command

## What We Built Today

✅ **Complete FastAPI backend** with proper structure
✅ **ESPN API integration** for live data
✅ **FastF1 integration** for telemetry and historical data
✅ **8 working API endpoints** covering schedule, standings, and session data
✅ **Proper configuration** with environment variables
✅ **CORS enabled** for frontend development
✅ **Local caching** for better performance
✅ **Full API documentation** with Swagger UI

## Ready for Phase 2!

Check out `PROJECT_PLAN.md` for the next features to implement:
- Frontend with React/Next.js
- Telemetry visualization with charts
- Driver comparison tools
- Live timing dashboard
- Historical analysis features
