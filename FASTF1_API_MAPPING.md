# FastF1 Python Library Comprehensive Guide

## Overview

FastF1 is a Python package that provides access to Formula 1 timing data, telemetry, and detailed session information. Unlike ESPN's REST API, FastF1 is a Python library that fetches data from F1's official live timing service and processes it into easy-to-use pandas DataFrames.

## Installation

```bash
pip install fastf1
```

## Core Concepts

### Data Sources
- **Primary**: F1 Live Timing API (official F1 data)
- **Historical**: Ergast API (fallback for older seasons, pre-2018)
- **Backends**: `'fastf1'` (default), `'f1timing'`, `'ergast'`

### Main Objects
1. **Session** - Represents a race weekend session (Practice, Qualifying, Race)
2. **Laps** - Collection of lap data (DataFrame-like)
3. **Lap** - Single lap data
4. **Telemetry** - Detailed sensor/car data

## Getting Started

### Basic Session Loading

```python
import fastf1

# Method 1: By round number
session = fastf1.get_session(2021, 1, 'FP2')  # Year, Round, Session

# Method 2: By Grand Prix name (fuzzy matching supported)
session = fastf1.get_session(2021, 'Monaco', 'Qualifying')
session = fastf1.get_session(2021, 'Silverstone', 'Q')

# Method 3: By session number
session = fastf1.get_session(2021, 5, 3)  # 3rd session of 5th GP

# Load the data
session.load()  # This fetches and processes all data
```

### Session Identifiers

**Practice Sessions:**
- `'FP1'`, `'FP2'`, `'FP3'` or `'Practice 1'`, `'Practice 2'`, `'Practice 3'`
- Session numbers: `1`, `2`, `3`

**Qualifying:**
- `'Q'`, `'Qualifying'`
- Session number: `4`

**Sprint:**
- `'S'`, `'Sprint'`, `'Sprint Qualifying'`
- Session number: `5` (varies by year)

**Race:**
- `'R'`, `'Race'`
- Session number: `5` or `6` (depending on format)

## Data Structures

### Session Object

```python
session = fastf1.get_session(2021, 'French Grand Prix', 'Q')
session.load()

# Session properties
session.name                # 'Qualifying'
session.date                # Date of session
session.session_start_time  # timedelta from zero point
session.t0_date             # Absolute timestamp of session start

# Associated event
session.event               # Pandas Series with event info
session.event['EventName']  # 'French Grand Prix'
session.event['EventDate']  # Event date
session.event['Country']    # 'France'
session.event['Location']   # 'Le Castellet'

# Session data
session.results             # DataFrame: Driver results/standings
session.laps                # Laps object: All laps in session
session.drivers             # List of driver numbers
session.weather             # DataFrame: Weather data
```

### Results DataFrame

```python
# Access results
results = session.results

# Available columns:
# - Position, ClassifiedPosition
# - GridPosition, Q1, Q2, Q3 (qualifying)
# - Status, Points
# - DriverNumber, Abbreviation, TeamName, TeamColor
# - FirstName, LastName, FullName
# - HeadshotUrl, CountryCode
# - Time (race finish time)
```

Example:
```python
# Top 10 Q3 times
top10 = session.results.iloc[0:10].loc[:, ['Abbreviation', 'Q3']]
print(top10)
```

### Laps Object (Laps DataFrame)

The `session.laps` object is a special DataFrame containing all lap data.

```python
laps = session.laps

# Available columns (comprehensive):
# Timing:
# - Time: Lap completion time (timedelta from session start)
# - LapTime: Duration of the lap
# - LapNumber: Lap number
# - LapStartTime, LapStartDate
# - Sector1Time, Sector2Time, Sector3Time
# - Sector1SessionTime, Sector2SessionTime, Sector3SessionTime

# Driver/Team:
# - Driver: Driver abbreviation (e.g., 'VER')
# - DriverNumber: Car number
# - Team: Team name

# Performance:
# - SpeedI1, SpeedI2: Intermediate speed trap speeds
# - SpeedFL: Finish line speed
# - SpeedST: Speed trap speed
# - IsPersonalBest: Boolean

# Track/Strategy:
# - Compound: Tire compound (SOFT, MEDIUM, HARD, etc.)
# - TyreLife: Age of tires in laps
# - FreshTyre: Boolean
# - Stint: Stint number
# - IsAccurate: Data accuracy flag

# Status:
# - TrackStatus: Track condition codes
# - Deleted: Lap deleted flag
# - DeletedReason
# - PitInTime, PitOutTime
# - Position: Position at lap completion
```

### Selecting Laps

```python
# Pick fastest lap overall
fastest = session.laps.pick_fastest()

# Pick fastest lap by driver
ver_fastest = session.laps.pick_driver('VER').pick_fastest()

# Filter by driver
verstappen_laps = session.laps.pick_driver('VER')
verstappen_laps = session.laps.pick_driver(33)  # By number

# Filter by team
redbull_laps = session.laps.pick_team('Red Bull Racing')

# Filter by tire compound
soft_laps = session.laps.pick_compound('SOFT')

# Filter by track status
green_flag_laps = session.laps.pick_track_status('1')  # Green flag

# Chaining filters
ver_soft_fastest = (session.laps
                    .pick_driver('VER')
                    .pick_compound('SOFT')
                    .pick_fastest())

# Multiple drivers
drivers_laps = session.laps.pick_drivers(['VER', 'HAM', 'LEC'])

# Quick laps only (outliers removed)
quick_laps = session.laps.pick_quicklaps()

# Accurate laps only
accurate_laps = session.laps.pick_accurate()
```

### Single Lap Object

```python
lap = session.laps.pick_fastest()

# Lap attributes
lap['LapTime']              # timedelta
lap['Driver']               # 'VER'
lap['Sector1Time']          # timedelta
lap['SpeedI1']              # float (km/h)
lap['Compound']             # 'SOFT'
lap['TyreLife']             # int
```

## Telemetry Data

FastF1's most powerful feature is detailed telemetry access.

### Car Data (Telemetry)

```python
lap = session.laps.pick_fastest()

# Get car telemetry
car_data = lap.get_car_data()

# Available channels:
# - Speed: Speed in km/h
# - RPM: Engine RPM
# - nGear: Gear number (1-8)
# - Throttle: Throttle position (0-100%)
# - Brake: Brake pressure (boolean or 0-100)
# - DRS: DRS status (0-14, various states)
# - Source: Data source indicator

# Time columns:
# - Date: Absolute timestamp
# - Time: timedelta from lap start
# - SessionTime: timedelta from session start

# Usage
print(car_data[['Speed', 'nGear', 'Throttle', 'Brake']])

# With padding (data before/after lap)
car_data = lap.get_car_data(pad=1, pad_side='both')
```

### Position Data

```python
# Get position/GPS data
pos_data = lap.get_pos_data()

# Available channels:
# - X, Y, Z: Track position coordinates
# - Status: Status code
# - Source: Data source

# Time columns (same as car data)
# - Date, Time, SessionTime
```

### Combined Telemetry

```python
# Get merged car + position data
telemetry = lap.get_telemetry()

# Includes all car_data + pos_data channels plus computed:
# - Distance: Cumulative distance traveled
# - RelativeDistance: Distance relative to lap distance
# - DifferentialDistance: Distance between samples
# - DriverAhead: Driver number ahead
# - DistanceToDriverAhead: Gap in meters

# Custom resampling frequency
telemetry = lap.get_telemetry(frequency=10)  # 10 Hz
telemetry = lap.get_telemetry(frequency='original')  # No resampling
```

### Telemetry for Multiple Laps

```python
# Get telemetry for multiple laps (same driver only)
laps = session.laps.pick_driver('VER')
telemetry = laps.get_telemetry()

# Or get car data for multiple laps
car_data = laps.get_car_data()
```

### Working with Telemetry

```python
# Telemetry is a DataFrame with special methods

# Add computed channels
tel = car_data.add_distance()  # Add distance channel
tel = car_data.add_relative_distance()  # Add relative distance
tel = car_data.add_driver_ahead()  # Add driver ahead info

# Merge channels from another telemetry object
merged = car_data.merge_channels(pos_data)
merged = car_data.merge_channels(pos_data, frequency=10)

# Slice by time
sliced = telemetry.slice_by_time(
    start_time=pd.Timedelta(seconds=10),
    end_time=pd.Timedelta(seconds=30)
)

# Slice by lap
tel_for_lap = telemetry.slice_by_lap(lap)
tel_with_padding = telemetry.slice_by_lap(
    lap,
    pad=5,  # 5 samples padding
    pad_side='both',
    interpolate_edges=True
)
```

## Advanced Features

### Weather Data

```python
session.load(weather=True)

weather = session.weather_data

# Available columns:
# - Time, SessionTime
# - AirTemp: Air temperature (°C)
# - Humidity: Relative humidity (%)
# - Pressure: Air pressure (mbar)
# - Rainfall: Boolean
# - TrackTemp: Track temperature (°C)
# - WindDirection: Wind direction (degrees)
# - WindSpeed: Wind speed (m/s)
```

### Race Control Messages

```python
session.load(messages=True)

messages = session.race_control_messages

# Available columns:
# - Time, SessionTime
# - Category: Message category
# - Message: Message text
# - Status: Track status
# - Flag: Flag type
# - Scope: Message scope
# - Sector: Affected sector
# - RacingNumber: Affected driver
```

### Selective Loading

```python
# Load only specific data types (faster)
session.load(
    laps=True,           # Load lap data
    telemetry=True,      # Load telemetry
    weather=False,       # Skip weather
    messages=False       # Skip race control messages
)
```

### Event Schedule

```python
# Get entire season schedule
schedule = fastf1.get_event_schedule(2021)

# Returns DataFrame with all events:
# - RoundNumber
# - Country, Location
# - OfficialEventName
# - EventDate, EventName
# - EventFormat (conventional/sprint)
# - Session1-5Date (session times)
# - F1ApiSupport (bool)

# Get single event
event = fastf1.get_event(2021, 'Monaco')
event = fastf1.get_event(2021, 7)  # By round number

# Event properties
print(event['EventName'])
print(event['EventDate'])

# Get sessions from event
fp1 = event.get_session('FP1')
race = event.get_session('R')
```

### Session Status

```python
# Get session status data
session.load(laps=True)

status_data = session.session_status

# Track status codes:
# '1' - Green/Track Clear
# '2' - Yellow Flag
# '3' - Reserved
# '4' - Safety Car
# '5' - Red Flag
# '6' - VSC (Virtual Safety Car)
# '7' - VSC Ending
```

## Data Quality and Accuracy

### Accuracy Flags

```python
# Check if lap data is accurate
lap['IsAccurate']  # Boolean

# Filter for accurate laps only
accurate_laps = session.laps.pick_accurate()
```

### Deleted Laps

```python
# Check if lap was deleted
lap['Deleted']  # Boolean
lap['DeletedReason']  # String

# Remove deleted laps
valid_laps = session.laps[session.laps['Deleted'] == False]
```

### Quick Laps

```python
# Get quick laps (removes outliers)
quick_laps = session.laps.pick_quicklaps()

# This removes:
# - Laps with pit in/out
# - Laps under safety car
# - Significantly slow laps
```

## Time Handling

FastF1 uses multiple time representations:

### Time Types

1. **SessionTime** - timedelta from session start (t0)
2. **Time** - timedelta for lap completion time
3. **Date** - Absolute pandas.Timestamp
4. **LapStartTime** - timedelta when lap started
5. **LapTime** - Duration of the lap

### Working with Time

```python
# Session zero point
session.t0_date  # Absolute timestamp

# Convert between time types
lap_completion_time = lap['Time']  # timedelta
absolute_time = session.t0_date + lap_completion_time

# Session start offset
start_offset = session.session_start_time
```

## Plotting Support

FastF1 includes plotting utilities:

```python
import fastf1.plotting

# Setup matplotlib for FastF1
fastf1.plotting.setup_mpl(
    mpl_timedelta_support=True,
    color_scheme='fastf1'  # or 'fastf1-dark'
)

# Get team colors
team_color = fastf1.plotting.team_colors['Red Bull Racing']
driver_color = fastf1.plotting.driver_color('VER')
```

## Caching

FastF1 supports caching to avoid re-downloading data:

```python
import fastf1

# Enable cache
fastf1.Cache.enable_cache('path/to/cache/folder')

# Disable cache
fastf1.Cache.disable_cache()

# Clear cache
fastf1.Cache.clear_cache('path/to/cache/folder')
```

## Error Handling and Limitations

### Data Availability

```python
# Check if F1 API is supported for this session
session.f1_api_support  # Boolean

# For older sessions (pre-2018), Ergast is used automatically
# Limited data available: no telemetry, basic lap times only
```

### Common Issues

1. **No telemetry for old seasons** - Only available from 2018 onwards
2. **Live timing during race** - May be incomplete/unstable
3. **Network issues** - Use caching to minimize API calls
4. **Missing data** - Some sessions may have incomplete data

## Best Practices

### 1. Use Caching

```python
fastf1.Cache.enable_cache('~/f1_cache')
```

### 2. Load Only What You Need

```python
# Don't load unnecessary data
session.load(telemetry=False, weather=False, messages=False)
```

### 3. Filter Early

```python
# Filter laps before getting telemetry
quick_laps = session.laps.pick_quicklaps()
ver_laps = quick_laps.pick_driver('VER')
telemetry = ver_laps.get_telemetry()
```

### 4. Use pick_ Methods

```python
# More efficient than manual filtering
fastest = session.laps.pick_fastest()
# vs
# fastest = session.laps.loc[session.laps['LapTime'].idxmin()]
```

### 5. Handle Missing Data

```python
try:
    session.load()
except Exception as e:
    print(f"Failed to load session: {e}")
    # Fallback to ergast or handle gracefully
```

## Data Structure Summary

```
FastF1 Data Hierarchy:
├── Event (Race Weekend)
│   ├── Event Metadata (country, location, dates)
│   └── Sessions
│       ├── Session Info (name, date, type)
│       ├── Results (Driver standings for session)
│       ├── Laps (All lap data)
│       │   ├── Lap Timing (lap time, sector times)
│       │   ├── Driver Info
│       │   ├── Tire Data
│       │   ├── Track Status
│       │   └── Telemetry Access
│       │       ├── Car Data (speed, throttle, brake, etc.)
│       │       ├── Position Data (X, Y, Z coordinates)
│       │       └── Computed Data (distance, gaps)
│       ├── Weather Data
│       └── Race Control Messages
```

## Comparison with Other APIs

**FastF1 Excels At:**
- Detailed telemetry data (speed, throttle, brake, gear, etc.)
- Lap-by-lap timing and sector data
- Position/GPS coordinates
- Weather and track conditions
- Race control messages
- Data analysis and visualization

**FastF1 Limitations:**
- Python only (not a REST API)
- Requires data processing/loading time
- No real-time push notifications
- Historical data limited to F1 API availability (2018+)
- No driver career statistics
- No constructor/team historical data

**Use FastF1 When You Need:**
- Detailed technical analysis
- Telemetry visualization
- Lap time comparisons
- Track position analysis
- Scientific/research applications
- Data science projects

**Use ESPN API When You Need:**
- Simple REST API access
- Driver/constructor standings
- Historical championship data
- Multi-language support
- Basic race results
- Integration with web/mobile apps
