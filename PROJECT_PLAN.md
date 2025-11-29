# Formula 1 Web Application - Project Plan

## Overview
A comprehensive F1 web application that combines data from ESPN's F1 API and FastF1's telemetry API to provide real-time race information, historical data, and detailed telemetry analysis.

## API Analysis

### ESPN F1 API
**Base URL**: `http://sports.core.api.espn.com/v2/sports/racing/leagues/f1`

**Key Endpoints**:
- `/events` - Race events and schedule
- `/seasons/{year}/types/2/standings/0` - Driver standings
- `/seasons/{year}/types/2/standings/1` - Constructor/team standings
- `/calendar` - Calendar information
- `/athletes` - Driver information
- `/events/{eventId}` - Detailed race event data

**Data Available**:
- Live race results and positions
- Driver and constructor standings
- Race schedule and calendar
- Event details (times, locations, circuits)
- Historical season data

### FastF1 API (Python Library)
**Documentation**: https://docs.fastf1.dev/

**Key Features**:
- Session data (Practice, Qualifying, Sprint, Race)
- Lap timing data with sector times
- Car telemetry (speed, RPM, gear, throttle, brake)
- Driver position and trajectory data
- Weather data
- Tire compound information
- Race control messages and flags
- Circuit information and track maps
- Integration with Ergast API for historical data

**Data Available**:
- Telemetry data from 2018 onwards
- Detailed lap-by-lap analysis
- Speed traces and comparisons
- Tire strategy analysis
- Historical F1 data back to 1950 (via Ergast)

## Proposed Architecture

### Backend (Python with FastAPI)
- **Framework**: FastAPI for high-performance REST API
- **Data Layer**:
  - FastF1 Python library for telemetry and session data
  - HTTP client for ESPN API integration
  - Redis/SQLite for caching to improve performance
- **API Endpoints**:
  - `/api/schedule` - Race calendar
  - `/api/standings/drivers` - Driver championship
  - `/api/standings/constructors` - Team championship
  - `/api/race/{event_id}` - Live/past race results
  - `/api/session/{session_id}/laps` - Lap times and data
  - `/api/session/{session_id}/telemetry` - Car telemetry
  - `/api/drivers/{driver}/comparison` - Driver comparisons
  - `/api/circuit/{circuit_id}` - Circuit information

### Frontend (React/Next.js)
- **Framework**: Next.js with React for server-side rendering
- **Styling**: Tailwind CSS for modern, responsive design
- **Charts**: Recharts or Chart.js for telemetry visualization
- **Maps**: Canvas or SVG for circuit maps and position tracking

## Core Features

### Phase 1: Essential Features
1. **Race Calendar & Schedule**
   - Display upcoming races
   - Show race weekend schedule (Practice, Qualifying, Race)
   - Countdown to next session
   - Timezone conversion

2. **Live Race Results**
   - Real-time race positions
   - Gap to leader and car ahead
   - Fastest lap information
   - Race status (green flag, safety car, red flag)

3. **Championship Standings**
   - Driver standings with points
   - Constructor standings
   - Points progression charts
   - Historical comparison

4. **Race Results Archive**
   - Past race results
   - Podium finishes
   - DNF information
   - Race statistics

### Phase 2: Advanced Analytics
5. **Lap Time Analysis**
   - Lap time charts for all drivers
   - Sector time breakdowns
   - Tire strategy visualization
   - Pit stop timing and duration

6. **Telemetry Visualization**
   - Speed traces on circuit map
   - Throttle/brake application
   - Gear changes
   - Driver comparison overlays

7. **Driver Comparisons**
   - Head-to-head lap comparisons
   - Qualifying vs race pace
   - Sector-by-sector analysis
   - Historical performance

8. **Track Information**
   - Circuit layouts and maps
   - Corner names and numbers
   - Track records
   - Historical data for each circuit

### Phase 3: Enhanced Features
9. **Live Timing Dashboard**
   - Real-time timing updates during sessions
   - Mini sector times
   - Speed trap data
   - Race control messages

10. **Historical Analysis**
    - Season comparison tools
    - Driver career statistics
    - Team performance history
    - Record tracking

11. **Weather Integration**
    - Session weather conditions
    - Impact on lap times
    - Historical weather patterns

12. **User Features**
    - Favorite drivers/teams
    - Custom notifications
    - Personalized dashboard
    - Data export capabilities

## Technical Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Libraries**:
  - fastf1 (telemetry and session data)
  - httpx (ESPN API calls)
  - pandas (data processing)
  - redis-py (caching)
- **Database**: PostgreSQL (for user data) + Redis (caching)

### Frontend
- **Framework**: Next.js 14+ (React 18+)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts or Chart.js
- **State Management**: React Query for server state
- **HTTP Client**: Axios or fetch

### Deployment
- **Backend**: Docker container on Railway/Render/AWS
- **Frontend**: Vercel or Netlify
- **Database**: Managed PostgreSQL (Supabase/Railway)
- **Cache**: Redis Cloud or Upstash

## Data Flow
1. Frontend requests data from Backend API
2. Backend checks cache (Redis) for recent data
3. If not cached:
   - Fetch from ESPN API for live data/standings
   - Use FastF1 for detailed telemetry/session data
   - Process and combine data as needed
4. Cache response with appropriate TTL
5. Return formatted data to frontend
6. Frontend visualizes data with charts and tables

## Development Roadmap

### Week 1-2: Project Setup & Phase 1
- Set up project structure (backend + frontend)
- Configure FastF1 and ESPN API integration
- Implement race calendar and schedule
- Build basic standings page
- Create responsive layout

### Week 3-4: Phase 1 Completion
- Live race results display
- Race results archive
- Basic styling and responsive design
- API documentation

### Week 5-6: Phase 2 - Analytics
- Lap time analysis charts
- Telemetry visualization
- Driver comparison tools
- Circuit information pages

### Week 7-8: Phase 3 & Polish
- Live timing integration
- Historical analysis tools
- User features and preferences
- Performance optimization
- Testing and bug fixes

## API Usage Considerations
- **FastF1**: Data is cached locally by the library, first load may be slow
- **ESPN API**: No authentication required, but implement rate limiting
- **Caching Strategy**: Cache ESPN data for 5-60 seconds during live events, longer for historical data
- **Error Handling**: Graceful fallbacks when APIs are unavailable

## Next Steps
1. Initialize project structure (backend and frontend)
2. Set up FastF1 with caching
3. Test ESPN API endpoints
4. Create basic API endpoints in FastAPI
5. Build initial React components for schedule display
