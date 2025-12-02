-- Tables for storing FastF1 session data

-- Table for storing qualifying session results (Q1, Q2, Q3)
CREATE TABLE IF NOT EXISTS fastf1_qualifying_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    session_name TEXT NOT NULL,  -- 'Q1', 'Q2', or 'Q3'
    driver_abbreviation TEXT NOT NULL,
    driver_number INTEGER,
    team TEXT,
    lap_time TEXT,  -- Formatted as MM:SS.mmm
    sector1_time TEXT,
    sector2_time TEXT,
    sector3_time TEXT,
    position INTEGER,  -- Position within that session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, round_number, session_name, driver_abbreviation)
);

-- Table for storing practice session results (FP1, FP2, FP3)
CREATE TABLE IF NOT EXISTS fastf1_practice_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    session_name TEXT NOT NULL,  -- 'FP1', 'FP2', or 'FP3'
    driver_abbreviation TEXT NOT NULL,
    driver_number INTEGER,
    team TEXT,
    lap_time TEXT,  -- Formatted as MM:SS.mmm
    laps_completed INTEGER,
    position INTEGER,  -- Position within that session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, round_number, session_name, driver_abbreviation)
);

-- Table for storing sprint session results
CREATE TABLE IF NOT EXISTS fastf1_sprint_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    driver_abbreviation TEXT NOT NULL,
    driver_number INTEGER,
    team TEXT,
    position INTEGER,
    grid_position INTEGER,
    points REAL,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, round_number, driver_abbreviation)
);

-- Table for storing session weather and race control data
CREATE TABLE IF NOT EXISTS fastf1_session_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    session_type TEXT NOT NULL,  -- 'R', 'Q', 'S', 'FP1', 'FP2', 'FP3'
    data_type TEXT NOT NULL,  -- 'weather', 'race_control', 'lap_times'
    data_json TEXT NOT NULL,  -- JSON blob of the data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, round_number, session_type, data_type)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_fastf1_qualifying ON fastf1_qualifying_results(year, round_number);
CREATE INDEX IF NOT EXISTS idx_fastf1_practice ON fastf1_practice_results(year, round_number);
CREATE INDEX IF NOT EXISTS idx_fastf1_sprint ON fastf1_sprint_results(year, round_number);
CREATE INDEX IF NOT EXISTS idx_fastf1_session_data ON fastf1_session_data(year, round_number, session_type);
