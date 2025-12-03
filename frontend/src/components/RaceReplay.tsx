import { useEffect, useState, useRef } from 'react';

interface Position {
  lap: number;
  position: number | null;
  lapTime: string | null;
  compound: string | null;
}

interface Driver {
  driver: string;
  team: string;
  color: string;
  positions: Position[];
}

interface RaceReplayData {
  year: number;
  roundNumber: number;
  totalLaps: number;
  drivers: Driver[];
}

interface TrackCoordinate {
  x: number;
  y: number;
}

interface DriverTelemetry {
  driver: string;
  color: string;
  positions: TrackCoordinate[];
  lapBoundaries: {
    lapNumber: number;
    startIndex: number;
    position: number;
    cumulativeTime: number;
    lapTime: number;
  }[];
}

interface TelemetryData {
  year: number;
  roundNumber: number;
  track: TrackCoordinate[];
  pitlane: TrackCoordinate[];
  drivers: DriverTelemetry[];
}

interface RaceReplayProps {
  year: number;
  round: number;
}

export default function RaceReplay({ year, round }: RaceReplayProps) {
  const [data, setData] = useState<RaceReplayData | null>(null);
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0); // Time in seconds from start
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const animationRef = useRef<number | null>(null);
  const lastUpdateRef = useRef<number>(0);

  // Calculate total race duration from telemetry data (winner's total time)
  const getTotalRaceDuration = (): number => {
    if (!telemetryData || telemetryData.drivers.length === 0) {
      return 0;
    }

    // Find the longest race time among all drivers (usually the winner)
    let maxDuration = 0;
    for (const driver of telemetryData.drivers) {
      if (driver.lapBoundaries.length > 0) {
        const lastLap = driver.lapBoundaries[driver.lapBoundaries.length - 1];
        const driverTotalTime = lastLap.cumulativeTime + lastLap.lapTime;
        maxDuration = Math.max(maxDuration, driverTotalTime);
      }
    }

    return maxDuration;
  };

  useEffect(() => {
    // Load race replay data for lap-by-lap position tracking
    fetch(`http://localhost:8000/fastf1/race-replay/${year}/${round}`)
      .then(res => res.json())
      .then(data => {
        setData(data);
      })
      .catch(err => {
        console.error('Error loading race replay data:', err);
      });

    // Load full telemetry data for smooth animation
    fetch(`http://localhost:8000/fastf1/race-telemetry/${year}/${round}`)
      .then(res => res.json())
      .then(telemetryData => {
        setTelemetryData(telemetryData);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading telemetry data:', err);
        setLoading(false);
      });
  }, [year, round]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !data || !telemetryData) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      return;
    }

    const animate = (timestamp: number) => {
      if (lastUpdateRef.current === 0) {
        lastUpdateRef.current = timestamp;
      }

      const deltaTime = (timestamp - lastUpdateRef.current) / 1000; // Convert to seconds
      lastUpdateRef.current = timestamp;

      setCurrentTime(prevTime => {
        const newTime = prevTime + deltaTime * playbackSpeed;
        const totalRaceDuration = getTotalRaceDuration();

        if (newTime >= totalRaceDuration) {
          setIsPlaying(false);
          return totalRaceDuration;
        }

        return newTime;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, data, telemetryData]);

  const togglePlay = () => {
    if (!data || !telemetryData) return;

    const totalRaceDuration = getTotalRaceDuration();
    if (currentTime >= totalRaceDuration) {
      setCurrentTime(0);
      lastUpdateRef.current = 0;
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeChange = (time: number) => {
    setCurrentTime(time);
    setIsPlaying(false);
    lastUpdateRef.current = 0;
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
  };

  // Calculate current lap based on time - use the first driver's lap boundaries as reference
  const getCurrentLap = () => {
    if (!data || !telemetryData || telemetryData.drivers.length === 0) return 1;

    // Use the first driver as reference for lap numbering
    const referenceDriver = telemetryData.drivers[0];
    if (!referenceDriver || referenceDriver.lapBoundaries.length === 0) return 1;

    // Find which lap we're in based on current time
    for (const lap of referenceDriver.lapBoundaries) {
      const lapEndTime = lap.cumulativeTime + lap.lapTime;
      if (currentTime >= lap.cumulativeTime && currentTime < lapEndTime) {
        return lap.lapNumber;
      }
    }

    // If beyond all laps, return the last lap number
    const lastLap = referenceDriver.lapBoundaries[referenceDriver.lapBoundaries.length - 1];
    return lastLap ? lastLap.lapNumber : data.totalLaps;
  };

  // Get driver position at current time using race time synchronization
  const getDriverPosition = (driverTelemetry: DriverTelemetry) => {
    const totalPositions = driverTelemetry.positions.length;
    if (totalPositions === 0 || driverTelemetry.lapBoundaries.length === 0) return null;

    // Find which lap the driver is in based on current race time
    let currentLapBoundary = null;
    let nextLapBoundary = null;

    for (let i = 0; i < driverTelemetry.lapBoundaries.length; i++) {
      const lap = driverTelemetry.lapBoundaries[i];
      const lapEndTime = lap.cumulativeTime + lap.lapTime;

      if (currentTime >= lap.cumulativeTime && currentTime < lapEndTime) {
        currentLapBoundary = lap;
        nextLapBoundary = driverTelemetry.lapBoundaries[i + 1] || null;
        break;
      }
    }

    // If current time is beyond driver's last lap, show them at their final position
    if (!currentLapBoundary) {
      const lastLap = driverTelemetry.lapBoundaries[driverTelemetry.lapBoundaries.length - 1];
      if (!lastLap) return null;

      // Show them at the end of their last completed lap
      const lastPositionIndex = totalPositions - 1;
      return {
        ...driverTelemetry.positions[lastPositionIndex],
        position: lastLap.position,
        isDnf: true  // Mark as DNF so we can style differently if needed
      };
    }

    // Calculate progress within current lap based on actual time elapsed
    const timeIntoLap = currentTime - currentLapBoundary.cumulativeTime;
    const lapProgress = Math.min(timeIntoLap / currentLapBoundary.lapTime, 1.0);

    // Find the end index for this lap's position data
    const endIndex = nextLapBoundary ? nextLapBoundary.startIndex : totalPositions;

    // Calculate exact position within this lap (with decimal for interpolation)
    const lapLength = endIndex - currentLapBoundary.startIndex;
    const exactPositionInLap = lapProgress * lapLength;
    const positionIndex = Math.min(currentLapBoundary.startIndex + Math.floor(exactPositionInLap), endIndex - 1);
    const nextPositionIndex = Math.min(positionIndex + 1, endIndex - 1);

    // Get the two points to interpolate between
    const currentPoint = driverTelemetry.positions[positionIndex];
    const nextPoint = driverTelemetry.positions[nextPositionIndex];

    // Calculate interpolation factor (0 to 1 between current and next point)
    const t = exactPositionInLap - Math.floor(exactPositionInLap);

    // Linear interpolation between points for smooth movement
    const interpolatedX = currentPoint.x + (nextPoint.x - currentPoint.x) * t;
    const interpolatedY = currentPoint.y + (nextPoint.y - currentPoint.y) * t;

    return {
      x: interpolatedX,
      y: interpolatedY,
      position: currentLapBoundary.position
    };
  };

  if (loading) {
    return (
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-400">Loading race replay data...</p>
      </div>
    );
  }

  if (!data || !telemetryData) {
    return (
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-8 text-center">
        <p className="text-red-400">Failed to load race replay data</p>
      </div>
    );
  }

  const currentLap = getCurrentLap();
  const totalRaceDuration = getTotalRaceDuration();

  // Get current standings for this lap
  const currentStandings = data.drivers
    .map(driver => {
      const lapData = driver.positions[currentLap - 1];
      return {
        ...driver,
        currentPosition: lapData?.position,
        lapTime: lapData?.lapTime,
        compound: lapData?.compound,
      };
    })
    .filter(d => d.currentPosition !== null)
    .sort((a, b) => (a.currentPosition || 999) - (b.currentPosition || 999));

  const speeds = [0.5, 1, 2, 4, 8];

  // Calculate track bounds for SVG viewBox
  const getTrackBounds = () => {
    if (!telemetryData || telemetryData.track.length === 0) return null;

    const xs = telemetryData.track.map(p => p.x);
    const ys = telemetryData.track.map(p => p.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const padding = 500;

    return {
      minX: minX - padding,
      minY: minY - padding,
      width: maxX - minX + 2 * padding,
      height: maxY - minY + 2 * padding,
    };
  };

  const trackBounds = getTrackBounds();

  return (
    <div className="space-y-6">
      {/* Track Map Visualization */}
      {telemetryData && trackBounds && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Track Map - Lap {currentLap}</h3>
          <div className="bg-gray-800/50 rounded-lg p-4">
            <svg
              viewBox={`${trackBounds.minX} ${trackBounds.minY} ${trackBounds.width} ${trackBounds.height}`}
              className="w-full h-auto"
              style={{ transform: 'scaleX(-1) rotate(-90deg)', maxHeight: '800px' }}
            >
              {/* Draw track outline */}
              <polyline
                points={telemetryData.track.map(p => `${p.x},${p.y}`).join(' ')}
                fill="none"
                stroke="#4B5563"
                strokeWidth="150"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Draw pit lane */}
              {telemetryData.pitlane && telemetryData.pitlane.length > 0 && (
                <polyline
                  points={telemetryData.pitlane.map(p => `${p.x},${p.y}`).join(' ')}
                  fill="none"
                  stroke="#6B7280"
                  strokeWidth="120"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeDasharray="150,150"
                  opacity="0.7"
                />
              )}

              {/* Draw car positions using telemetry data */}
              {telemetryData.drivers.map((driverTelemetry) => {
                const driverPos = getDriverPosition(driverTelemetry);
                if (!driverPos) return null;

                return (
                  <g key={driverTelemetry.driver}>
                    <circle
                      cx={driverPos.x}
                      cy={driverPos.y}
                      r="150"
                      fill={driverTelemetry.color}
                      opacity="0.9"
                    />
                    <text
                      x={driverPos.x}
                      y={driverPos.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="white"
                      fontSize="120"
                      fontWeight="bold"
                      style={{ transform: 'scaleY(-1)', transformOrigin: `${driverPos.x}px ${driverPos.y}px` }}
                    >
                      {driverPos.position}
                    </text>
                  </g>
                );
              })}
            </svg>
            <p className="text-sm text-gray-400 text-center mt-2">
              {telemetryData.track.length} track data points • {currentTime.toFixed(1)}s / {totalRaceDuration.toFixed(0)}s
            </p>
          </div>
        </div>
      )}

      {/* Race Progress Visualization */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">
              Lap {currentLap} / {data.totalLaps}
            </h3>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Speed:</span>
              {speeds.map(speed => (
                <button
                  key={speed}
                  onClick={() => handleSpeedChange(speed)}
                  className={`px-3 py-1 rounded text-sm ${
                    playbackSpeed === speed
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>

          {/* Time Slider */}
          <div className="space-y-2">
            <input
              type="range"
              min="0"
              max={totalRaceDuration}
              step="0.1"
              value={currentTime}
              onChange={(e) => handleTimeChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #ef4444 0%, #ef4444 ${(currentTime / totalRaceDuration) * 100}%, #374151 ${(currentTime / totalRaceDuration) * 100}%, #374151 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0:00</span>
              <span>{Math.floor(totalRaceDuration / 60)}:{(totalRaceDuration % 60).toFixed(0).padStart(2, '0')}</span>
            </div>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex justify-center gap-4 mb-6">
          <button
            onClick={() => handleTimeChange(Math.max(0, currentTime - 90))}
            disabled={currentTime === 0}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:text-gray-600 rounded transition-colors"
          >
            ← Prev Lap
          </button>
          <button
            onClick={togglePlay}
            className="px-6 py-2 bg-red-500 hover:bg-red-600 rounded font-semibold transition-colors"
          >
            {isPlaying ? '⏸ Pause' : currentTime >= totalRaceDuration ? '↺ Replay' : '▶ Play'}
          </button>
          <button
            onClick={() => handleTimeChange(Math.min(totalRaceDuration, currentTime + 90))}
            disabled={currentTime >= totalRaceDuration}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:text-gray-600 rounded transition-colors"
          >
            Next Lap →
          </button>
        </div>

        {/* Position Chart */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="space-y-2">
            {currentStandings.map((driver, index) => {
              // Calculate position change from start
              const startPosition = driver.positions[0]?.position || driver.currentPosition;
              const positionChange = startPosition && driver.currentPosition
                ? startPosition - driver.currentPosition
                : 0;

              return (
                <div
                  key={driver.driver}
                  className="flex items-center gap-3 p-2 rounded hover:bg-gray-700/50 transition-colors"
                >
                  {/* Position */}
                  <div className="w-8 text-center font-bold text-lg">
                    {driver.currentPosition}
                  </div>

                  {/* Driver Bar */}
                  <div
                    className="flex-1 flex items-center justify-between px-4 py-2 rounded"
                    style={{ backgroundColor: driver.color + '40', borderLeft: `4px solid ${driver.color}` }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-white">{driver.driver}</span>
                      <span className="text-sm text-gray-300">{driver.team}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      {driver.compound && (
                        <span className="px-2 py-0.5 bg-gray-900/50 rounded text-xs">
                          {driver.compound}
                        </span>
                      )}
                      {driver.lapTime && (
                        <span className="text-gray-400">{driver.lapTime}</span>
                      )}
                      {positionChange !== 0 && (
                        <span className={`font-semibold ${positionChange > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {positionChange > 0 ? '↑' : '↓'} {Math.abs(positionChange)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
