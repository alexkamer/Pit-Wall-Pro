# F1 Analytics Frontend - Astro

## 🚀 Quick Start

Your F1 webapp now has a modern Astro frontend!

### Running the Application

**Backend (FastAPI):**
```bash
uv run uvicorn src.f1_webapp.api.app:app --host 0.0.0.0 --port 8000
```
- API runs on: http://localhost:8000
- API docs: http://localhost:8000/docs

**Frontend (Astro):**
```bash
cd frontend
npm run dev
```
- Frontend runs on: http://localhost:4321

## 📁 Project Structure

```
f1_webapp/
├── src/f1_webapp/           # Python backend
│   ├── api/                 # FastAPI app
│   ├── espn/                # ESPN API client
│   └── fastf1/              # FastF1 client
│
└── frontend/                # Astro frontend
    ├── src/
    │   ├── layouts/
    │   │   └── Layout.astro      # Main layout with nav
    │   ├── pages/
    │   │   ├── index.astro       # Homepage
    │   │   ├── standings.astro   # Standings page
    │   │   └── schedule.astro    # Schedule page
    │   └── lib/
    │       └── api.ts            # API client
    ├── public/
    └── package.json
```

## 🎨 Tech Stack

### Frontend
- **Astro 5** - Fast, content-focused framework
- **React 19** - For interactive components (charts)
- **Tailwind CSS 4** - Utility-first styling
- **TypeScript** - Type safety
- **Recharts** - Data visualization (ready to use)

### Backend
- **FastAPI** - Python web framework
- **ESPN F1 API** - Standings, drivers, events
- **FastF1** - Telemetry, session data, lap times

## 📄 Current Pages

### 1. Homepage (`/`)
- Top 10 driver standings
- Season calendar summary
- Quick navigation cards

### 2. Standings (`/standings`)
- Full driver championship table
- Constructor championship table
- Real-time points and wins

### 3. Schedule (`/schedule`)
- Complete 2024 race calendar
- Race locations and dates
- Event formats

## 🔧 Configuration

**Environment Variables** (`frontend/.env`):
```
PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Next Steps

### Easy Additions:
1. **Race Detail Pages** - Individual race results
2. **Driver Pages** - Detailed driver stats
3. **Telemetry Charts** - Interactive speed/throttle visualizations
4. **Live Timing** - Real-time session data

### How to Add Features:

**1. Add a new page:**
```astro
<!-- frontend/src/pages/drivers.astro -->
---
import Layout from '../layouts/Layout.astro';
---

<Layout title="Drivers">
  <h1>F1 Drivers 2024</h1>
</Layout>
```

**2. Add API functions:**
```typescript
// frontend/src/lib/api.ts
export async function getDriverDetails(driverId: string) {
  return fetchAPI(`/espn/drivers/${driverId}`);
}
```

**3. Create React components for interactivity:**
```tsx
// frontend/src/components/TelemetryChart.tsx
export function TelemetryChart({ data }) {
  // Use Recharts for visualization
}
```

## 🚀 Building for Production

```bash
cd frontend
npm run build
npm run preview
```

This creates a static build in `frontend/dist/` that you can deploy anywhere!

## 📊 API Endpoints Available

See `API_ENDPOINT_EXAMPLES.md` for full API documentation.

**ESPN:**
- `/espn/standings/{year}?type=driver|constructor`
- `/espn/drivers/{driver_id}`
- `/espn/events?season={year}`

**FastF1:**
- `/fastf1/schedule/{year}`
- `/fastf1/session/{year}/{gp}/{session_type}`
- `/fastf1/fastest-lap/{year}/{gp}/{session_type}`
- `/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}`
- `/fastf1/compare/{year}/{gp}/{session_type}?driver1=X&driver2=Y`

## 🎨 Styling

Tailwind CSS is configured and ready to use. Example classes:
- `bg-gray-900` - Dark background
- `text-red-500` - F1 red accent
- `border-gray-800` - Subtle borders
- `hover:bg-gray-800` - Interactive states

## ✅ What's Working

- ✅ Backend API fully functional
- ✅ Frontend dev server running
- ✅ Homepage with live data
- ✅ Standings page (drivers + constructors)
- ✅ Schedule page (all races)
- ✅ Responsive design
- ✅ Fast page loads with Astro
- ✅ Type-safe API client
- ✅ Modern dark theme

## 🐛 Known Issues

None! Everything is working great.

## 📚 Resources

- Astro docs: https://docs.astro.build
- Tailwind docs: https://tailwindcss.com/docs
- Recharts docs: https://recharts.org
- FastF1 docs: https://docs.fastf1.dev

---

Happy coding! 🏎️💨
