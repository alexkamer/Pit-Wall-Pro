# Frontend Technology Stack Plan

## Core Framework & Build Tools

### Next.js 15+ (App Router)
**Why:**
- Server-side rendering for better performance
- Built-in API routes (if needed for frontend logic)
- File-based routing
- Image optimization
- TypeScript support out of the box
- Perfect for data-heavy applications like F1 analytics

**Installation:**
```bash
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir
```

### TypeScript
**Why:**
- Type safety for API responses
- Better IDE support and autocomplete
- Catch errors at compile time
- Essential for complex data structures (telemetry, lap times, etc.)

## UI Framework & Styling

### Tailwind CSS
**Why:**
- Utility-first CSS for rapid development
- Small bundle size (only ships classes you use)
- Responsive design made easy
- Consistent design system
- Already integrated with Next.js

### shadcn/ui
**Why:**
- Beautiful, accessible React components
- Copy-paste components (no package dependency bloat)
- Built on Radix UI primitives (excellent accessibility)
- Customizable with Tailwind
- Includes Chart components built on Recharts
- Perfect for dashboards and data-heavy UIs

**Components we'll use:**
- `Card` - For race results, standings cards
- `Table` - For lap times, standings tables
- `Tabs` - For switching between Practice/Qualifying/Race
- `Select` - For year/race selection
- `Dialog` - For detailed views
- `Badge` - For tire compounds, positions
- `Skeleton` - Loading states
- `Chart` components - For all visualizations

**Installation:**
```bash
npx shadcn@latest init
```

## Data Visualization

### Recharts (via shadcn/ui charts)
**Why:**
- React-native charting library
- Composable components
- Easy to customize
- Perfect for F1 data visualization
- Already integrated with shadcn/ui
- 26k+ GitHub stars

**Chart types we'll use:**
- **Line Charts** - Lap time progression, telemetry (speed traces)
- **Area Charts** - Gap to leader over time, tire degradation
- **Bar Charts** - Sector time comparisons, pit stop durations
- **Scatter Charts** - Qualifying pace vs race pace
- **Composed Charts** - Multiple data types (e.g., speed + throttle)

**Alternative considered:** Chart.js - but Recharts is more React-idiomatic

## Data Fetching & State Management

### TanStack Query (React Query) v5
**Why:**
- Perfect for API data fetching
- Automatic caching and background refetching
- Loading and error states built-in
- Optimistic updates
- No need for Redux/Zustand for server state
- Ideal for frequently updating F1 data

**Use cases:**
- Cache race schedule (1 hour TTL)
- Cache standings (5 min TTL during race weekends)
- Real-time lap times during sessions
- Telemetry data

**Installation:**
```bash
npm install @tanstack/react-query
```

### Zustand (Optional, for client state)
**Why:**
- Simple global state management
- No boilerplate like Redux
- TypeScript support
- Small bundle size (1kb)

**Use cases:**
- User preferences (favorite drivers, theme)
- Selected race/session filter
- Chart display options

**Installation:**
```bash
npm install zustand
```

## Date/Time Handling

### date-fns
**Why:**
- Lightweight (we only import what we need)
- Immutable
- TypeScript support
- Perfect for race times, countdowns, timezone conversion

**Use cases:**
- Race countdown timers
- Convert UTC to local time
- Format lap times (mm:ss.SSS)
- Session duration calculations

**Installation:**
```bash
npm install date-fns
```

## Icons

### Lucide React
**Why:**
- Beautiful, consistent icons
- Tree-shakeable
- Already used by shadcn/ui
- TypeScript support
- 1000+ icons

**Icons we'll use:**
- Calendar, Clock - Race schedule
- Trophy, Award - Standings
- Flag, CheckeredFlag - Race status
- Timer, Gauge - Telemetry
- TrendingUp/Down - Performance indicators

**Installation:**
```bash
npm install lucide-react
```

## Utilities

### clsx + tailwind-merge
**Why:**
- Conditional className handling
- Merge Tailwind classes intelligently
- Used by shadcn/ui

**Installation:**
```bash
npm install clsx tailwind-merge
```

### zod
**Why:**
- Runtime type validation
- Validate API responses
- Form validation
- Parse environment variables
- TypeScript inference

**Installation:**
```bash
npm install zod
```

## Performance & Analytics (Optional for later)

### next/image
- Built-in with Next.js
- Automatic image optimization
- Lazy loading
- Team logos, driver photos

### React Virtualization (if needed)
- For very long lap time lists
- Only render visible rows

## Development Tools

### ESLint + Prettier
- Code quality and formatting
- Already configured with Next.js

### TypeScript ESLint
- TypeScript-specific linting rules

## Complete Package List

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^3.5.1",
    "date-fns": "^3.0.0",
    "lucide-react": "latest",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "zod": "^3.22.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.0",
    "eslint": "^8",
    "eslint-config-next": "^15.0.0",
    "prettier": "^3.0.0"
  }
}
```

## shadcn/ui Components to Install

```bash
# Layout & Navigation
npx shadcn@latest add card
npx shadcn@latest add tabs
npx shadcn@latest add separator

# Data Display
npx shadcn@latest add table
npx shadcn@latest add badge
npx shadcn@latest add avatar

# Forms & Inputs
npx shadcn@latest add select
npx shadcn@latest add button
npx shadcn@latest add input

# Feedback
npx shadcn@latest add skeleton
npx shadcn@latest add alert
npx shadcn@latest add toast

# Overlays
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu

# Charts
npx shadcn@latest add chart
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Homepage (upcoming races)
│   ├── schedule/
│   │   └── page.tsx        # Full race calendar
│   ├── standings/
│   │   └── page.tsx        # Driver & constructor standings
│   ├── race/
│   │   └── [id]/
│   │       └── page.tsx    # Race details & results
│   └── telemetry/
│       └── page.tsx        # Telemetry visualization
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── charts/             # Custom chart components
│   │   ├── lap-time-chart.tsx
│   │   ├── telemetry-chart.tsx
│   │   └── standings-chart.tsx
│   ├── race/
│   │   ├── race-card.tsx
│   │   ├── race-countdown.tsx
│   │   └── session-selector.tsx
│   └── layout/
│       ├── nav.tsx
│       └── footer.tsx
├── lib/
│   ├── api/                # API client functions
│   │   ├── schedule.ts
│   │   ├── standings.ts
│   │   └── session.ts
│   ├── utils.ts            # Utility functions
│   ├── constants.ts        # F1 constants (driver codes, etc.)
│   └── types.ts            # TypeScript types
├── hooks/
│   ├── use-schedule.ts     # React Query hooks
│   ├── use-standings.ts
│   └── use-session.ts
└── styles/
    └── globals.css         # Global styles
```

## Why NOT these libraries?

### Material-UI (MUI)
- Heavier bundle size
- More opinionated styling
- Harder to customize for F1 branding

### Chart.js
- Less React-idiomatic
- Recharts has better composition model

### Redux Toolkit
- Overkill for our use case
- React Query handles server state better
- Zustand is simpler for client state

### Axios
- Native fetch + React Query is sufficient
- One less dependency

### Moment.js
- Deprecated and large
- date-fns is modern and tree-shakeable

## Performance Considerations

1. **Code Splitting**: Next.js automatically splits code by route
2. **Lazy Loading**: Use `next/dynamic` for heavy chart components
3. **React Query Caching**: Reduce API calls
4. **Memoization**: Use React.memo for expensive chart renders
5. **Virtual Scrolling**: If lap lists exceed 1000+ rows
6. **Image Optimization**: Use next/image for team logos

## Accessibility

- shadcn/ui components are built on Radix UI (WCAG compliant)
- Keyboard navigation support
- Screen reader support
- Focus management
- ARIA labels on charts

## Mobile Responsiveness

- Tailwind's responsive breakpoints
- Mobile-first approach
- Touch-friendly controls
- Simplified charts for mobile
- Collapsible tables

## Theme Support

- Dark/Light mode using next-themes
- F1-themed color palette
- Team colors for charts
- High contrast mode support

## Next Steps

1. ✅ Plan complete
2. Create Next.js project
3. Install shadcn/ui and configure theme
4. Set up React Query provider
5. Create API client functions
6. Build first page (race schedule)
7. Add chart components
8. Implement remaining pages

This stack gives us:
- 🎨 Beautiful, modern UI
- 📊 Powerful data visualization
- ⚡ Excellent performance
- 🔧 Easy to maintain and extend
- 📱 Mobile responsive
- ♿ Accessible by default
