# FastF1 API Reference - Complete Guide

This document provides the correct imports, endpoints, and usage patterns for FastF1 v3.6.1.

## Installation

```bash
pip install fastf1
```

**Requirements:** Python 3.8 or higher

## Core Imports

```python
import fastf1
import fastf1.plotting
from fastf1 import plotting
```

## Basic Setup

### Enable Caching (Recommended)

```python
import fastf1

# Enable cache to speed up data loading
fastf1.Cache.enable_cache('path/to/cache')
```

### Setup Plotting

```python
import fastf1.plotting

fastf1.plotting.setup_mpl(color_scheme='fastf1')
```

## Main Entry Points

### 1. Get Session

```python
# By round number
session = fastf1.get_session(2021, 7, 'Q')  # Year, Round, Session Type

# By event name
session = fastf1.get_session(2021, 'French Grand Prix', 'Q')

# By location
session = fastf1.get_session(2021, 'Silverstone', 'Q')
```

**Session Types:**
- `'FP1'`, `'FP2'`, `'FP3'` - Free Practice sessions
- `'Q'` - Qualifying
- `'S'` - Sprint
- `'SQ'` - Sprint Qualifying/Sprint Shootout
- `'R'` - Race

### 2. Get Event

```python
# Get event information
event = fastf1.get_event(2021, 7)
event = fastf1.get_event(2021, 'French Grand Prix')

# Access event properties
print(event['EventName'])
print(event['Country'])
print(event['Location'])
```

### 3. Get Event Schedule

```python
# Get full season schedule
schedule = fastf1.get_event_schedule(2021)

# Access specific events
gp = schedule.get_event_by_round(12)
gp = schedule.get_event_by_name('Austin')
```

## Session Object

### Loading Session Data

```python
session = fastf1.get_session(2021, 'French Grand Prix', 'Q')

# Load all data (default)
session.load()

# Load specific data
session.load(
    laps=True,          # Load lap timing data
    telemetry=True,     # Load telemetry data
    weather=True,       # Load weather data
    messages=True       # Load race control messages
)

# Load without telemetry (faster)
session.load(telemetry=False)
```

### Session Properties

```python
session.name                    # 'Qualifying', 'Race', etc.
session.date                    # Session date
session.event                   # Associated Event object
session.session_info            # Session metadata dict
session.drivers                 # List of driver numbers (strings)
session.results                 # SessionResults DataFrame
session.laps                    # Laps DataFrame
session.total_laps              # Total scheduled laps (Race/Sprint)
session.weather_data            # Weather DataFrame
session.car_data                # Dict of telemetry by driver
session.pos_data                # Dict of position data by driver
session.session_status          # Session status DataFrame
session.track_status            # Track status DataFrame
session.race_control_messages   # Race control messages DataFrame
session.session_start_time      # Timedelta of session start
session.t0_date                 # Datetime of data stream start
```

### Session Methods

```python
# Get driver information
driver = session.get_driver('VER')  # By abbreviation
driver = session.get_driver('1')    # By number

# Get circuit information
circuit_info = session.get_circuit_info()
```

## Working with Laps

### Accessing Laps

```python
session.load()
laps = session.laps  # All laps from all drivers
```

### Lap Data Columns

```python
# Available columns in laps DataFrame:
laps.columns
# ['Time', 'Driver', 'DriverNumber', 'LapTime', 'LapNumber', 'Stint',
#  'PitOutTime', 'PitInTime', 'Sector1Time', 'Sector2Time', 'Sector3Time',
#  'Sector1SessionTime', 'Sector2SessionTime', 'Sector3SessionTime',
#  'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 'IsPersonalBest',
#  'Compound', 'TyreLife', 'FreshTyre', 'Team', 'LapStartTime',
#  'LapStartDate', 'TrackStatus', 'Position', 'Deleted', 'DeletedReason',
#  'FastF1Generated', 'IsAccurate']
```

### Filtering Laps

```python
# Pick specific driver(s)
ver_laps = laps.pick_drivers('VER')
ver_laps = laps.pick_drivers(1)  # By number
multi_laps = laps.pick_drivers(['VER', 'HAM', 5])

# Pick specific lap(s)
lap_1 = laps.pick_laps(1)
laps_10_to_20 = laps.pick_laps(range(10, 21))

# Pick specific team(s)
rbr_laps = laps.pick_teams('Red Bull')
multiple_teams = laps.pick_teams(['Haas', 'Alpine'])

# Pick fastest lap
fastest = laps.pick_fastest()
fastest_by_time_only = laps.pick_fastest(only_by_time=True)

# Pick quick laps (within 107% of fastest)
quick_laps = laps.pick_quicklaps()
quick_laps = laps.pick_quicklaps(threshold=1.05)  # Custom threshold

# Pick by compound
soft_laps = laps.pick_compounds('SOFT')
slick_laps = laps.pick_compounds(['SOFT', 'MEDIUM', 'HARD'])

# Pick by track status
green_flag = laps.pick_track_status('1', how='equals')

# Filter out pit laps
no_pit_laps = laps.pick_wo_box()

# Pick pit laps
in_laps = laps.pick_box_laps(which='in')
out_laps = laps.pick_box_laps(which='out')
all_pit_laps = laps.pick_box_laps(which='both')

# Pick not deleted laps
valid_laps = laps.pick_not_deleted()

# Pick accurate laps only
accurate_laps = laps.pick_accurate()
```

### Qualifying Session Splitting

```python
# Split qualifying into Q1, Q2, Q3
q1, q2, q3 = laps.split_qualifying_sessions()
```

### Iterating Over Laps

```python
# Iterate over all laps
for idx, lap in laps.iterlaps():
    print(lap['Driver'], lap['LapTime'])

# Iterate only over laps with specific data
for idx, lap in laps.iterlaps(require=['LapTime', 'Sector1Time']):
    print(lap['Driver'], lap['LapTime'])
```

## Working with Telemetry

### Getting Telemetry from Laps

```python
# Get telemetry for single lap
lap = laps.pick_fastest()
telemetry = lap.get_telemetry()

# Get car data (Speed, RPM, Throttle, Brake, nGear, DRS)
car_data = lap.get_car_data()

# Get position data (X, Y, Z, Status)
pos_data = lap.get_pos_data()

# Get telemetry for multiple laps (single driver only!)
ver_laps = laps.pick_drivers('VER')
ver_telemetry = ver_laps.get_telemetry()
```

### Telemetry Channels

**Car Data:**
- `Speed` - Car speed [km/h]
- `RPM` - Engine RPM
- `nGear` - Gear number (int)
- `Throttle` - Throttle position [0-100%]
- `Brake` - Brake applied (boolean)
- `DRS` - DRS status (int)

**Position Data:**
- `X` - X position [1/10 m]
- `Y` - Y position [1/10 m]
- `Z` - Z position [1/10 m]
- `Status` - OnTrack/OffTrack

**Common Columns:**
- `Time` - Timedelta from start
- `SessionTime` - Timedelta from session start
- `Date` - Full datetime
- `Source` - 'car', 'pos', or 'interpolated'

### Adding Computed Channels

```python
# Add distance channels
telemetry = telemetry.add_differential_distance()  # Distance between samples
telemetry = telemetry.add_distance()              # Cumulative distance
telemetry = telemetry.add_relative_distance()     # Relative distance [0.0-1.0]

# Add track status
telemetry = telemetry.add_track_status()

# Add driver ahead information
telemetry = telemetry.add_driver_ahead()  # Adds 'DriverAhead' and 'DistanceToDriverAhead'
```

### Slicing Telemetry

```python
# Slice by lap
lap = laps.pick_fastest()
telemetry = session.car_data['VER'].slice_by_lap(lap)

# Slice by time
telemetry = telemetry.slice_by_time(
    start_time=pd.Timedelta(seconds=100),
    end_time=pd.Timedelta(seconds=200)
)

# Slice by mask
mask = telemetry['Speed'] > 300
high_speed = telemetry.slice_by_mask(mask)
```

### Merging and Resampling

```python
# Merge different telemetry channels
merged = car_data.merge_channels(pos_data)

# Resample to specific frequency
resampled = telemetry.resample_channels(rule='10ms')
```

## Session Results

### Accessing Results

```python
session.load()
results = session.results

# Results DataFrame columns:
# ['DriverNumber', 'BroadcastName', 'Abbreviation', 'DriverId', 'TeamName',
#  'TeamColor', 'TeamId', 'FirstName', 'LastName', 'FullName',
#  'HeadshotUrl', 'CountryCode', 'Position', 'ClassifiedPosition',
#  'GridPosition', 'Q1', 'Q2', 'Q3', 'Time', 'Status', 'Points', 'Laps']
```

### Working with Results

```python
# Get top 10 results
top_10 = results.iloc[0:10]

# Get specific driver
ver_result = results[results['Abbreviation'] == 'VER']
ver_result = session.get_driver('VER')

# Access driver properties
print(ver_result['FullName'])
print(ver_result['TeamName'])
print(ver_result['Position'])
print(ver_result['Q3'])  # Qualifying sessions only
```

## Weather Data

```python
# Get weather data for session
session.load(weather=True)
weather = session.weather_data

# Weather data columns:
# ['Time', 'AirTemp', 'Humidity', 'Pressure', 'Rainfall',
#  'TrackTemp', 'WindDirection', 'WindSpeed']

# Get weather for specific lap
lap = laps.pick_fastest()
lap_weather = lap.get_weather_data()

# Get weather for all laps
laps_weather = laps.get_weather_data()
```

## Circuit Information

```python
# Get circuit info
circuit_info = session.get_circuit_info()

# Access circuit data
corners = circuit_info.corners              # DataFrame with corner locations
marshal_lights = circuit_info.marshal_lights    # DataFrame with marshal light locations
marshal_sectors = circuit_info.marshal_sectors  # DataFrame with marshal sector locations
rotation = circuit_info.rotation            # Circuit rotation angle

# Corner data columns: X, Y, Number, Letter, Angle, Distance
```

## Track and Session Status

```python
session.load()

# Track status (flags, safety car, etc.)
track_status = session.track_status
# Columns: ['Time', 'Status', 'Message']

# Session status (started, finished, etc.)
session_status = session.session_status
# Columns: ['Time', 'Status']

# Race control messages
messages = session.race_control_messages
# Columns: ['Time', 'Category', 'Message', 'Status', 'Flag', 'Scope', 'Sector', 'RacingNumber']
```

## Events Module

```python
from fastf1.events import EventSchedule, Event

# Get schedule
schedule = fastf1.get_event_schedule(2021)

# Event data columns:
# ['RoundNumber', 'Country', 'Location', 'OfficialEventName', 'EventDate',
#  'EventName', 'EventFormat', 'Session1', 'Session1Date', 'Session1DateUtc',
#  'Session2', 'Session2Date', 'Session2DateUtc', 'Session3', 'Session3Date',
#  'Session3DateUtc', 'Session4', 'Session4Date', 'Session4DateUtc',
#  'Session5', 'Session5Date', 'Session5DateUtc', 'F1ApiSupport']

# Get sessions from event
event = fastf1.get_event(2021, 7)
race_session = event.get_race()
quali_session = event.get_qualifying()
practice_session = event.get_practice(1)  # 1, 2, or 3
sprint_session = event.get_sprint()
```

## Plotting Module

```python
from fastf1 import plotting
import matplotlib.pyplot as plt

# Setup FastF1 plotting theme
plotting.setup_mpl(color_scheme='fastf1')

# Get team colors
team_color = plotting.get_team_color('Red Bull', session=session)
driver_color = plotting.get_driver_color('VER', session=session)

# Team colors are hex strings like '#0600EF'
```

## Complete Example: Lap Time Analysis

```python
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt

# Enable cache
fastf1.Cache.enable_cache('cache')

# Setup plotting
fastf1.plotting.setup_mpl(color_scheme='fastf1')

# Load session
session = fastf1.get_session(2024, 'Monaco', 'Q')
session.load()

# Get fastest laps for two drivers
ver_lap = session.laps.pick_drivers('VER').pick_fastest()
lec_lap = session.laps.pick_drivers('LEC').pick_fastest()

# Get telemetry
ver_tel = ver_lap.get_car_data().add_distance()
lec_tel = lec_lap.get_car_data().add_distance()

# Plot speed comparison
fig, ax = plt.subplots()
ax.plot(ver_tel['Distance'], ver_tel['Speed'], label='VER')
ax.plot(lec_tel['Distance'], lec_tel['Speed'], label='LEC')
ax.set_xlabel('Distance (m)')
ax.set_ylabel('Speed (km/h)')
ax.legend()
plt.show()
```

## Complete Example: Race Analysis

```python
import fastf1
import pandas as pd

fastf1.Cache.enable_cache('cache')

# Load race session
session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

# Get all laps
laps = session.laps

# Get lap times by driver
ver_laptimes = laps.pick_drivers('VER')[['LapNumber', 'LapTime', 'Compound']]

# Get pit stops
pit_stops = laps[laps['PitInTime'].notna()][['Driver', 'LapNumber', 'PitInTime']]

# Get fastest lap of race
fastest = laps.pick_fastest()
print(f"Fastest lap: {fastest['Driver']} - {fastest['LapTime']}")

# Get finishing positions
results = session.results
print(results[['Position', 'Abbreviation', 'TeamName', 'Status']])
```

## Important Data Types

- **Times**: `pandas.Timedelta` objects
- **Dates**: `pandas.Timestamp` objects
- **Driver Numbers**: Strings (e.g., '1', '44')
- **Compounds**: Strings ('SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET')
- **Team Names**: Strings (short version without sponsors)

## Common Patterns

### 1. Get fastest lap telemetry for a driver

```python
session = fastf1.get_session(2024, 1, 'Q')
session.load()

fastest_lap = session.laps.pick_drivers('VER').pick_fastest()
telemetry = fastest_lap.get_car_data().add_distance()
```

### 2. Compare qualifying times

```python
session = fastf1.get_session(2024, 1, 'Q')
session.load()

results = session.results[['Abbreviation', 'Q1', 'Q2', 'Q3']].head(10)
```

### 3. Get race pace by stint

```python
session = fastf1.get_session(2024, 1, 'R')
session.load()

ver_laps = session.laps.pick_drivers('VER').pick_wo_box()
by_stint = ver_laps.groupby('Stint')['LapTime'].mean()
```

## Data Availability

- **Full telemetry and timing**: 2018 onwards
- **Schedule and results**: 1950 onwards (via Ergast)
- **Live timing**: Can be recorded during sessions

## Notes

- Always call `session.load()` before accessing data
- Use caching to improve performance
- Driver numbers are strings, not integers
- Telemetry operations on multiple laps require single driver only
- Integration error accumulates - use distance calculations on short segments only
