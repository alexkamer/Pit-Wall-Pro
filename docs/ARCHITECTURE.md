# F1 WebApp Architecture

This document provides an overview of the F1 WebApp system architecture, including data flow, component interactions, and design decisions.

## System Overview

The F1 WebApp is a full-stack application that combines multiple data sources to provide comprehensive Formula 1 data analysis and visualization.

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                    (Astro + React + Tailwind)               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Standings   │  │   Races      │  │  Telemetry   │     │
│  │    Pages     │  │   Pages      │  │    Charts    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                       Backend Layer                          │
│                     (FastAPI + Python)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Router                          │  │
│  │  /espn/*  /fastf1/*  /db/*  /health                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ESPN Client │  │FastF1 Client │  │ DB Service   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌────────────────┐  ┌────────────────┐  ┌──────────────────┐
│  ESPN F1 API   │  │ FastF1 Library │  │  SQLite Database │
│  (External)    │  │  (External)    │  │   (Local Cache)  │
└────────────────┘  └────────────────┘  └──────────────────┘
```

## Component Details

### Frontend (Astro + React)

**Technology Stack:**
- Astro 5.x - Static site generation and routing
- React 19 - Interactive UI components
- Tailwind CSS v4 - Styling framework
- Recharts - Data visualization
- TypeScript - Type safety

**Key Features:**
- Server-side rendering (SSR) and static generation
- Component-based architecture with React islands
- Responsive design for mobile and desktop
- Real-time data fetching from backend API

**Directory Structure:**
```
frontend/
├── src/
│   ├── pages/              # Astro pages (routes)
│   │   ├── index.astro     # Home page
│   │   └── standings/      # Standings pages
│   ├── components/         # React components
│   │   ├── StandingsTable.tsx
│   │   ├── RaceResults.tsx
│   │   └── TelemetryChart.tsx
│   ├── layouts/            # Page layouts
│   └── styles/             # Global styles
└── public/                 # Static assets
```

### Backend (FastAPI)

**Technology Stack:**
- FastAPI 0.122+ - Modern async web framework
- Python 3.12+ - Programming language
- Uvicorn - ASGI server
- Pydantic - Data validation
- Pandas - Data manipulation

**API Structure:**
```
src/f1_webapp/api/
├── app.py              # Main FastAPI application
├── routes/             # API endpoint modules
│   ├── espn.py        # ESPN data endpoints
│   ├── fastf1.py      # FastF1 data endpoints
│   └── database.py    # Database query endpoints
├── models/             # Database models
│   ├── race.py
│   ├── driver.py
│   └── constructor.py
└── services/           # Business logic
    ├── espn_service.py
    ├── fastf1_service.py
    └── db_service.py
```

**API Design Principles:**
- RESTful endpoint design
- Async/await for concurrent requests
- Automatic API documentation with OpenAPI
- CORS enabled for frontend integration
- Error handling with proper HTTP status codes

### Data Layer

#### 1. ESPN F1 API Client

**Purpose:** Fetch historical and current championship data

**Key Features:**
- Championship standings (1950-present)
- Driver and constructor profiles
- Race schedules and results
- Real-time season updates

**Implementation:**
- HTTP client using `requests` library
- Response caching to minimize API calls
- Data normalization for consistent format
- Rate limiting to respect API usage limits

#### 2. FastF1 Library Client

**Purpose:** Detailed telemetry and timing data

**Key Features:**
- Telemetry data (2018-present)
- Lap-by-lap timing information
- GPS tracking and position data
- Weather conditions
- Race control messages

**Implementation:**
- Wrapper around FastF1 library
- Local file caching in `f1_cache/` directory
- Pandas DataFrame processing
- Session data loading and parsing

#### 3. SQLite Database

**Purpose:** Cache frequently accessed data and improve performance

**Schema Overview:**
```sql
-- Core tables
Seasons (year, champion_driver_id, champion_constructor_id)
Races (id, year, round, name, date, circuit_name, country)
Drivers (id, name, nationality, team_id)
Constructors (id, name, nationality, logo_url)

-- Results and standings
RaceResults (race_id, driver_id, position, points, status)
DriverStandings (race_id, driver_id, position, points)
ConstructorStandings (race_id, constructor_id, position, points)
```

See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for complete schema details.

## Data Flow

### 1. Historical Data Request Flow

```
User → Frontend → Backend API → Database Cache → Response
                              ↓ (if not cached)
                          ESPN API → Database → Response
```

**Example:** Getting 2023 championship standings
1. Frontend requests: `GET /espn/standings/2023`
2. Backend checks SQLite cache
3. If cached: Return from database
4. If not cached: Fetch from ESPN API, save to database, return response

### 2. Telemetry Data Request Flow

```
User → Frontend → Backend API → FastF1 Client → FastF1 Library
                                              ↓
                                      Local Cache (f1_cache/)
                                              ↓
                                        F1 Data Servers
```

**Example:** Getting Monaco 2024 qualifying telemetry
1. Frontend requests: `GET /fastf1/telemetry/2024/Monaco/Q/VER`
2. Backend calls FastF1 client
3. FastF1 checks local cache
4. If cached: Load from `f1_cache/`
5. If not cached: Download from F1 servers, cache locally
6. Process and return telemetry data

### 3. Live Data Update Flow

```
Scheduled Task → ESPN API → Database Update → WebSocket (future)
                                            ↓
                                        Frontend Auto-Refresh
```

## Performance Considerations

### Caching Strategy

**Three-tier caching:**

1. **Browser Cache** (Frontend)
   - Static assets cached by browser
   - API responses cached with appropriate headers

2. **Application Cache** (Backend)
   - SQLite database for frequently accessed data
   - In-memory caching for hot data paths

3. **FastF1 Cache** (File System)
   - Session data cached locally
   - Prevents repeated downloads from F1 servers

### Optimization Techniques

1. **Database Indexing:**
   - Indexed columns: year, round, driver_id, race_id
   - Compound indexes for common query patterns

2. **Lazy Loading:**
   - Telemetry data loaded on-demand
   - Large datasets paginated

3. **Async Operations:**
   - FastAPI async endpoints for I/O-bound operations
   - Concurrent data fetching where possible

4. **Data Compression:**
   - Gzip compression for API responses
   - Minified frontend assets

## Scalability

### Current Architecture (Single Server)

**Suitable for:**
- Personal projects
- Small to medium user base (< 1000 concurrent users)
- Development and testing

**Limitations:**
- Single point of failure
- Limited horizontal scaling
- Database contention under high load

### Future Scaling Options

**Horizontal Scaling:**
```
                    Load Balancer
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
    API Server 1   API Server 2   API Server 3
          ↓              ↓              ↓
          └──────────────┼──────────────┘
                         ↓
              Shared Database (PostgreSQL)
                         ↓
                    Redis Cache
```

**Improvements:**
- Multiple API server instances behind load balancer
- PostgreSQL instead of SQLite for concurrent writes
- Redis for distributed caching
- CDN for frontend static assets

## Security Considerations

### Current Implementation

1. **CORS Configuration:**
   - Configured to allow frontend origin
   - Restricted methods and headers

2. **Input Validation:**
   - Pydantic models for request validation
   - Path parameter sanitization

3. **Rate Limiting:**
   - Respect ESPN API rate limits
   - Local rate limiting for API endpoints

### Production Recommendations

1. **Authentication & Authorization:**
   - API key or JWT-based authentication
   - User roles and permissions

2. **HTTPS:**
   - SSL/TLS certificates
   - Secure cookie handling

3. **Input Sanitization:**
   - SQL injection prevention (using ORMs)
   - XSS protection on frontend

4. **API Security:**
   - Rate limiting per user/IP
   - DDoS protection
   - API versioning

## Deployment Architecture

### Development Environment

```
localhost:4321 (Frontend Dev Server)
      ↓
localhost:8000 (Backend API Server)
      ↓
./f1_data.db (Local SQLite)
./f1_cache/ (FastF1 Cache)
```

### Production Environment (Recommended)

```
CDN (Static Assets)
      ↓
Frontend (Vercel/Netlify)
      ↓
API Gateway
      ↓
Backend (AWS/GCP/Azure)
      ↓
Database (PostgreSQL)
      ↓
Object Storage (S3)
```

**Deployment Options:**

1. **Frontend:**
   - Vercel (recommended for Astro)
   - Netlify
   - AWS S3 + CloudFront

2. **Backend:**
   - Docker container on AWS ECS/Fargate
   - Google Cloud Run
   - DigitalOcean App Platform
   - Railway

3. **Database:**
   - Managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - PlanetScale (MySQL)
   - Supabase (PostgreSQL + APIs)

## Technology Choices

### Why FastAPI?

- Modern async support for concurrent operations
- Automatic API documentation
- Excellent performance (comparable to Node.js)
- Type hints and validation with Pydantic
- Large ecosystem and community

### Why Astro?

- Optimal performance with partial hydration
- Framework-agnostic (can use React, Vue, etc.)
- Built-in static site generation
- Excellent developer experience
- SEO-friendly

### Why SQLite?

- Zero configuration
- Serverless (no separate DB process)
- Excellent for read-heavy workloads
- Perfect for development and small deployments
- Easy to upgrade to PostgreSQL later

### Why FastF1?

- Official F1 telemetry data access
- Comprehensive API covering all data types
- Active community and maintenance
- Built-in caching and performance optimization
- Pandas integration for data analysis

## Future Enhancements

### Planned Features

1. **Real-time Updates:**
   - WebSocket connections for live timing
   - Server-Sent Events for race updates

2. **Advanced Analytics:**
   - Driver comparison tools
   - Predictive race analysis
   - Historical trend analysis

3. **User Features:**
   - User accounts and preferences
   - Favorite drivers and teams
   - Custom dashboards

4. **Performance:**
   - Redis caching layer
   - GraphQL API alternative
   - Database read replicas

5. **Mobile:**
   - Progressive Web App (PWA)
   - Native mobile apps (React Native)

### Technical Debt

- Add comprehensive test coverage
- Implement CI/CD pipeline
- Add monitoring and logging (Sentry, DataDog)
- Database migration system (Alembic)
- API versioning strategy

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Astro Documentation](https://docs.astro.build/)
- [FastF1 Documentation](https://docs.fastf1.dev/)
- [ESPN F1 API](https://www.espn.com/apis/devcenter/docs/)
