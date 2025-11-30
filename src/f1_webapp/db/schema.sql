-- F1 Data Schema

-- Drivers table
CREATE TABLE IF NOT EXISTS drivers (
    id TEXT PRIMARY KEY,  -- ESPN numeric driver ID
    abbreviation TEXT NOT NULL,  -- Driver abbreviation (e.g., "VER", "HAM")
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    number TEXT,
    nationality TEXT,
    date_of_birth TEXT,
    headshot_url TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams/Constructors table
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT,
    logo_url TEXT,
    color TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seasons table
CREATE TABLE IF NOT EXISTS seasons (
    year INTEGER PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Races table
CREATE TABLE IF NOT EXISTS races (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    official_event_name TEXT,
    country TEXT,
    location TEXT,
    circuit_name TEXT,
    event_date TEXT,
    event_format TEXT DEFAULT 'conventional',
    has_sprint BOOLEAN DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, round_number),
    FOREIGN KEY (year) REFERENCES seasons(year)
);

-- Driver Standings table
CREATE TABLE IF NOT EXISTS driver_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    driver_id TEXT NOT NULL,
    team_id TEXT,
    position INTEGER NOT NULL,
    points REAL NOT NULL,
    wins INTEGER DEFAULT 0,
    poles INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    fastest_laps INTEGER DEFAULT 0,
    dnfs INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, driver_id),
    FOREIGN KEY (year) REFERENCES seasons(year),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Constructor Standings table
CREATE TABLE IF NOT EXISTS constructor_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    points REAL NOT NULL,
    wins INTEGER DEFAULT 0,
    poles INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    fastest_laps INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, team_id),
    FOREIGN KEY (year) REFERENCES seasons(year),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Race Results table (individual race performance)
CREATE TABLE IF NOT EXISTS race_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL,
    driver_id TEXT NOT NULL,
    team_id TEXT,
    position INTEGER,
    grid_position INTEGER,
    points REAL DEFAULT 0,
    laps_completed INTEGER,
    status TEXT,
    fastest_lap BOOLEAN DEFAULT 0,
    time TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(race_id, driver_id),
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Qualifying Results table
CREATE TABLE IF NOT EXISTS qualifying_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL,
    driver_id TEXT NOT NULL,
    team_id TEXT,
    position INTEGER,
    q1_time TEXT,
    q2_time TEXT,
    q3_time TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(race_id, driver_id),
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Sprint Results table
CREATE TABLE IF NOT EXISTS sprint_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL,
    driver_id TEXT NOT NULL,
    team_id TEXT,
    position INTEGER,
    grid_position INTEGER,
    points REAL DEFAULT 0,
    laps_completed INTEGER,
    status TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(race_id, driver_id),
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Driver Race Points (for easy race-by-race lookups)
CREATE TABLE IF NOT EXISTS driver_race_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    driver_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    race_points REAL DEFAULT 0,
    sprint_points REAL DEFAULT 0,
    total_points REAL DEFAULT 0,
    cumulative_points REAL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, driver_id, round_number),
    FOREIGN KEY (year) REFERENCES seasons(year),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

-- Constructor Race Points (for easy race-by-race lookups)
CREATE TABLE IF NOT EXISTS constructor_race_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    race_points REAL DEFAULT 0,
    sprint_points REAL DEFAULT 0,
    total_points REAL DEFAULT 0,
    cumulative_points REAL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, team_id, round_number),
    FOREIGN KEY (year) REFERENCES seasons(year),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_driver_standings_year ON driver_standings(year);
CREATE INDEX IF NOT EXISTS idx_constructor_standings_year ON constructor_standings(year);
CREATE INDEX IF NOT EXISTS idx_races_year ON races(year);
CREATE INDEX IF NOT EXISTS idx_race_results_race_id ON race_results(race_id);
CREATE INDEX IF NOT EXISTS idx_qualifying_results_race_id ON qualifying_results(race_id);
CREATE INDEX IF NOT EXISTS idx_sprint_results_race_id ON sprint_results(race_id);
CREATE INDEX IF NOT EXISTS idx_driver_race_points_year ON driver_race_points(year);
CREATE INDEX IF NOT EXISTS idx_constructor_race_points_year ON constructor_race_points(year);
