#!/bin/bash
set -e  # Exit on any error

echo "🏎️  F1 WebApp - Frontend Setup Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Step 1: Cleaning up any existing frontend directory...${NC}"
if [ -d "frontend" ]; then
    rm -rf frontend
    echo "✓ Removed existing frontend directory"
fi

echo ""
echo -e "${BLUE}Step 2: Creating Next.js project...${NC}"
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*" \
  --turbopack \
  --yes

echo ""
echo -e "${BLUE}Step 3: Installing additional dependencies...${NC}"
cd frontend
npm install @tanstack/react-query recharts date-fns lucide-react clsx tailwind-merge zod zustand

echo ""
echo -e "${BLUE}Step 4: Creating components.json for shadcn/ui...${NC}"
cat > components.json <<'EOF'
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
EOF
echo "✓ Created components.json"

echo ""
echo -e "${BLUE}Step 5: Installing shadcn/ui components...${NC}"
npx shadcn@latest add button card tabs table badge select skeleton alert dialog dropdown-menu separator chart --yes --overwrite

echo ""
echo -e "${BLUE}Step 6: Creating project structure...${NC}"

# Create directories
mkdir -p lib/api
mkdir -p hooks
mkdir -p components/charts
mkdir -p components/race
mkdir -p components/layout

echo "✓ Created directory structure"

echo ""
echo -e "${BLUE}Step 7: Creating utility files...${NC}"

# Create lib/utils.ts (if not exists from shadcn)
if [ ! -f "lib/utils.ts" ]; then
cat > lib/utils.ts <<'EOF'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF
fi

# Create lib/constants.ts
cat > lib/constants.ts <<'EOF'
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const DRIVER_CODES = [
  'VER', 'HAM', 'LEC', 'NOR', 'PER', 'SAI', 'RUS', 'ALO',
  'PIA', 'STR', 'GAS', 'OCO', 'HUL', 'TSU', 'MAG', 'RIC',
  'ALB', 'SAR', 'BOT', 'ZHO'
] as const;

export const SESSION_TYPES = {
  FP1: 'Practice 1',
  FP2: 'Practice 2',
  FP3: 'Practice 3',
  Q: 'Qualifying',
  S: 'Sprint',
  R: 'Race'
} as const;

export const TIRE_COMPOUNDS = {
  SOFT: { name: 'Soft', color: '#FF0000' },
  MEDIUM: { name: 'Medium', color: '#FDB641' },
  HARD: { name: 'Hard', color: '#F0F0F0' },
  INTERMEDIATE: { name: 'Intermediate', color: '#00FF00' },
  WET: { name: 'Wet', color: '#0000FF' }
} as const;
EOF

# Create lib/types.ts
cat > lib/types.ts <<'EOF'
export interface RaceEvent {
  RoundNumber: number;
  Country: string;
  Location: string;
  OfficialEventName: string;
  EventDate: string;
  EventName: string;
  EventFormat: string;
  Session1?: string;
  Session1Date?: string;
  Session2?: string;
  Session2Date?: string;
  Session3?: string;
  Session3Date?: string;
  Session4?: string;
  Session4Date?: string;
  Session5?: string;
  Session5Date?: string;
}

export interface DriverStanding {
  position: number;
  driver: string;
  team: string;
  points: number;
  wins: number;
}

export interface LapTime {
  Driver: string;
  LapNumber: number;
  LapTime: number;
  Sector1Time: number;
  Sector2Time: number;
  Sector3Time: number;
  Compound: string;
  TyreLife: number;
}

export interface TelemetryData {
  Distance: number;
  Speed: number;
  RPM: number;
  nGear: number;
  Throttle: number;
  Brake: number;
  DRS: number;
}
EOF

echo "✓ Created utility files"

echo ""
echo -e "${BLUE}Step 8: Creating environment file...${NC}"
cat > .env.local <<'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
echo "✓ Created .env.local"

echo ""
echo -e "${GREEN}✅ Frontend setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. cd frontend"
echo "2. npm run dev"
echo ""
echo "The frontend will be available at http://localhost:3000"
echo "The backend API is running at http://localhost:8000"
echo ""
echo "Note: Make sure your backend server is still running!"
