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

interface RaceMessage {
  Time: string;
  Category: string;
  Message: string;
  Flag?: string;
  Scope?: string;
  Lap?: number;
  RacingNumber?: string;
}

interface SessionData {
  race_control_messages: RaceMessage[];
}

interface RaceReplayProps {
  year: number;
  round: number;
}

export default function RaceReplay({ year, round }: RaceReplayProps) {
  const [data, setData] = useState<RaceReplayData | null>(null);
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
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

    // Load session data for race control messages
    fetch(`http://localhost:8000/fastf1/session-data/${year}/${round}/R`)
      .then(res => res.json())
      .then(sessionData => {
        setSessionData(sessionData);
      })
      .catch(err => {
        console.error('Error loading session data:', err);
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

  // Get current tire compound for a driver based on current lap
  const getCurrentTireCompound = (driverAbbr: string): string | null => {
    if (!data) return null;

    const currentLapNum = getCurrentLap();
    const driver = data.drivers.find(d => d.driver === driverAbbr);
    if (!driver || !driver.positions) return null;

    // Get the position data for the current lap (lap numbers are 1-indexed)
    const lapPosition = driver.positions[currentLapNum - 1];
    return lapPosition?.compound || null;
  };

  // Get gap information for drivers - comparing their lap and track progress
  // Returns the lap number and approximate progress they're on
  const getDriverProgressInfo = (driverTelemetry: DriverTelemetry) => {
    if (driverTelemetry.lapBoundaries.length === 0) return null;

    const totalPositions = driverTelemetry.positions.length;

    // Find which lap the driver is in
    let currentLapBoundary = null;
    let nextLapBoundary = null;
    let lapIndex = -1;

    for (let i = 0; i < driverTelemetry.lapBoundaries.length; i++) {
      const lap = driverTelemetry.lapBoundaries[i];
      const lapEndTime = lap.cumulativeTime + lap.lapTime;

      if (currentTime >= lap.cumulativeTime && currentTime < lapEndTime) {
        currentLapBoundary = lap;
        nextLapBoundary = driverTelemetry.lapBoundaries[i + 1] || null;
        lapIndex = i;
        break;
      }
    }

    // If beyond all laps
    if (!currentLapBoundary) {
      const lastLap = driverTelemetry.lapBoundaries[driverTelemetry.lapBoundaries.length - 1];
      if (!lastLap) return null;
      return {
        lapNumber: lastLap.lapNumber,
        lapIndex: driverTelemetry.lapBoundaries.length - 1,
        progress: 1.0, // 100% of lap complete
        totalTime: lastLap.cumulativeTime + lastLap.lapTime
      };
    }

    // Calculate progress within current lap
    const timeIntoLap = currentTime - currentLapBoundary.cumulativeTime;
    const lapProgress = timeIntoLap / currentLapBoundary.lapTime;

    return {
      lapNumber: currentLapBoundary.lapNumber,
      lapIndex: lapIndex,
      progress: lapProgress,
      totalTime: currentLapBoundary.cumulativeTime + timeIntoLap
    };
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
    const lapProgress = timeIntoLap / currentLapBoundary.lapTime;

    // Find the end index for this lap's position data
    const endIndex = nextLapBoundary ? nextLapBoundary.startIndex : totalPositions;

    // Calculate exact position within this lap (with decimal for interpolation)
    const lapLength = endIndex - currentLapBoundary.startIndex;
    const exactPositionInLap = lapProgress * lapLength;
    const positionIndex = Math.floor(currentLapBoundary.startIndex + exactPositionInLap);

    // Handle interpolation, including across lap boundaries
    let currentPoint, nextPoint;
    let t; // interpolation factor

    if (positionIndex >= endIndex - 1) {
      // We're at the end of this lap, interpolate to the start of next lap if available
      currentPoint = driverTelemetry.positions[endIndex - 1];
      if (nextLapBoundary && nextLapBoundary.startIndex < totalPositions) {
        // Interpolate to first point of next lap
        nextPoint = driverTelemetry.positions[nextLapBoundary.startIndex];
        // Calculate how far past the end we are (0 to 1)
        t = exactPositionInLap - (endIndex - currentLapBoundary.startIndex - 1);
      } else {
        // No next lap, stay at the last position
        nextPoint = currentPoint;
        t = 0;
      }
    } else {
      // Normal interpolation within the lap
      currentPoint = driverTelemetry.positions[positionIndex];
      nextPoint = driverTelemetry.positions[positionIndex + 1];
      t = exactPositionInLap - Math.floor(exactPositionInLap);
    }

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

  // Get relevant race messages for current time (show messages from last 30 seconds)
  const getRelevantMessages = (): RaceMessage[] => {
    if (!sessionData || !sessionData.race_control_messages) return [];

    // Convert current lap to approximate race time for filtering
    const currentLapNum = getCurrentLap();

    // Filter messages by lap - show messages from current lap and previous lap
    return sessionData.race_control_messages
      .filter(msg => {
        if (!msg.Lap) return true; // Include messages without lap info
        return msg.Lap >= currentLapNum - 1 && msg.Lap <= currentLapNum;
      })
      .slice(-5); // Show last 5 messages
  };

  const relevantMessages = getRelevantMessages();

  return (
    <div className="space-y-6">
      {/* Track Map Visualization */}
      {telemetryData && trackBounds && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Track Map - Lap {currentLap}</h3>
          <div className="bg-gray-800/50 rounded-lg p-4 relative">
            {/* Live Race Order Overlay */}
            <div className="absolute top-4 left-4 bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg p-3 z-10">
              <h4 className="text-sm font-bold text-gray-300 mb-2 uppercase tracking-wide">Live Order</h4>
              <div className="space-y-1">
                {telemetryData.drivers
                  .map(driverTelemetry => {
                    const driverPos = getDriverPosition(driverTelemetry);
                    const progressInfo = getDriverProgressInfo(driverTelemetry);
                    const compound = getCurrentTireCompound(driverTelemetry.driver);
                    return {
                      driver: driverTelemetry.driver,
                      color: driverTelemetry.color,
                      position: driverPos?.position || 999,
                      progressInfo: progressInfo,
                      compound: compound,
                      telemetry: driverTelemetry
                    };
                  })
                  .sort((a, b) => a.position - b.position)
                  .map((driver, index, sortedDrivers) => {
                    // Calculate time gap to driver ahead based on total race time
                    let timeGap = null;
                    if (index > 0 && driver.progressInfo && sortedDrivers[index - 1].progressInfo) {
                      const gap = driver.progressInfo.totalTime - sortedDrivers[index - 1].progressInfo.totalTime;
                      timeGap = gap;
                    }

                    // Tire compound color mapping
                    const tireColors: { [key: string]: string } = {
                      'SOFT': '#ff0000',
                      'MEDIUM': '#ffff00',
                      'HARD': '#ffffff',
                      'INTERMEDIATE': '#00ff00',
                      'WET': '#0000ff'
                    };

                    // Get first letter of compound
                    const compoundLetter = driver.compound ? driver.compound.charAt(0).toUpperCase() : '';

                    return (
                      <div key={driver.driver} className="flex items-center gap-2 text-xs">
                        <span className="w-5 text-right font-bold text-gray-400">{driver.position}</span>
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: driver.color }}
                        />
                        <span className="font-medium text-white w-8">{driver.driver}</span>
                        <div className="w-4 flex items-center justify-center">
                          {driver.compound && (
                            <div
                              className="w-4 h-4 rounded-full border border-gray-600 flex items-center justify-center"
                              style={{ backgroundColor: tireColors[driver.compound.toUpperCase()] || '#999' }}
                              title={driver.compound}
                            >
                              <span className="text-[8px] font-bold text-black">
                                {compoundLetter}
                              </span>
                            </div>
                          )}
                        </div>
                        {timeGap !== null && timeGap > 0.1 && (
                          <span className="text-gray-500 ml-auto font-mono">
                            +{timeGap.toFixed(1)}s
                          </span>
                        )}
                      </div>
                    );
                  })
                }
              </div>
            </div>

            {/* Race Messages Overlay */}
            {relevantMessages.length > 0 && (
              <div className="absolute top-4 right-4 bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg p-3 z-10 max-w-sm">
                <h4 className="text-sm font-bold text-gray-300 mb-2 uppercase tracking-wide">Race Control</h4>
                <div className="space-y-2">
                  {relevantMessages.map((msg, index) => {
                    // Determine flag color
                    let flagColor = 'border-gray-500';

                    if (msg.Flag === 'YELLOW' || msg.Category === 'Flag' && msg.Message.includes('YELLOW')) {
                      flagColor = 'border-yellow-400';
                    } else if (msg.Flag === 'RED' || msg.Category === 'Flag' && msg.Message.includes('RED')) {
                      flagColor = 'border-red-500';
                    } else if (msg.Flag === 'GREEN' || msg.Category === 'Flag' && msg.Message.includes('GREEN')) {
                      flagColor = 'border-green-400';
                    } else if (msg.Flag === 'BLUE' || msg.Message.includes('BLUE FLAG')) {
                      flagColor = 'border-blue-400';
                    } else if (msg.Message.includes('SAFETY CAR')) {
                      flagColor = 'border-yellow-400';
                    }

                    return (
                      <div
                        key={`${msg.Time}-${index}`}
                        className={`border-l-2 ${flagColor} pl-2 py-1`}
                      >
                        <p className="text-xs text-white leading-tight">{msg.Message}</p>
                        {msg.Lap && (
                          <span className="text-[10px] text-gray-400">Lap {msg.Lap}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Flag Status Indicator */}
            {(() => {
              // Determine current flag status from most recent message
              let currentFlag = 'GREEN';
              let flagBg = 'bg-green-500';

              if (relevantMessages.length > 0) {
                const latestMsg = relevantMessages[relevantMessages.length - 1];
                if (latestMsg.Flag === 'YELLOW' || latestMsg.Message.includes('YELLOW') || latestMsg.Message.includes('SAFETY CAR')) {
                  currentFlag = 'YELLOW';
                  flagBg = 'bg-yellow-400';
                } else if (latestMsg.Flag === 'RED' || latestMsg.Message.includes('RED FLAG')) {
                  currentFlag = 'RED';
                  flagBg = 'bg-red-500';
                } else if (latestMsg.Flag === 'GREEN' || latestMsg.Message.includes('GREEN')) {
                  currentFlag = 'GREEN';
                  flagBg = 'bg-green-500';
                }
              }

              const isYellow = currentFlag === 'YELLOW';

              return (
                <div className="absolute bottom-4 right-4 bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg p-3 z-10">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-6 h-6 rounded ${flagBg} ${isYellow ? 'yellow-light-flash' : ''}`}
                    />
                    <span className="text-sm font-bold text-gray-300">{currentFlag} FLAG</span>
                  </div>
                </div>
              );
            })()}

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

// Add CSS for yellow flag flashing animation
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes yellowFlash {
      0%, 100% { opacity: 1; background-color: rgb(250, 204, 21); }
      50% { opacity: 0.3; background-color: rgb(250, 204, 21, 0.3); }
    }

    @keyframes yellowBorderFlash {
      0%, 100% { border-color: rgb(250, 204, 21); }
      50% { border-color: rgb(250, 204, 21, 0.5); }
    }

    .yellow-light-flash {
      animation: yellowFlash 1s ease-in-out infinite;
    }

    .yellow-flag-flash {
      animation: yellowBorderFlash 1s ease-in-out infinite;
    }
  `;
  if (!document.getElementById('race-replay-styles')) {
    style.id = 'race-replay-styles';
    document.head.appendChild(style);
  }
}
