"""FastAPI application combining ESPN and FastF1 APIs."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Any
import logging
import pandas as pd
import numpy as np
import json

from ..espn.client import ESPNClient
from ..fastf1.client import FastF1Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NaNEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts NaN/inf to None."""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
        return super().default(obj)


def json_safe(data: Any) -> Any:
    """Recursively convert NaN/inf values to None in nested structures."""
    if isinstance(data, dict):
        return {k: json_safe(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [json_safe(item) for item in data]
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return None
        return data
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif pd.isna(data):
        return None
    return data


def dataframe_to_json_safe(df):
    """Convert DataFrame to JSON-safe dictionary, handling all pandas special types."""
    df = df.copy()

    # Convert all timedelta columns to strings
    for col in df.columns:
        if pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else None)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)

    # Replace all NaN, inf, -inf with None
    df = df.replace([np.inf, -np.inf], None)
    df = df.where(pd.notna(df), None)

    return df.to_dict(orient="records")


def create_app(cache_dir: str = "./f1_cache") -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        cache_dir: Directory for FastF1 cache

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="F1 Data API",
        description="Comprehensive F1 data API combining ESPN and FastF1",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize clients
    espn = ESPNClient()
    ff1 = FastF1Client(cache_dir=cache_dir)

    # ESPN Endpoints

    @app.get("/")
    def root():
        """Root endpoint."""
        return {
            "name": "F1 Data API",
            "version": "0.1.0",
            "endpoints": {
                "espn": {
                    "standings": "/espn/standings/{year}",
                    "driver": "/espn/drivers/{driver_id}",
                    "events": "/espn/events?season={year}&limit={limit}",
                },
                "fastf1": {
                    "session": "/fastf1/session/{year}/{gp}/{session_type}",
                    "fastest_lap": "/fastf1/fastest-lap/{year}/{gp}/{session_type}",
                    "telemetry": "/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}",
                },
            },
        }

    @app.get("/espn/standings/{year}")
    def get_standings(year: int, type: str = "driver"):
        """Get championship standings.

        Args:
            year: Season year
            type: 'driver' or 'constructor'
        """
        try:
            if type == "driver":
                data = espn.get_driver_standings(year)
            elif type == "constructor":
                data = espn.get_constructor_standings(year)
            else:
                raise HTTPException(400, "Type must be 'driver' or 'constructor'")

            return data
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            raise HTTPException(500, str(e))

    @app.get("/espn/drivers/{driver_id}")
    def get_driver(driver_id: str):
        """Get driver profile.

        Args:
            driver_id: ESPN driver ID (e.g., '4665')
        """
        try:
            return espn.get_driver(driver_id)
        except Exception as e:
            logger.error(f"Error fetching driver: {e}")
            raise HTTPException(404, f"Driver {driver_id} not found")

    @app.get("/espn/events")
    def get_events(season: Optional[int] = None, limit: int = 100):
        """Get F1 events.

        Args:
            season: Optional season year to get all events for that season
            limit: Maximum number of events to return (default: 100)
        """
        try:
            return espn.get_events(season=season, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            raise HTTPException(500, str(e))

    @app.get("/espn/event/{event_id}")
    def get_event(event_id: str):
        """Get event details.

        Args:
            event_id: ESPN event ID
        """
        try:
            return espn.get_event(event_id)
        except Exception as e:
            logger.error(f"Error fetching event: {e}")
            raise HTTPException(404, f"Event {event_id} not found")

    # FastF1 Endpoints

    @app.get("/fastf1/schedule/{year}")
    def get_schedule(year: int):
        """Get season schedule.

        Args:
            year: Championship year
        """
        try:
            schedule = ff1.get_event_schedule(year)
            return dataframe_to_json_safe(schedule)
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/session/{year}/{gp}/{session_type}")
    def get_session_info(year: int, gp: str, session_type: str):
        """Get session information and results.

        Args:
            year: Championship year
            gp: Grand Prix name or round number
            session_type: 'FP1', 'FP2', 'FP3', 'Q', 'S', 'R'
        """
        try:
            session = ff1.load_session(
                year, gp, session_type,
                telemetry=False,  # Don't load heavy telemetry
                weather=False,
                messages=False
            )

            data = {
                "name": session.name,
                "date": session.date.isoformat(),
                "event": {
                    "EventName": session.event["EventName"],
                    "EventDate": session.event["EventDate"].isoformat(),
                    "Location": session.event["Location"],
                    "Country": session.event["Country"],
                    "RoundNumber": int(session.event["RoundNumber"]),
                },
                "results": dataframe_to_json_safe(session.results),
            }
            return json_safe(data)
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/fastest-lap/{year}/{gp}/{session_type}")
    def get_fastest_lap_info(
        year: int,
        gp: str,
        session_type: str,
        driver: Optional[str] = None
    ):
        """Get fastest lap information.

        Args:
            year: Championship year
            gp: Grand Prix name or round number
            session_type: Session type
            driver: Optional driver abbreviation filter
        """
        try:
            session = ff1.load_session(year, gp, session_type, telemetry=False)
            fastest = ff1.get_fastest_lap(session, driver)

            return {
                "driver": fastest["Driver"],
                "lap_time": str(fastest["LapTime"]),
                "lap_number": int(fastest["LapNumber"]),
                "compound": fastest["Compound"],
                "team": fastest["Team"],
            }
        except Exception as e:
            logger.error(f"Error getting fastest lap: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}")
    def get_driver_telemetry(
        year: int,
        gp: str,
        session_type: str,
        driver: str,
        lap_type: str = "fastest"
    ):
        """Get driver telemetry for a lap.

        Args:
            year: Championship year
            gp: Grand Prix name
            session_type: Session type
            driver: Driver abbreviation (e.g., 'VER')
            lap_type: 'fastest' or lap number
        """
        try:
            session = ff1.load_session(year, gp, session_type)

            if lap_type == "fastest":
                lap = ff1.get_fastest_lap(session, driver)
            else:
                laps = ff1.get_driver_laps(session, driver)
                lap = laps[laps["LapNumber"] == int(lap_type)].iloc[0]

            telemetry = ff1.get_lap_telemetry(lap)

            return json_safe({
                "driver": driver,
                "lap_number": int(lap["LapNumber"]),
                "lap_time": str(lap["LapTime"]),
                "telemetry": {
                    "distance": telemetry["Distance"].tolist(),
                    "speed": telemetry["Speed"].tolist(),
                    "throttle": telemetry["Throttle"].tolist(),
                    "brake": telemetry["Brake"].tolist(),
                    "gear": telemetry["nGear"].tolist(),
                },
            })
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/compare/{year}/{gp}/{session_type}")
    def compare_drivers(
        year: int,
        gp: str,
        session_type: str,
        driver1: str,
        driver2: str
    ):
        """Compare two drivers' fastest laps.

        Args:
            year: Championship year
            gp: Grand Prix name
            session_type: Session type
            driver1: First driver abbreviation
            driver2: Second driver abbreviation
        """
        try:
            session = ff1.load_session(year, gp, session_type)

            lap1 = ff1.get_fastest_lap(session, driver1)
            lap2 = ff1.get_fastest_lap(session, driver2)

            comparison = ff1.compare_laps(lap1, lap2)

            return json_safe({
                "driver1": {
                    "name": comparison["lap1"]["driver"],
                    "time": str(comparison["lap1"]["time"]),
                    "telemetry": {
                        "distance": comparison["lap1"]["telemetry"]["Distance"].tolist(),
                        "speed": comparison["lap1"]["telemetry"]["Speed"].tolist(),
                        "throttle": comparison["lap1"]["telemetry"]["Throttle"].tolist(),
                    },
                },
                "driver2": {
                    "name": comparison["lap2"]["driver"],
                    "time": str(comparison["lap2"]["time"]),
                    "telemetry": {
                        "distance": comparison["lap2"]["telemetry"]["Distance"].tolist(),
                        "speed": comparison["lap2"]["telemetry"]["Speed"].tolist(),
                        "throttle": comparison["lap2"]["telemetry"]["Throttle"].tolist(),
                    },
                },
            })
        except Exception as e:
            logger.error(f"Error comparing drivers: {e}")
            raise HTTPException(500, str(e))

    @app.get("/standings/complete/{year}")
    def get_complete_standings(year: int):
        """Get complete standings data directly from database in one call.

        Returns driver and constructor standings with race-by-race data
        and metadata about winners, poles, and sprints.
        Fixes performance issues by using database queries instead of 100+ API calls.
        """
        import sqlite3

        try:
            # Connect to database (use absolute path relative to project root)
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all drivers who participated in races this year with their teams
            # Use LAST_VALUE to get the most recent team for each driver
            cursor.execute("""
                WITH driver_latest_team AS (
                    SELECT
                        d.id as driver_id,
                        d.abbreviation,
                        d.display_name as driver_name,
                        t.display_name as team_name,
                        t.logo_url as team_logo,
                        t.color as team_color,
                        r.round_number,
                        ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY r.round_number DESC) as rn
                    FROM session_results sr
                    JOIN drivers d ON sr.driver_id = d.id
                    JOIN teams t ON sr.team_id = t.id
                    JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                    WHERE r.year = ? AND rs.session_type = 'Race'
                )
                SELECT driver_id, abbreviation, driver_name, team_name, team_logo, team_color
                FROM driver_latest_team
                WHERE rn = 1
                ORDER BY driver_name
            """, (year,))

            drivers = {row['driver_id']: dict(row) for row in cursor.fetchall()}

            # Get all races for the year
            cursor.execute("""
                SELECT round_number, event_name, country, event_format,
                       has_sprint
                FROM races
                WHERE year = ?
                ORDER BY round_number
            """, (year,))

            races = [dict(row) for row in cursor.fetchall()]

            # Get race winners
            cursor.execute("""
                SELECT r.round_number, d.abbreviation as winner_abbr
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND rs.session_type = 'Race' AND sr.position = 1
                ORDER BY r.round_number
            """, (year,))

            race_winners = {row['round_number']: row['winner_abbr'] for row in cursor.fetchall()}

            # Get pole positions (from qualifying)
            cursor.execute("""
                SELECT r.round_number, d.abbreviation as pole_abbr
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND rs.session_type = 'Qualifying' AND sr.position = 1
                ORDER BY r.round_number
            """, (year,))

            pole_positions = {row['round_number']: row['pole_abbr'] for row in cursor.fetchall()}

            # Get sprint winners
            cursor.execute("""
                SELECT r.round_number, d.abbreviation as sprint_abbr
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND rs.session_type = 'Sprint Race' AND sr.position = 1
                ORDER BY r.round_number
            """, (year,))

            sprint_winners = {row['round_number']: row['sprint_abbr'] for row in cursor.fetchall()}

            # Build race metadata
            race_metadata = []
            for race in races:
                round_num = race['round_number']
                race_metadata.append({
                    'roundNumber': round_num,
                    'eventName': race['event_name'],
                    'country': race['country'],
                    'hasSprint': bool(race['has_sprint']),
                    'raceWinner': race_winners.get(round_num),
                    'polePosition': pole_positions.get(round_num),
                    'sprintWinner': sprint_winners.get(round_num)
                })

            # Get year-appropriate F1 points system
            def get_points_system(year: int) -> dict:
                """Return the points system for a given year."""
                if year >= 2010:
                    return {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
                elif year >= 2003:
                    return {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                elif year >= 1991:
                    return {1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year >= 1961:
                    return {1: 9, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year == 1960:
                    return {1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                else:  # 1950-1959
                    return {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}

            def has_fastest_lap_point(year: int) -> bool:
                """Check if fastest lap point was awarded in this year."""
                # Fastest lap point: 1950-1959 and 2019+
                return year <= 1959 or year >= 2019

            def get_sprint_points_system(year: int) -> dict:
                """Return sprint points system for a given year (2021+)."""
                if year >= 2021:
                    return {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                return {}

            points_system = get_points_system(year)
            sprint_points_system = get_sprint_points_system(year)
            fastest_lap_enabled = has_fastest_lap_point(year)

            # Get driver race-by-race results with calculated points (Race + Sprint combined)
            cursor.execute("""
                SELECT
                    d.id as driver_id,
                    d.abbreviation,
                    d.display_name as driver_name,
                    t.display_name as team_name,
                    r.round_number,
                    r.event_name,
                    r.country,
                    rs.session_type,
                    sr.position,
                    sr.fastest_lap
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN teams t ON sr.team_id = t.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND rs.session_type IN ('Race', 'Sprint Race')
                ORDER BY d.display_name, r.round_number, rs.session_type
            """, (year,))

            # Organize results by driver and round (combining race + sprint points)
            driver_race_data = {}
            for row in cursor.fetchall():
                driver_id = row['driver_id']
                round_number = row['round_number']

                if driver_id not in driver_race_data:
                    driver_race_data[driver_id] = {
                        'info': drivers.get(driver_id, {}),
                        'races': {}  # Use dict keyed by round_number to combine race+sprint
                    }

                # Initialize round if not exists
                if round_number not in driver_race_data[driver_id]['races']:
                    driver_race_data[driver_id]['races'][round_number] = {
                        'roundNumber': round_number,
                        'eventName': row['event_name'],
                        'country': row['country'],
                        'points': 0
                    }

                position = row['position']
                session_type = row['session_type']

                # Calculate points based on session type
                if session_type == 'Race':
                    race_points = points_system.get(position, 0)
                    # Add 1 point for fastest lap if enabled for this year
                    if fastest_lap_enabled and row['fastest_lap'] and position:
                        # For 2019+: must finish in top 10
                        # For 1950-1959: any finishing position gets the point
                        if year <= 1959 or position <= 10:
                            race_points += 1
                    driver_race_data[driver_id]['races'][round_number]['points'] += race_points
                elif session_type == 'Sprint Race':
                    sprint_points = sprint_points_system.get(position, 0)
                    driver_race_data[driver_id]['races'][round_number]['points'] += sprint_points

            # Convert race dict to list
            for driver_id in driver_race_data:
                driver_race_data[driver_id]['races'] = list(driver_race_data[driver_id]['races'].values())

            # Build driver results with all races filled in
            driver_results = []
            for driver_id, data in driver_race_data.items():
                # Create a map of round_number to race result
                race_map = {race['roundNumber']: race for race in data['races']}

                # Fill in all races in order
                all_race_results = []
                for race_meta in races:
                    round_num = race_meta['round_number']
                    if round_num in race_map:
                        all_race_results.append(race_map[round_num])
                    else:
                        # Driver didn't participate in this race
                        all_race_results.append({
                            'roundNumber': round_num,
                            'eventName': race_meta['event_name'],
                            'country': race_meta['country'],
                            'points': None  # Use None to indicate no participation
                        })

                total_points = sum(race['points'] for race in data['races'])
                driver_results.append({
                    'driverName': data['info']['driver_name'],
                    'driverAbbreviation': data['info']['abbreviation'],
                    'teamName': data['info']['team_name'],
                    'teamLogo': data['info'].get('team_logo'),
                    'teamColor': data['info'].get('team_color'),
                    'totalPoints': total_points,
                    'raceResults': all_race_results
                })

            # Sort by total points descending
            driver_results.sort(key=lambda x: x['totalPoints'], reverse=True)

            # Get constructor race-by-race results (Race + Sprint combined)
            cursor.execute("""
                SELECT
                    t.id as team_id,
                    t.display_name as team_name,
                    r.round_number,
                    r.event_name,
                    r.country,
                    rs.session_type,
                    GROUP_CONCAT(sr.position || ':' || COALESCE(sr.fastest_lap, 0)) as positions
                FROM session_results sr
                JOIN teams t ON sr.team_id = t.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND rs.session_type IN ('Race', 'Sprint Race')
                GROUP BY t.id, r.round_number, rs.session_type
                ORDER BY t.display_name, r.round_number, rs.session_type
            """, (year,))

            # Organize constructor results by round (combining race + sprint)
            constructor_race_data = {}
            for row in cursor.fetchall():
                team_id = row['team_id']
                round_number = row['round_number']
                session_type = row['session_type']

                if team_id not in constructor_race_data:
                    constructor_race_data[team_id] = {
                        'teamName': row['team_name'],
                        'races': {}  # Use dict keyed by round_number
                    }

                # Initialize round if not exists
                if round_number not in constructor_race_data[team_id]['races']:
                    constructor_race_data[team_id]['races'][round_number] = {
                        'roundNumber': round_number,
                        'eventName': row['event_name'],
                        'country': row['country'],
                        'points': 0
                    }

                # Calculate team points from positions
                positions_str = row['positions'] or ''
                team_points = 0
                team_had_fastest = False

                for pos_info in positions_str.split(','):
                    if ':' in pos_info:
                        pos_str, fastest_str = pos_info.split(':')
                        try:
                            pos = int(pos_str)
                            if session_type == 'Race':
                                team_points += points_system.get(pos, 0)
                                if fastest_lap_enabled and fastest_str == '1':
                                    # For 2019+: must finish in top 10
                                    # For 1950-1959: any finishing position gets the point
                                    if year <= 1959 or pos <= 10:
                                        team_had_fastest = True
                            elif session_type == 'Sprint Race':
                                team_points += sprint_points_system.get(pos, 0)
                        except:
                            pass

                if team_had_fastest:
                    team_points += 1

                constructor_race_data[team_id]['races'][round_number]['points'] += team_points

            # Convert race dict to list
            for team_id in constructor_race_data:
                constructor_race_data[team_id]['races'] = list(constructor_race_data[team_id]['races'].values())

            # Get team logos and colors for constructors
            cursor.execute("""
                SELECT id, logo_url, color
                FROM teams
            """)
            team_data = {row['id']: {'logo_url': row['logo_url'], 'color': row['color']} for row in cursor.fetchall()}

            # Build constructor results
            constructor_results = []
            for team_id, data in constructor_race_data.items():
                total_points = sum(race['points'] for race in data['races'])
                team_info = team_data.get(team_id, {})
                constructor_results.append({
                    'teamName': data['teamName'],
                    'teamLogo': team_info.get('logo_url'),
                    'teamColor': team_info.get('color'),
                    'totalPoints': total_points,
                    'raceResults': data['races']
                })

            # Sort by total points descending
            constructor_results.sort(key=lambda x: x['totalPoints'], reverse=True)

            conn.close()

            return json_safe({
                'year': year,
                'raceMetadata': race_metadata,
                'driverResults': driver_results,
                'constructorResults': constructor_results
            })

        except Exception as e:
            logger.error(f"Error getting complete standings: {e}")
            raise HTTPException(500, str(e))

    return app


# For running with uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
