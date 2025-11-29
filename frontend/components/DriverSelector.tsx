'use client';

import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';

interface Driver {
  abbreviation: string;
  name: string;
  team: string;
}

interface DriverSelectorProps {
  drivers: Driver[];
  selectedDrivers: string[];
  onDriverToggle: (abbreviation: string) => void;
  maxSelection?: number;
}

// Team colors for driver chips
const DRIVER_COLORS: Record<string, string> = {
  VER: '#3671C6',
  PER: '#3671C6',
  HAM: '#27F4D2',
  RUS: '#27F4D2',
  LEC: '#E8002D',
  SAI: '#E8002D',
  NOR: '#FF8000',
  PIA: '#FF8000',
  ALO: '#229971',
  STR: '#229971',
  TSU: '#6692FF',
  RIC: '#6692FF',
  ALB: '#64C4FF',
  SAR: '#64C4FF',
  HUL: '#B6BABD',
  MAG: '#B6BABD',
  OCO: '#FF87BC',
  GAS: '#FF87BC',
  ZHO: '#52E252',
  BOT: '#52E252',
};

export function DriverSelector({
  drivers,
  selectedDrivers,
  onDriverToggle,
  maxSelection = 10
}: DriverSelectorProps) {
  const handleToggle = (abbreviation: string) => {
    const isSelected = selectedDrivers.includes(abbreviation);

    // Allow deselection or selection if under max
    if (isSelected || selectedDrivers.length < maxSelection) {
      onDriverToggle(abbreviation);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Select Drivers
        </CardTitle>
        <CardDescription>
          Choose up to {maxSelection} drivers to compare ({selectedDrivers.length} selected)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {drivers.map((driver) => {
            const isSelected = selectedDrivers.includes(driver.abbreviation);
            const isDisabled = !isSelected && selectedDrivers.length >= maxSelection;
            const color = DRIVER_COLORS[driver.abbreviation] || '#888888';

            return (
              <div
                key={driver.abbreviation}
                className={`flex items-center space-x-2 p-2 rounded-md border transition-all ${
                  isSelected
                    ? 'bg-accent border-accent-foreground'
                    : isDisabled
                    ? 'opacity-40 cursor-not-allowed'
                    : 'hover:bg-accent/50 cursor-pointer'
                }`}
                onClick={() => !isDisabled && handleToggle(driver.abbreviation)}
              >
                <Checkbox
                  id={driver.abbreviation}
                  checked={isSelected}
                  onCheckedChange={() => handleToggle(driver.abbreviation)}
                  disabled={isDisabled}
                />
                <Label
                  htmlFor={driver.abbreviation}
                  className={`flex-1 cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 ${
                    isDisabled ? 'cursor-not-allowed' : ''
                  }`}
                >
                  <span
                    className="inline-block w-2 h-2 rounded-full mr-1.5"
                    style={{ backgroundColor: color }}
                  />
                  {driver.abbreviation}
                </Label>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
