# Claude Code Context

## Project Overview
F1 WebApp with schedule, race details, standings, and data visualization.

## Important Notes

### Chrome DevTools Screenshots
When using Chrome DevTools `take_screenshot`, be careful about image dimensions:
- Maximum allowed size: 8000 pixels per dimension
- Use `fullPage: false` for viewport-only screenshots to avoid size issues
- For full page captures, consider taking multiple viewport screenshots or using smaller viewport sizes

## Key Files
- Frontend:
  - `/frontend/app/schedule/page.tsx` - Schedule page with race cards
  - `/frontend/app/race/[year]/[round]/page.tsx` - Race details page
  - `/frontend/components/EnhancedRaceResults.tsx` - Race results with tire strategy
  - `/frontend/components/TrackMap.tsx` - Track visualization

- Backend:
  - `/backend/app/api/schedule.py` - Schedule endpoints
  - `/backend/app/api/session.py` - Session data endpoints
  - `/backend/app/services/fastf1_service.py` - FastF1 integration
