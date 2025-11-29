'use client';

import { useMemo } from 'react';

interface Corner {
  X: number;
  Y: number;
}

interface CircuitInfo {
  corners: Corner[];
  rotation: number;
}

interface TrackMapProps {
  circuitInfo: CircuitInfo | null;
  className?: string;
}

export function TrackMap({ circuitInfo, className = '' }: TrackMapProps) {
  const { pathD, viewBox } = useMemo(() => {
    if (!circuitInfo || !circuitInfo.corners || circuitInfo.corners.length === 0) {
      return { pathD: '', viewBox: '0 0 100 100' };
    }

    const corners = circuitInfo.corners;

    // Find min/max for viewBox
    const xCoords = corners.map(c => c.X);
    const yCoords = corners.map(c => c.Y);
    const minX = Math.min(...xCoords);
    const maxX = Math.max(...xCoords);
    const minY = Math.min(...yCoords);
    const maxY = Math.max(...yCoords);

    // Add padding
    const padding = 500;
    const viewBoxStr = `${minX - padding} ${minY - padding} ${maxX - minX + padding * 2} ${maxY - minY + padding * 2}`;

    // Create smooth curved path using Catmull-Rom spline
    const tension = 0.5; // Controls smoothness (0 = straight lines, 1 = very smooth)

    const getControlPoints = (p0: Corner, p1: Corner, p2: Corner, p3: Corner) => {
      const d1 = Math.sqrt((p1.X - p0.X) ** 2 + (p1.Y - p0.Y) ** 2);
      const d2 = Math.sqrt((p2.X - p1.X) ** 2 + (p2.Y - p1.Y) ** 2);
      const d3 = Math.sqrt((p3.X - p2.X) ** 2 + (p3.Y - p2.Y) ** 2);

      const t1 = tension * d2 / (d1 + d2);
      const t2 = tension * d2 / (d2 + d3);

      const cp1x = p1.X + t1 * (p2.X - p0.X);
      const cp1y = p1.Y + t1 * (p2.Y - p0.Y);
      const cp2x = p2.X - t2 * (p3.X - p1.X);
      const cp2y = p2.Y - t2 * (p3.Y - p1.Y);

      return { cp1x, cp1y, cp2x, cp2y };
    };

    let path = `M ${corners[0].X} ${corners[0].Y}`;

    for (let i = 0; i < corners.length; i++) {
      const p0 = corners[(i - 1 + corners.length) % corners.length];
      const p1 = corners[i];
      const p2 = corners[(i + 1) % corners.length];
      const p3 = corners[(i + 2) % corners.length];

      const { cp1x, cp1y, cp2x, cp2y } = getControlPoints(p0, p1, p2, p3);
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.X} ${p2.Y}`;
    }

    path += ' Z';

    return { pathD: path, viewBox: viewBoxStr };
  }, [circuitInfo]);

  if (!circuitInfo || !circuitInfo.corners || circuitInfo.corners.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-muted/30 rounded-lg ${className}`}>
        <span className="text-sm text-muted-foreground">Track map unavailable</span>
      </div>
    );
  }

  return (
    <svg
      viewBox={viewBox}
      className={`${className}`}
      preserveAspectRatio="xMidYMid meet"
      style={{ transform: 'rotate(-90deg) scaleY(-1)' }}
    >
      {/* Track outline */}
      <path
        d={pathD}
        fill="none"
        stroke="currentColor"
        strokeWidth="150"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-primary"
      />
      {/* Track center line for contrast */}
      <path
        d={pathD}
        fill="none"
        stroke="hsl(var(--background))"
        strokeWidth="80"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
    </svg>
  );
}
