'use client';

import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Trophy, Zap, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';

interface RaceResult {
  Position: number;
  GridPosition?: number;
  DriverNumber: string;
  Abbreviation: string;
  FullName?: string;
  Driver?: string;
  TeamName: string;
  Team?: string;
  Time?: string;
  Status?: string;
  Points: number;
  HeadshotUrl?: string;
  FastestLap?: boolean;
}

interface LapData {
  Driver: string;
  Compound?: string;
  FastestLap?: boolean;
}

interface EnhancedRaceResultsProps {
  results: RaceResult[];
  lapData?: { laps: LapData[] };
}

// Team logo URLs
const getTeamLogo = (teamName: string): string => {
  const teamMap: Record<string, string> = {
    'Red Bull Racing': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/red-bull-racing-logo.png',
    'Ferrari': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/ferrari-logo.png',
    'Mercedes': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/mercedes-logo.png',
    'McLaren': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/mclaren-logo.png',
    'Aston Martin': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/aston-martin-logo.png',
    'Alpine': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/alpine-logo.png',
    'Williams': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/williams-logo.png',
    'RB': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/rb-logo.png',
    'Kick Sauber': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/kick-sauber-logo.png',
    'Haas F1 Team': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/haas-f1-team-logo.png',
  };
  return teamMap[teamName] || '';
};

const getDriverPhoto = (result: RaceResult): string => {
  if (result.HeadshotUrl) {
    return result.HeadshotUrl;
  }
  return `https://ui-avatars.com/api/?name=${result.Abbreviation}&background=random&size=128`;
};

// Tire compound colors
const TIRE_COLORS: Record<string, string> = {
  SOFT: '#FF0000',
  MEDIUM: '#FFD700',
  HARD: '#FFFFFF',
  INTERMEDIATE: '#00FF00',
  WET: '#0000FF',
};

const TireIcon = ({ compound, size = 24 }: { compound: string; size?: number }) => {
  const color = TIRE_COLORS[compound] || '#888888';
  const textColor = compound === 'HARD' ? '#000000' : '#FFFFFF';
  const label = compound.charAt(0);

  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill={color} stroke="currentColor" strokeWidth="2" />
      <text
        x="12"
        y="12"
        textAnchor="middle"
        dominantBaseline="central"
        fill={textColor}
        fontSize="12"
        fontWeight="bold"
      >
        {label}
      </text>
    </svg>
  );
};

const formatTime = (time: string | undefined, position: number): string => {
  if (!time) return '-';

  // Convert to string if it's not already
  const timeStr = String(time);

  // For winner, format as H:MM:SS.mmm if it's in seconds format
  if (position === 1) {
    // Check if time is already formatted (contains colons)
    if (timeStr.includes(':')) {
      return timeStr;
    }

    // Try to parse as seconds and format
    const totalSeconds = parseFloat(timeStr);
    if (!isNaN(totalSeconds)) {
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = Math.floor(totalSeconds % 60);
      const milliseconds = Math.floor((totalSeconds % 1) * 1000);

      return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
    }

    return timeStr;
  }

  return `+${timeStr}`;
};

const getTireStrategy = (driverAbbr: string, lapData?: { laps: LapData[] }): string[] => {
  if (!lapData?.laps) return [];

  const driverLaps = lapData.laps.filter(lap => lap.Driver === driverAbbr);
  const compounds: string[] = [];
  let lastCompound = '';
  let isFirstCompound = true;

  driverLaps.forEach(lap => {
    if (lap.Compound && lap.Compound !== lastCompound) {
      // For the first compound change, only add it if we're past lap 1
      // (lap 0 or 1 is typically formation lap data)
      if (isFirstCompound) {
        compounds.push(lap.Compound);
        isFirstCompound = false;
      } else {
        // Subsequent compound changes are actual pit stops
        compounds.push(lap.Compound);
      }
      lastCompound = lap.Compound;
    }
  });

  return compounds;
};

const hasFastestLap = (driverAbbr: string, lapData?: { laps: LapData[] }): boolean => {
  if (!lapData?.laps) return false;
  return lapData.laps.some(lap => lap.Driver === driverAbbr && lap.FastestLap);
};

const getPositionChange = (gridPosition?: number, finishPosition?: number): { change: number; icon: any } | null => {
  if (!gridPosition || !finishPosition) return null;

  const change = gridPosition - finishPosition;

  if (change > 0) {
    return { change, icon: TrendingUp };
  } else if (change < 0) {
    return { change: Math.abs(change), icon: TrendingDown };
  }
  return { change: 0, icon: Minus };
};

const getStatusColor = (status?: string): string => {
  if (!status) return 'text-green-500';
  const statusLower = status.toLowerCase();

  if (statusLower.includes('finished') || statusLower.includes('+')) {
    return 'text-green-500';
  } else if (statusLower.includes('dnf') || statusLower.includes('collision') || statusLower.includes('damage')) {
    return 'text-red-500';
  } else if (statusLower.includes('disqualified')) {
    return 'text-orange-500';
  }
  return 'text-yellow-500';
};

export function EnhancedRaceResults({ results, lapData }: EnhancedRaceResultsProps) {
  // Separate podium (top 3) from the rest
  const podiumResults = results.slice(0, 3);
  const otherResults = results.slice(3);

  const PodiumCard = ({ result, index }: { result: RaceResult; index: number }) => {
    const position = result.Position || index + 1;
    const tireStrategy = getTireStrategy(result.Abbreviation, lapData);
    const teamLogo = getTeamLogo(result.TeamName || result.Team || '');
    const driverPhoto = getDriverPhoto(result);
    const fastestLap = hasFastestLap(result.Abbreviation, lapData) || result.FastestLap;
    const positionChange = getPositionChange(result.GridPosition, position);

    const podiumClass = position === 1 ? 'podium-1' : position === 2 ? 'podium-2' : 'podium-3';
    // Winner is tallest, 2nd place is medium, 3rd is shortest
    const heightClass = position === 1 ? 'lg:min-h-[500px]' : position === 2 ? 'lg:min-h-[440px]' : 'lg:min-h-[400px]';
    const orderClass = position === 1 ? 'lg:order-2' : position === 2 ? 'lg:order-1' : 'lg:order-3';

    return (
      <div
        className={`${podiumClass} ${heightClass} ${orderClass} p-8 rounded-2xl shadow-2xl relative overflow-hidden transition-all hover:scale-105 hover:shadow-3xl duration-300`}
      >
        {/* Decorative shine effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent opacity-50 pointer-events-none" />

        {/* Position Badge - Large and Prominent */}
        <div className="absolute top-6 right-6 z-10">
          <div className="w-20 h-20 rounded-full bg-black/30 backdrop-blur-md flex items-center justify-center border-4 border-white/50 shadow-2xl">
            <span className="text-4xl font-black text-white drop-shadow-2xl">{position}</span>
          </div>
        </div>

        {/* Trophy Icon for Winner - Larger */}
        {position === 1 && (
          <Trophy className="absolute top-6 left-6 h-12 w-12 text-white drop-shadow-2xl animate-pulse z-10" />
        )}

        {/* Podium Position Label */}
        <div className="text-center mb-6 relative z-10">
          <div className="text-xs font-bold text-white/70 uppercase tracking-widest mb-2">
            {position === 1 ? '🏆 Winner' : position === 2 ? '🥈 2nd Place' : '🥉 3rd Place'}
          </div>
        </div>

        {/* Driver Photo - Larger */}
        <div className="flex justify-center mb-6 relative z-10">
          <div className="relative">
            <Avatar className="h-32 w-32 border-4 border-white shadow-2xl ring-4 ring-white/30">
              <AvatarImage src={driverPhoto} alt={result.Abbreviation} />
              <AvatarFallback className="text-3xl font-bold">{result.Abbreviation}</AvatarFallback>
            </Avatar>
            {/* Glow effect behind photo */}
            <div className="absolute inset-0 bg-white/30 rounded-full blur-xl -z-10" />
          </div>
        </div>

        {/* Driver Info - Larger Typography */}
        <div className="text-center mb-6 relative z-10">
          <div className="text-3xl md:text-4xl font-black text-white drop-shadow-2xl mb-2">
            {result.Abbreviation}
          </div>
          <div className="text-base text-white/95 font-semibold">
            {result.FullName || result.Driver}
          </div>
        </div>

        {/* Team - More Prominent */}
        <div className="flex items-center justify-center gap-3 mb-6 relative z-10">
          {teamLogo && (
            <img src={teamLogo} alt={result.TeamName} className="h-6 object-contain brightness-0 invert drop-shadow-lg" />
          )}
          <span className="text-base font-bold text-white/95 drop-shadow-md">{result.TeamName || result.Team}</span>
        </div>

        {/* Tire Strategy - Larger Icons */}
        {tireStrategy.length > 0 && (
          <div className="flex items-center justify-center gap-2 mb-6 relative z-10">
            <div className="text-xs font-bold text-white/70 uppercase tracking-wider mr-1">Strategy:</div>
            {tireStrategy.map((compound, idx) => (
              <div key={idx} title={compound} className="drop-shadow-lg">
                <TireIcon compound={compound} size={36} />
              </div>
            ))}
          </div>
        )}

        {/* Stats Row - Larger and More Prominent */}
        <div className="relative z-10 mt-auto">
          <div className="grid grid-cols-2 gap-4 pt-6 border-t-2 border-white/40">
            {/* Time */}
            <div className="text-center">
              <div className="text-xs text-white/80 font-bold uppercase tracking-wider mb-1">Time</div>
              <div className="text-base font-mono font-black text-white drop-shadow-md">
                {formatTime(result.Time || result.Status, position)}
              </div>
            </div>

            {/* Points */}
            <div className="text-center">
              <div className="text-xs text-white/80 font-bold uppercase tracking-wider mb-1">Points</div>
              <div className="text-3xl font-black text-white drop-shadow-md">{result.Points || 0}</div>
            </div>
          </div>

          {/* Badges - Below stats */}
          <div className="flex items-center justify-center gap-2 mt-4 flex-wrap">
            {fastestLap && (
              <div className="bg-purple-600/90 backdrop-blur-sm text-white px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg">
                <Zap className="h-4 w-4" />
                <span className="text-sm font-bold">Fastest Lap</span>
              </div>
            )}
            {positionChange && positionChange.change !== 0 && (
              <div className={`${positionChange.change > 0 ? 'bg-green-600/90' : 'bg-red-600/90'} backdrop-blur-sm text-white px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg`}>
                {positionChange.change > 0 ? (
                  <>
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm font-bold">+{positionChange.change} {positionChange.change === 1 ? 'place' : 'places'}</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4" />
                    <span className="text-sm font-bold">-{positionChange.change} {positionChange.change === 1 ? 'place' : 'places'}</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const ResultRow = ({ result, index }: { result: RaceResult; index: number }) => {
    const position = result.Position || index + 4;
    const tireStrategy = getTireStrategy(result.Abbreviation, lapData);
    const teamLogo = getTeamLogo(result.TeamName || result.Team || '');
    const driverPhoto = getDriverPhoto(result);
    const fastestLap = hasFastestLap(result.Abbreviation, lapData) || result.FastestLap;
    const positionChange = getPositionChange(result.GridPosition, position);
    const statusColor = getStatusColor(result.Status);

    return (
      <div className="flex items-center gap-4 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-all">
        {/* Position */}
        <div className="flex-shrink-0 w-12">
          <Badge variant="outline" className="w-12 h-12 flex items-center justify-center text-xl font-bold">
            {position}
          </Badge>
        </div>

        {/* Driver Photo */}
        <Avatar className="h-14 w-14 border-2">
          <AvatarImage src={driverPhoto} alt={result.Abbreviation} />
          <AvatarFallback>{result.Abbreviation}</AvatarFallback>
        </Avatar>

        {/* Driver Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-xl">{result.Abbreviation}</span>
            {fastestLap && (
              <Badge variant="secondary" className="bg-purple-600 hover:bg-purple-600 text-white">
                <Zap className="h-3 w-3 mr-1" />
                Fastest Lap
              </Badge>
            )}
            {positionChange && positionChange.change !== 0 && (
              <Badge
                variant="secondary"
                className={positionChange.change > 0 ? 'bg-green-600 hover:bg-green-600' : 'bg-red-600 hover:bg-red-600'}
              >
                {positionChange.change > 0 ? (
                  <>
                    <TrendingUp className="h-3 w-3 mr-1" />
                    +{positionChange.change}
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3 mr-1" />
                    -{positionChange.change}
                  </>
                )}
              </Badge>
            )}
          </div>
          <div className="text-sm text-muted-foreground truncate">
            {result.FullName || result.Driver}
          </div>
          <div className="flex items-center gap-2 mt-1">
            {teamLogo && (
              <img src={teamLogo} alt={result.TeamName} className="h-4 object-contain" />
            )}
            <span className="text-sm text-muted-foreground">{result.TeamName || result.Team}</span>
          </div>
        </div>

        {/* Tire Strategy */}
        {tireStrategy.length > 0 && (
          <div className="hidden md:flex items-center gap-1">
            {tireStrategy.map((compound, idx) => (
              <div key={idx} title={compound}>
                <TireIcon compound={compound} size={28} />
              </div>
            ))}
          </div>
        )}

        {/* Time/Status */}
        <div className="text-right min-w-[120px]">
          <div className="font-mono font-semibold">
            {formatTime(result.Time || result.Status, position)}
          </div>
          {result.Status && !result.Time && (
            <div className={`text-xs flex items-center gap-1 justify-end mt-1 ${statusColor}`}>
              <AlertCircle className="h-3 w-3" />
              <span>{result.Status}</span>
            </div>
          )}
        </div>

        {/* Points */}
        <div className="text-right min-w-[60px]">
          <Badge variant="secondary" className="text-lg font-bold px-3 py-1">
            {result.Points || 0}
          </Badge>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Podium Section */}
      <div>
        <h3 className="text-3xl font-black mb-8 flex items-center gap-3">
          <Trophy className="h-8 w-8 text-[var(--gold)]" />
          Podium Finishers
        </h3>
        {/* Podium layout: 2nd, 1st, 3rd (winner in center, taller) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-4 items-end">
          {podiumResults.map((result, index) => (
            <PodiumCard key={result.DriverNumber || index} result={result} index={index} />
          ))}
        </div>
      </div>

      {/* Rest of Field */}
      {otherResults.length > 0 && (
        <div>
          <h3 className="text-xl font-bold mb-4 text-muted-foreground">Rest of Field</h3>
          <div className="space-y-2">
            {otherResults.map((result, index) => (
              <ResultRow key={result.DriverNumber || index} result={result} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
