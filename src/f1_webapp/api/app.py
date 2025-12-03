"""FastAPI application combining ESPN and FastF1 APIs."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Any
import logging
import pandas as pd
import numpy as np
import json
import asyncio

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


def format_timedelta(td):
    """Format timedelta to MM:SS.mmm format."""
    if pd.isna(td):
        return None
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds % 1) * 1000)
    return f"{minutes}:{seconds:02d}.{milliseconds:03d}"


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

    @app.get("/fastf1/seasons")
    def get_available_seasons():
        """Get list of available seasons from the database.

        Returns:
            List of years that have race data
        """
        import sqlite3
        try:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT year FROM races ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            conn.close()

            return {"seasons": years}
        except Exception as e:
            logger.error(f"Error fetching seasons: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/schedule/{year}")
    def get_schedule(year: int):
        """Get season schedule with podium finishers.

        Args:
            year: Championship year
        """
        import sqlite3
        try:
            schedule = ff1.get_event_schedule(year)
            schedule_data = dataframe_to_json_safe(schedule)

            # Get podium finishers for each race
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query to get top 3 finishers for each race
            cursor.execute("""
                SELECT
                    r.round_number,
                    d.id as driver_id,
                    d.abbreviation,
                    sr.position
                FROM races r
                JOIN race_sessions rs ON r.espn_event_id = rs.race_espn_event_id
                JOIN session_results sr ON rs.espn_competition_id = sr.session_espn_competition_id
                JOIN drivers d ON sr.driver_id = d.id
                WHERE r.year = ? AND rs.session_type = 'Race' AND sr.position <= 3
                ORDER BY r.round_number, sr.position
            """, (year,))

            # Build podium map with driver IDs and abbreviations
            podium_map = {}
            for row in cursor.fetchall():
                round_num = row['round_number']
                if round_num not in podium_map:
                    podium_map[round_num] = []
                podium_map[round_num].append({
                    'id': row['driver_id'],
                    'abbreviation': row['abbreviation']
                })

            # Get year-appropriate points system for calculating winning constructor
            def get_points_for_position(position: int, year: int) -> int:
                """Get points for a finishing position based on the year's points system."""
                if year >= 2010:
                    points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
                elif year >= 2003:
                    points_system = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                elif year >= 1991:
                    points_system = {1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year >= 1961:
                    points_system = {1: 9, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year == 1960:
                    points_system = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                else:  # 1950-1959
                    points_system = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}
                return points_system.get(position, 0)

            # Query to get winning constructor for each race
            # Need to calculate based on the year's points system
            cursor.execute("""
                SELECT
                    r.round_number,
                    r.year,
                    t.display_name as team_name,
                    t.logo_url,
                    sr.position
                FROM races r
                JOIN race_sessions rs ON r.espn_event_id = rs.race_espn_event_id
                JOIN session_results sr ON rs.espn_competition_id = sr.session_espn_competition_id
                JOIN teams t ON sr.team_id = t.id
                WHERE r.year = ? AND rs.session_type = 'Race' AND sr.position IS NOT NULL
                ORDER BY r.round_number, sr.position
            """, (year,))

            # Team logo mapping - Using official F1 team logos
            TEAM_LOGOS = {
                'McLaren': 'https://media.formula1.com/content/dam/fom-website/teams/2025/mclaren-logo.png',
                'Mercedes': 'https://media.formula1.com/content/dam/fom-website/teams/2025/mercedes-logo.png',
                'Red Bull': 'https://media.formula1.com/content/dam/fom-website/teams/2025/red-bull-racing-logo.png',
                'Ferrari': 'https://media.formula1.com/content/dam/fom-website/teams/2025/ferrari-logo.png',
                'Aston Martin': 'https://media.formula1.com/content/dam/fom-website/teams/2025/aston-martin-logo.png',
                'Alpine': 'https://media.formula1.com/content/dam/fom-website/teams/2025/alpine-logo.png',
                'Williams': 'https://media.formula1.com/content/dam/fom-website/teams/2025/williams-logo.png',
                'Racing Bulls': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/rb-logo.png',
                'Sauber': 'https://media.formula1.com/content/dam/fom-website/teams/2025/kick-sauber-logo.png',
                'Haas': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/haas-f1-team-logo.png'
            }

            # Build winning constructor map
            winning_constructor_map = {}
            current_round = None
            team_points = {}
            team_info = {}  # Store team info including logo

            for row in cursor.fetchall():
                round_num = row['round_number']
                team_name = row['team_name']
                position = row['position']
                race_year = row['year']
                logo_url = row['logo_url'] or TEAM_LOGOS.get(team_name, '')

                # Store team info
                if team_name not in team_info:
                    team_info[team_name] = {'logo': logo_url}

                # If we've moved to a new round, calculate winner for previous round
                if current_round is not None and round_num != current_round:
                    if team_points:
                        winning_team_name = max(team_points.items(), key=lambda x: x[1])[0]
                        winning_constructor_map[current_round] = {
                            'name': winning_team_name,
                            'logo': team_info[winning_team_name]['logo']
                        }
                    team_points = {}

                current_round = round_num

                # Add points for this position
                points = get_points_for_position(position, race_year)
                team_points[team_name] = team_points.get(team_name, 0) + points

            # Don't forget the last round
            if current_round is not None and team_points:
                winning_team_name = max(team_points.items(), key=lambda x: x[1])[0]
                winning_constructor_map[current_round] = {
                    'name': winning_team_name,
                    'logo': team_info[winning_team_name]['logo']
                }

            conn.close()

            # Add podium data and winning constructor to schedule
            for race in schedule_data:
                round_num = race.get('RoundNumber')
                race['Podium'] = podium_map.get(round_num, [])
                race['WinningConstructor'] = winning_constructor_map.get(round_num, None)

            return schedule_data
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/race-results/{year}/{round_number}")
    def get_race_results(year: int, round_number: int):
        """Get complete race results from database.

        Args:
            year: Championship year
            round_number: Race round number
        """
        import sqlite3
        try:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get race info
            cursor.execute("""
                SELECT event_name, country, location, event_date
                FROM races
                WHERE year = ? AND round_number = ?
            """, (year, round_number))

            race_info = cursor.fetchone()
            if not race_info:
                raise HTTPException(404, f"Race not found for {year} round {round_number}")

            # Get race results
            cursor.execute("""
                SELECT
                    sr.position,
                    sr.grid_position,
                    d.id as driver_id,
                    d.display_name as driver_name,
                    d.abbreviation,
                    d.number as driver_number,
                    t.display_name as team_name,
                    t.logo_url as team_logo,
                    t.color as team_color,
                    sr.laps_completed,
                    sr.status,
                    sr.fastest_lap,
                    sr.points
                FROM session_results sr
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                JOIN drivers d ON sr.driver_id = d.id
                LEFT JOIN teams t ON sr.team_id = t.id
                WHERE r.year = ? AND r.round_number = ? AND rs.session_type = 'Race'
                ORDER BY sr.position ASC NULLS LAST
            """, (year, round_number))

            results = [dict(row) for row in cursor.fetchall()]

            # Calculate points if not in database
            def get_points_for_position(position: int, year: int) -> int:
                """Get points for a finishing position based on the year's points system."""
                if year >= 2010:
                    points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
                elif year >= 2003:
                    points_system = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                elif year >= 1991:
                    points_system = {1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year >= 1961:
                    points_system = {1: 9, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                elif year == 1960:
                    points_system = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1}
                else:  # 1950-1959
                    points_system = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}
                return points_system.get(position, 0)

            # Add calculated points if missing
            for result in results:
                if result['points'] is None and result['position']:
                    result['points'] = get_points_for_position(result['position'], year)
                    # Add 1 point for fastest lap if applicable (2019+)
                    if year >= 2019 and result['fastest_lap'] == 1 and result['position'] <= 10:
                        result['points'] += 1

            conn.close()

            return json_safe({
                'race': {
                    'year': year,
                    'roundNumber': round_number,
                    'eventName': race_info['event_name'],
                    'country': race_info['country'],
                    'location': race_info['location'],
                    'date': race_info['event_date']
                },
                'results': results
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching race results: {e}")
            raise HTTPException(500, str(e))

    def load_fastf1_data_background(year: int, round_number: int):
        """Background task to load and cache FastF1 data for a race."""
        try:
            logger.info(f"Background loading FastF1 data for {year} round {round_number}")

            # Load qualifying data
            try:
                session = ff1.load_session(year, round_number, 'Q', telemetry=False, weather=False, messages=False)
                logger.info(f"Loaded qualifying data for {year} round {round_number}")
            except Exception as e:
                logger.warning(f"Could not load qualifying data: {e}")

            # Load race data
            try:
                session = ff1.load_session(year, round_number, 'R', telemetry=False, weather=False, messages=False)
                logger.info(f"Loaded race data for {year} round {round_number}")
            except Exception as e:
                logger.warning(f"Could not load race data: {e}")

            # Load practice data
            for practice in ['FP1', 'FP2', 'FP3']:
                try:
                    session = ff1.load_session(year, round_number, practice, telemetry=False, weather=False, messages=False)
                    logger.info(f"Loaded {practice} data for {year} round {round_number}")
                except Exception as e:
                    logger.warning(f"Could not load {practice} data: {e}")

            # Load sprint data if available
            try:
                session = ff1.load_session(year, round_number, 'S', telemetry=False, weather=False, messages=False)
                logger.info(f"Loaded sprint data for {year} round {round_number}")
            except Exception as e:
                logger.warning(f"Could not load sprint data: {e}")

            logger.info(f"Completed background loading for {year} round {round_number}")
        except Exception as e:
            logger.error(f"Error in background loading: {e}")

    @app.post("/fastf1/preload/{year}/{round_number}")
    async def preload_fastf1_data(year: int, round_number: int, background_tasks: BackgroundTasks):
        """Trigger background loading of FastF1 data for a race.

        Args:
            year: Championship year
            round_number: Race round number
            background_tasks: FastAPI background tasks

        Returns:
            Acknowledgment that loading has started
        """
        background_tasks.add_task(load_fastf1_data_background, year, round_number)
        return {"status": "loading", "message": f"Started loading FastF1 data for {year} round {round_number}"}

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

    @app.get("/fastf1/qualifying/{year}/{round_number}")
    def get_qualifying_results(year: int, round_number: int):
        """Get qualifying results split by Q1, Q2, Q3.

        Args:
            year: Championship year
            round_number: Race round number

        Returns:
            Qualifying results for each session (Q1, Q2, Q3)
        """
        import sqlite3
        try:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if we have cached data in database
            cursor.execute("""
                SELECT COUNT(*) as count FROM fastf1_qualifying_results
                WHERE year = ? AND round_number = ?
            """, (year, round_number))

            has_data = cursor.fetchone()['count'] > 0

            if has_data:
                # Load from database
                logger.info(f"Loading qualifying data from database for {year} round {round_number}")

                def load_session_from_db(session_name):
                    cursor.execute("""
                        SELECT
                            fqr.driver_abbreviation as driver,
                            fqr.driver_number,
                            fqr.team,
                            fqr.lap_time,
                            fqr.sector1_time,
                            fqr.sector2_time,
                            fqr.sector3_time,
                            d.id as driver_id,
                            t.color as team_color
                        FROM fastf1_qualifying_results fqr
                        LEFT JOIN (
                            SELECT abbreviation, id
                            FROM drivers
                            WHERE (abbreviation, active) IN (
                                SELECT abbreviation, MAX(active)
                                FROM drivers
                                GROUP BY abbreviation
                            )
                            GROUP BY abbreviation
                            HAVING id = MAX(id)
                        ) d ON fqr.driver_abbreviation = d.abbreviation
                        LEFT JOIN teams t ON fqr.team = t.display_name
                        WHERE fqr.year = ? AND fqr.round_number = ? AND fqr.session_name = ?
                        ORDER BY fqr.lap_time
                    """, (year, round_number, session_name))
                    return [dict(row) for row in cursor.fetchall()]

                result = {
                    'q1': load_session_from_db('Q1'),
                    'q2': load_session_from_db('Q2'),
                    'q3': load_session_from_db('Q3'),
                }
                conn.close()
                return json_safe(result)

            # Not in database, fetch from FastF1
            logger.info(f"Loading qualifying data from FastF1 for {year} round {round_number}")
            session = ff1.load_session(year, round_number, 'Q', telemetry=False)

            # Split qualifying into Q1, Q2, Q3
            q1, q2, q3 = session.laps.split_qualifying_sessions()

            def format_quali_session(q_session, session_name):
                if q_session is None or q_session.empty:
                    return []

                # Get fastest lap per driver
                results = []
                for driver in q_session['DriverNumber'].unique():
                    driver_laps = q_session[q_session['DriverNumber'] == driver]
                    fastest = driver_laps.loc[driver_laps['LapTime'].idxmin()] if not driver_laps['LapTime'].isna().all() else None

                    if fastest is not None:
                        # Get driver_id and team_color from database
                        cursor.execute("""
                            SELECT d.id as driver_id, t.color as team_color
                            FROM drivers d
                            LEFT JOIN teams t ON t.display_name = ?
                            WHERE d.abbreviation = ?
                            LIMIT 1
                        """, (fastest['Team'], fastest['Driver']))
                        db_info = cursor.fetchone()

                        result = {
                            'driver': fastest['Driver'],
                            'driver_number': int(fastest['DriverNumber']),
                            'team': fastest['Team'],
                            'lap_time': format_timedelta(fastest['LapTime']),
                            'sector1_time': format_timedelta(fastest['Sector1Time']),
                            'sector2_time': format_timedelta(fastest['Sector2Time']),
                            'sector3_time': format_timedelta(fastest['Sector3Time']),
                            'driver_id': db_info['driver_id'] if db_info else None,
                            'team_color': db_info['team_color'] if db_info else None,
                        }
                        results.append(result)

                        # Save to database
                        try:
                            cursor.execute("""
                                INSERT OR REPLACE INTO fastf1_qualifying_results
                                (year, round_number, session_name, driver_abbreviation, driver_number, team,
                                 lap_time, sector1_time, sector2_time, sector3_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (year, round_number, session_name, result['driver'], result['driver_number'],
                                  result['team'], result['lap_time'], result['sector1_time'],
                                  result['sector2_time'], result['sector3_time']))
                        except Exception as e:
                            logger.warning(f"Could not save qualifying result to DB: {e}")

                # Sort by lap time
                results.sort(key=lambda x: x['lap_time'] if x['lap_time'] else 'Z')
                return results

            result = {
                'q1': format_quali_session(q1, 'Q1'),
                'q2': format_quali_session(q2, 'Q2'),
                'q3': format_quali_session(q3, 'Q3'),
            }

            conn.commit()
            conn.close()
            logger.info(f"Saved qualifying data to database for {year} round {round_number}")

            return json_safe(result)
        except Exception as e:
            logger.error(f"Error getting qualifying results: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/practice/{year}/{round_number}")
    def get_practice_results(year: int, round_number: int):
        """Get practice session results for FP1, FP2, FP3.

        Args:
            year: Championship year
            round_number: Race round number

        Returns:
            Practice session results for each session
        """
        import sqlite3
        try:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if we have cached data in database
            cursor.execute("""
                SELECT COUNT(*) as count FROM fastf1_practice_results
                WHERE year = ? AND round_number = ?
            """, (year, round_number))

            has_data = cursor.fetchone()['count'] > 0

            if has_data:
                # Load from database
                logger.info(f"Loading practice data from database for {year} round {round_number}")

                def load_session_from_db(session_name):
                    cursor.execute("""
                        SELECT
                            fpr.driver_abbreviation as driver,
                            fpr.driver_number,
                            fpr.team,
                            fpr.lap_time,
                            fpr.laps_completed,
                            d.id as driver_id,
                            t.color as team_color
                        FROM fastf1_practice_results fpr
                        LEFT JOIN (
                            SELECT abbreviation, id
                            FROM drivers
                            WHERE (abbreviation, active) IN (
                                SELECT abbreviation, MAX(active)
                                FROM drivers
                                GROUP BY abbreviation
                            )
                            GROUP BY abbreviation
                            HAVING id = MAX(id)
                        ) d ON fpr.driver_abbreviation = d.abbreviation
                        LEFT JOIN teams t ON fpr.team = t.display_name
                        WHERE fpr.year = ? AND fpr.round_number = ? AND fpr.session_name = ?
                        ORDER BY fpr.lap_time
                    """, (year, round_number, session_name))
                    return [dict(row) for row in cursor.fetchall()]

                result = {
                    'fp1': load_session_from_db('FP1'),
                    'fp2': load_session_from_db('FP2'),
                    'fp3': load_session_from_db('FP3'),
                }
                conn.close()
                return json_safe(result)

            # Not in database, fetch from FastF1
            logger.info(f"Loading practice data from FastF1 for {year} round {round_number}")
            results = {}

            # Try to load each practice session
            for session_name in ['FP1', 'FP2', 'FP3']:
                try:
                    session = ff1.load_session(year, round_number, session_name, telemetry=False)

                    # Get fastest lap per driver
                    session_results = []
                    for driver in session.laps['DriverNumber'].unique():
                        driver_laps = session.laps[session.laps['DriverNumber'] == driver]
                        fastest = driver_laps.loc[driver_laps['LapTime'].idxmin()] if not driver_laps['LapTime'].isna().all() else None

                        if fastest is not None:
                            # Get driver_id and team_color from database
                            cursor.execute("""
                                SELECT d.id as driver_id, t.color as team_color
                                FROM drivers d
                                LEFT JOIN teams t ON t.display_name = ?
                                WHERE d.abbreviation = ?
                                LIMIT 1
                            """, (fastest['Team'], fastest['Driver']))
                            db_info = cursor.fetchone()

                            result = {
                                'driver': fastest['Driver'],
                                'driver_number': int(fastest['DriverNumber']),
                                'team': fastest['Team'],
                                'lap_time': format_timedelta(fastest['LapTime']),
                                'laps_completed': int(len(driver_laps)),
                                'driver_id': db_info['driver_id'] if db_info else None,
                                'team_color': db_info['team_color'] if db_info else None,
                            }
                            session_results.append(result)

                            # Save to database
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO fastf1_practice_results
                                    (year, round_number, session_name, driver_abbreviation, driver_number, team,
                                     lap_time, laps_completed)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (year, round_number, session_name, result['driver'], result['driver_number'],
                                      result['team'], result['lap_time'], result['laps_completed']))
                            except Exception as e:
                                logger.warning(f"Could not save practice result to DB: {e}")

                    # Sort by lap time
                    session_results.sort(key=lambda x: x['lap_time'] if x['lap_time'] else 'Z')
                    results[session_name.lower()] = session_results

                except Exception as e:
                    logger.warning(f"Could not load {session_name}: {e}")
                    results[session_name.lower()] = []

            conn.commit()
            conn.close()
            logger.info(f"Saved practice data to database for {year} round {round_number}")

            return json_safe(results)
        except Exception as e:
            logger.error(f"Error getting practice results: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/sprint/{year}/{round_number}")
    def get_sprint_results(year: int, round_number: int):
        """Get sprint race results.

        Args:
            year: Championship year
            round_number: Race round number

        Returns:
            Sprint race results
        """
        import sqlite3
        try:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if we have cached data in database
            cursor.execute("""
                SELECT COUNT(*) as count FROM fastf1_sprint_results
                WHERE year = ? AND round_number = ?
            """, (year, round_number))

            has_data = cursor.fetchone()['count'] > 0

            if has_data:
                # Load from database
                logger.info(f"Loading sprint data from database for {year} round {round_number}")
                cursor.execute("""
                    SELECT
                        fsr.driver_abbreviation as driver,
                        fsr.driver_number,
                        fsr.team,
                        fsr.position,
                        fsr.grid_position,
                        fsr.points,
                        fsr.status,
                        d.id as driver_id,
                        t.color as team_color
                    FROM fastf1_sprint_results fsr
                    LEFT JOIN (
                        SELECT abbreviation, id
                        FROM drivers
                        WHERE (abbreviation, active) IN (
                            SELECT abbreviation, MAX(active)
                            FROM drivers
                            GROUP BY abbreviation
                        )
                        GROUP BY abbreviation
                        HAVING id = MAX(id)
                    ) d ON fsr.driver_abbreviation = d.abbreviation
                    LEFT JOIN teams t ON fsr.team = t.display_name
                    WHERE fsr.year = ? AND fsr.round_number = ?
                    ORDER BY fsr.position
                """, (year, round_number))

                sprint_results = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return json_safe({"results": sprint_results})

            # Not in database, fetch from FastF1
            logger.info(f"Loading sprint data from FastF1 for {year} round {round_number}")

            # Try different sprint session identifiers
            session_identifiers = ['S', 'Sprint']
            session = None

            for identifier in session_identifiers:
                try:
                    session = ff1.load_session(year, round_number, identifier, telemetry=False)
                    break
                except:
                    continue

            if session is None:
                conn.close()
                return {"results": [], "message": "No sprint race for this event"}

            # Get results from session
            results = session.results

            sprint_results = []
            for _, driver in results.iterrows():
                # Get driver_id and team_color from database
                cursor.execute("""
                    SELECT d.id as driver_id, t.color as team_color
                    FROM drivers d
                    LEFT JOIN teams t ON t.display_name = ?
                    WHERE d.abbreviation = ?
                    LIMIT 1
                """, (driver['TeamName'], driver['Abbreviation']))
                db_info = cursor.fetchone()

                result = {
                    'position': int(driver['Position']) if pd.notna(driver['Position']) else None,
                    'driver': driver['Abbreviation'],
                    'driver_number': int(driver['DriverNumber']) if pd.notna(driver['DriverNumber']) else None,
                    'team': driver['TeamName'],
                    'grid_position': int(driver['GridPosition']) if pd.notna(driver['GridPosition']) else None,
                    'points': float(driver['Points']) if pd.notna(driver['Points']) else 0,
                    'status': driver['Status'] if pd.notna(driver['Status']) else 'Unknown',
                    'driver_id': db_info['driver_id'] if db_info else None,
                    'team_color': db_info['team_color'] if db_info else None,
                }
                sprint_results.append(result)

                # Save to database
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO fastf1_sprint_results
                        (year, round_number, driver_abbreviation, driver_number, team,
                         position, grid_position, points, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (year, round_number, result['driver'], result['driver_number'],
                          result['team'], result['position'], result['grid_position'],
                          result['points'], result['status']))
                except Exception as e:
                    logger.warning(f"Could not save sprint result to DB: {e}")

            conn.commit()
            conn.close()
            logger.info(f"Saved sprint data to database for {year} round {round_number}")

            return json_safe({"results": sprint_results})
        except Exception as e:
            logger.error(f"Error getting sprint results: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/session-data/{year}/{round_number}/{session_type}")
    def get_session_data(year: int, round_number: int, session_type: str):
        """Get advanced session data including weather, track status, and race control messages.

        Args:
            year: Championship year
            round_number: Race round number
            session_type: Session type (R, Q, S, FP1, FP2, FP3)

        Returns:
            Advanced session data
        """
        try:
            session = ff1.load_session(
                year, round_number, session_type,
                telemetry=False, weather=True, messages=True
            )

            # Weather data
            weather_data = []
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                weather_df = session.weather_data.head(20)  # Limit to 20 samples
                weather_data = dataframe_to_json_safe(weather_df)

            # Track status data
            track_status_data = []
            if hasattr(session, 'track_status') and session.track_status is not None:
                track_status_df = session.track_status
                track_status_data = dataframe_to_json_safe(track_status_df)

            # Race control messages
            messages_data = []
            if hasattr(session, 'race_control_messages') and session.race_control_messages is not None:
                messages_df = session.race_control_messages
                messages_data = dataframe_to_json_safe(messages_df)

            # Lap times summary
            lap_times = []
            if hasattr(session, 'laps') and session.laps is not None:
                for driver in session.laps['DriverNumber'].unique():
                    driver_laps = session.laps[session.laps['DriverNumber'] == driver]
                    fastest = driver_laps.loc[driver_laps['LapTime'].idxmin()] if not driver_laps['LapTime'].isna().all() else None

                    if fastest is not None:
                        lap_times.append({
                            'driver': fastest['Driver'],
                            'driver_number': int(fastest['DriverNumber']),
                            'team': fastest['Team'],
                            'fastest_lap': format_timedelta(fastest['LapTime']),
                            'average_speed': float(fastest['SpeedI1']) if pd.notna(fastest['SpeedI1']) else None,
                        })

                lap_times.sort(key=lambda x: x['fastest_lap'] if x['fastest_lap'] else 'Z')

            return json_safe({
                'weather': weather_data,
                'track_status': track_status_data,
                'race_control_messages': messages_data,
                'lap_times': lap_times,
            })
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/race-replay/{year}/{round_number}")
    def get_race_replay_data(year: int, round_number: int, include_track: bool = False):
        """Get lap-by-lap position data for race replay visualization.

        Args:
            year: Championship year
            round_number: Race round number
            include_track: Include track position coordinates (X, Y) for track map visualization

        Returns:
            Lap-by-lap position data for all drivers with team colors
        """
        import sqlite3
        try:
            # Load session with or without telemetry based on track map requirement
            session = ff1.load_session(year, round_number, 'R',
                                      telemetry=include_track,
                                      weather=False, messages=False)

            # Get lap data
            laps_df = session.laps

            if laps_df is None or laps_df.empty:
                return json_safe({'error': 'No lap data available', 'drivers': [], 'totalLaps': 0})

            # Get driver colors from database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.abbreviation, t.color, t.display_name as team_name
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN teams t ON sr.team_id = t.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND r.round_number = ? AND rs.session_type = 'Race'
            """, (year, round_number))

            driver_colors = {}
            driver_teams = {}
            for row in cursor.fetchall():
                driver_colors[row['abbreviation']] = row['color']
                driver_teams[row['abbreviation']] = row['team_name']

            conn.close()

            # Get unique drivers
            drivers = laps_df['Driver'].unique()
            max_lap = int(laps_df['LapNumber'].max())

            # Build driver data structure
            driver_data = []
            for driver in drivers:
                driver_laps = laps_df[laps_df['Driver'] == driver].sort_values('LapNumber')

                # Extract lap-by-lap positions
                positions = []
                for lap_num in range(1, max_lap + 1):
                    lap_data = driver_laps[driver_laps['LapNumber'] == lap_num]
                    if not lap_data.empty:
                        position = lap_data.iloc[0]['Position']
                        lap_time = lap_data.iloc[0]['LapTime']
                        positions.append({
                            'lap': lap_num,
                            'position': int(position) if pd.notna(position) else None,
                            'lapTime': format_timedelta(lap_time) if pd.notna(lap_time) else None,
                            'compound': lap_data.iloc[0]['Compound'] if pd.notna(lap_data.iloc[0]['Compound']) else None,
                        })
                    else:
                        # Driver didn't complete this lap (DNF)
                        positions.append({
                            'lap': lap_num,
                            'position': None,
                            'lapTime': None,
                            'compound': None,
                        })

                driver_data.append({
                    'driver': driver,
                    'team': driver_teams.get(driver, 'Unknown'),
                    'color': driver_colors.get(driver, '#999999'),
                    'positions': positions
                })

            # Sort drivers by final position
            driver_data.sort(key=lambda x: x['positions'][-1]['position'] if x['positions'] and x['positions'][-1]['position'] else 999)

            return json_safe({
                'year': year,
                'roundNumber': round_number,
                'totalLaps': max_lap,
                'drivers': driver_data
            })

        except Exception as e:
            logger.error(f"Error getting race replay data: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/track-map/{year}/{round_number}")
    def get_track_map_data(year: int, round_number: int, lap_number: int = 10):
        """Get track map coordinates and driver positions for visualization.

        Args:
            year: Championship year
            round_number: Race round number
            lap_number: Lap number to show driver positions (default: 10)

        Returns:
            Track coordinates (X, Y) for drawing the circuit and driver positions
        """
        import sqlite3
        try:
            session = ff1.load_session(year, round_number, 'R', telemetry=True, weather=False, messages=False)

            # Get a reference lap (ideally from the leader on a clean lap)
            laps_df = session.laps

            # Try to get lap from race leader for track outline
            leader_laps = laps_df[laps_df['Position'] == 1]
            if not leader_laps.empty:
                reference_lap = leader_laps[leader_laps['LapNumber'] == 10]  # Always use lap 10 for track outline
                if reference_lap.empty:
                    reference_lap = leader_laps.iloc[0:1]
            else:
                reference_lap = laps_df[laps_df['LapNumber'] == 10].iloc[0:1]

            if reference_lap.empty:
                return json_safe({'error': 'No lap data available', 'track': [], 'drivers': []})

            # Get position data for the track outline
            lap = reference_lap.iloc[0]
            pos_data = lap.get_pos_data()

            # Subsample to reduce data size (every 10th point)
            pos_data_sampled = pos_data[::10]

            # Extract X, Y coordinates for track
            track_coords = [
                {'x': float(row['X']), 'y': float(row['Y'])}
                for _, row in pos_data_sampled.iterrows()
                if pd.notna(row['X']) and pd.notna(row['Y'])
            ]

            # Get driver colors from database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.abbreviation, t.color, t.display_name as team_name
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN teams t ON sr.team_id = t.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND r.round_number = ? AND rs.session_type = 'Race'
            """, (year, round_number))

            driver_colors = {}
            for row in cursor.fetchall():
                driver_colors[row['abbreviation']] = row['color']

            conn.close()

            # Get driver positions for the specified lap
            driver_positions = []
            lap_laps = laps_df[laps_df['LapNumber'] == lap_number]

            for _, lap_row in lap_laps.iterrows():
                try:
                    driver = lap_row['Driver']
                    position = lap_row['Position']

                    if pd.notna(position):
                        # Get position data for this driver's lap
                        driver_pos_data = lap_row.get_pos_data()

                        # Sample at the middle of the lap to get a representative position
                        mid_index = len(driver_pos_data) // 2
                        if mid_index < len(driver_pos_data):
                            mid_point = driver_pos_data.iloc[mid_index]

                            if pd.notna(mid_point['X']) and pd.notna(mid_point['Y']):
                                driver_positions.append({
                                    'driver': driver,
                                    'position': int(position),
                                    'x': float(mid_point['X']),
                                    'y': float(mid_point['Y']),
                                    'color': driver_colors.get(driver, '#999999')
                                })
                except Exception as e:
                    logger.warning(f"Could not get position for driver {driver}: {e}")
                    continue

            # Sort by position
            driver_positions.sort(key=lambda x: x['position'])

            return json_safe({
                'year': year,
                'roundNumber': round_number,
                'lapNumber': lap_number,
                'track': track_coords,
                'drivers': driver_positions
            })

        except Exception as e:
            logger.error(f"Error getting track map data: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/race-telemetry/{year}/{round_number}")
    def get_race_telemetry_data(year: int, round_number: int):
        """Get full race telemetry with position data for smooth animation.

        Args:
            year: Championship year
            round_number: Race round number

        Returns:
            Complete telemetry position data for all drivers throughout the race
        """
        import sqlite3
        try:
            session = ff1.load_session(year, round_number, 'R', telemetry=True, weather=False, messages=False)

            # Get track outline and pit lane
            laps_df = session.laps

            # Get a clean racing lap (no pit stops) from the leader for main track
            leader_laps = laps_df[laps_df['Position'] == 1]
            if not leader_laps.empty:
                # Find a lap where the leader didn't pit
                clean_laps = leader_laps[leader_laps['PitOutTime'].isna() & leader_laps['PitInTime'].isna()]
                if not clean_laps.empty:
                    reference_lap = clean_laps.iloc[0:1]
                else:
                    reference_lap = leader_laps.iloc[0:1]
            else:
                reference_lap = laps_df.iloc[0:1]

            if reference_lap.empty:
                return json_safe({'error': 'No lap data available', 'track': [], 'pitlane': [], 'drivers': []})

            # Get main track coordinates (racing line)
            lap = reference_lap.iloc[0]
            pos_data = lap.get_pos_data()
            # Use every 2nd point for a complete track outline
            pos_data_sampled = pos_data[::2]

            track_coords = [
                {'x': float(row['X']), 'y': float(row['Y'])}
                for _, row in pos_data_sampled.iterrows()
                if pd.notna(row['X']) and pd.notna(row['Y'])
            ]

            # Close the track loop by adding the first point at the end
            if track_coords and len(track_coords) > 0:
                track_coords.append(track_coords[0])

            # Get pit lane coordinates from a lap where someone pitted
            pitlane_coords = []
            try:
                pit_laps = laps_df[laps_df['PitInTime'].notna()]
                if not pit_laps.empty:
                    pit_lap = pit_laps.iloc[0]
                    pit_pos_data = pit_lap.get_pos_data()

                    # Sample pit lane data
                    pit_pos_sampled = pit_pos_data[::2]

                    all_pit_coords = [
                        {'x': float(row['X']), 'y': float(row['Y'])}
                        for _, row in pit_pos_sampled.iterrows()
                        if pd.notna(row['X']) and pd.notna(row['Y'])
                    ]

                    # Extract just the pit lane section by finding points that deviate from main track
                    # This is a simplified approach - in reality you'd need more sophisticated filtering
                    pitlane_coords = all_pit_coords
            except Exception as e:
                logger.warning(f"Could not extract pit lane coordinates: {e}")

            # Get driver colors from database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.abbreviation, t.color, t.display_name as team_name
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.id
                JOIN teams t ON sr.team_id = t.id
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND r.round_number = ? AND rs.session_type = 'Race'
            """, (year, round_number))

            driver_colors = {}
            for row in cursor.fetchall():
                driver_colors[row['abbreviation']] = row['color']

            conn.close()

            # Get telemetry data for all drivers
            drivers_telemetry = []

            for driver_abbr in laps_df['Driver'].unique():
                try:
                    driver_laps = laps_df[laps_df['Driver'] == driver_abbr].sort_values('LapNumber')

                    # Collect all position data for this driver across all laps
                    all_positions = []
                    lap_boundaries = []  # Track where each lap starts
                    cumulative_time = 0.0  # Track cumulative race time in seconds

                    for _, lap_row in driver_laps.iterrows():
                        lap_num = int(lap_row['LapNumber'])
                        position = lap_row['Position']
                        lap_time = lap_row['LapTime']

                        if pd.notna(position):
                            try:
                                # Get position data for this lap
                                lap_pos_data = lap_row.get_pos_data()

                                # Sample every 5th point to reduce data size while keeping smooth animation
                                lap_pos_data_sampled = lap_pos_data[::5]

                                # Calculate lap time in seconds
                                lap_time_seconds = lap_time.total_seconds() if pd.notna(lap_time) else 90.0  # Default to 90s if missing

                                lap_boundaries.append({
                                    'lapNumber': lap_num,
                                    'startIndex': len(all_positions),
                                    'position': int(position),
                                    'cumulativeTime': cumulative_time,  # Race time at start of this lap
                                    'lapTime': lap_time_seconds  # Duration of this lap in seconds
                                })

                                # Update cumulative time for next lap
                                cumulative_time += lap_time_seconds

                                # Add all position points for this lap
                                for _, point in lap_pos_data_sampled.iterrows():
                                    if pd.notna(point['X']) and pd.notna(point['Y']):
                                        all_positions.append({
                                            'x': float(point['X']),
                                            'y': float(point['Y'])
                                        })
                            except Exception as e:
                                logger.warning(f"Could not get telemetry for {driver_abbr} lap {lap_num}: {e}")
                                continue

                    if all_positions:
                        drivers_telemetry.append({
                            'driver': driver_abbr,
                            'color': driver_colors.get(driver_abbr, '#999999'),
                            'positions': all_positions,
                            'lapBoundaries': lap_boundaries
                        })

                except Exception as e:
                    logger.warning(f"Could not process driver {driver_abbr}: {e}")
                    continue

            return json_safe({
                'year': year,
                'roundNumber': round_number,
                'track': track_coords,
                'pitlane': pitlane_coords,
                'drivers': drivers_telemetry
            })

        except Exception as e:
            logger.error(f"Error getting race telemetry data: {e}")
            raise HTTPException(500, str(e))

    @app.get("/drivers")
    def search_drivers(query: Optional[str] = None, limit: int = 50):
        """Search for drivers across all seasons.

        Args:
            query: Optional search query (searches name, abbreviation)
            limit: Maximum number of results (default: 50)

        Returns:
            List of drivers matching the search
        """
        import sqlite3

        try:
            # Connect to database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build search query
            if query:
                search_pattern = f"%{query}%"
                cursor.execute("""
                    SELECT DISTINCT
                        d.id as driver_id,
                        d.abbreviation,
                        d.display_name as driver_name,
                        d.first_name,
                        d.last_name,
                        d.nationality,
                        d.number as driver_number,
                        d.headshot_url,
                        d.flag_url,
                        d.active,
                        COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' THEN sr.session_espn_competition_id END) as total_races
                    FROM drivers d
                    LEFT JOIN session_results sr ON d.id = sr.driver_id
                    LEFT JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    WHERE d.display_name LIKE ? OR d.abbreviation LIKE ?
                    GROUP BY d.id
                    ORDER BY d.active DESC, d.display_name
                    LIMIT ?
                """, (search_pattern, search_pattern, limit))
            else:
                # Return most recent/active drivers
                cursor.execute("""
                    SELECT DISTINCT
                        d.id as driver_id,
                        d.abbreviation,
                        d.display_name as driver_name,
                        d.first_name,
                        d.last_name,
                        d.nationality,
                        d.number as driver_number,
                        d.headshot_url,
                        d.flag_url,
                        d.active,
                        COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' THEN sr.session_espn_competition_id END) as total_races
                    FROM drivers d
                    LEFT JOIN session_results sr ON d.id = sr.driver_id
                    LEFT JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    GROUP BY d.id
                    ORDER BY d.active DESC, d.display_name
                    LIMIT ?
                """, (limit,))

            drivers_list = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return json_safe({
                'total': len(drivers_list),
                'drivers': drivers_list
            })

        except Exception as e:
            logger.error(f"Error searching drivers: {e}")
            raise HTTPException(500, str(e))

    @app.get("/drivers/profile/{driver_id}")
    def get_driver_profile(driver_id: str):
        """Get detailed driver profile with career statistics.

        Args:
            driver_id: ESPN driver ID

        Returns:
            Driver profile with career stats
        """
        import sqlite3

        try:
            # Connect to database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get driver basic info
            cursor.execute("""
                SELECT
                    d.*,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' THEN sr.session_espn_competition_id END) as total_races,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' AND sr.position = 1 THEN sr.session_espn_competition_id END) as wins,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' AND sr.position <= 3 THEN sr.session_espn_competition_id END) as podiums
                FROM drivers d
                LEFT JOIN session_results sr ON d.id = sr.driver_id
                LEFT JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                WHERE d.id = ?
                GROUP BY d.id
            """, (driver_id,))

            driver_row = cursor.fetchone()
            if not driver_row:
                raise HTTPException(404, f"Driver {driver_id} not found")

            driver = dict(driver_row)

            # Get season-by-season statistics
            cursor.execute("""
                SELECT
                    r.year,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' THEN sr.session_espn_competition_id END) as races,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' AND sr.position = 1 THEN sr.session_espn_competition_id END) as wins,
                    COUNT(DISTINCT CASE WHEN rs.session_type = 'Race' AND sr.position <= 3 THEN sr.session_espn_competition_id END) as podiums,
                    t.display_name as team_name,
                    t.logo_url as team_logo
                FROM session_results sr
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                LEFT JOIN teams t ON sr.team_id = t.id
                WHERE sr.driver_id = ? AND rs.session_type = 'Race'
                GROUP BY r.year, t.id
                ORDER BY r.year DESC
            """, (driver_id,))

            seasons = [dict(row) for row in cursor.fetchall()]

            # Calculate points and championship position for each season
            def get_points_system(year: int) -> dict:
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
                else:
                    return {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}

            def get_sprint_points_system(year: int) -> dict:
                if year >= 2021:
                    return {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                return {}

            def has_fastest_lap_point(year: int) -> bool:
                return year <= 1959 or year >= 2019

            def is_half_points_race(year: int, round_number: int) -> bool:
                """Check if a race awarded half points (usually due to red flag/shortened race)."""
                half_points_races = {
                    1984: [6],  # Monaco 1984
                    2021: [12], # Belgian GP 2021
                }
                return round_number in half_points_races.get(year, [])

            # Enrich seasons with points and championship position
            for season in seasons:
                year = season['year']
                points_system = get_points_system(year)
                sprint_points_system = get_sprint_points_system(year)
                fastest_lap_enabled = has_fastest_lap_point(year)

                # Get all results for this driver in this year
                cursor.execute("""
                    SELECT sr.position, sr.fastest_lap, rs.session_type, r.round_number
                    FROM session_results sr
                    JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                    WHERE sr.driver_id = ? AND r.year = ? AND rs.session_type IN ('Race', 'Sprint Race')
                """, (driver_id, year))

                total_points = 0
                for result in cursor.fetchall():
                    position = result[0]
                    fastest_lap = result[1]
                    session_type = result[2]
                    round_number = result[3]

                    if session_type == 'Race' and position:
                        race_points = points_system.get(position, 0)

                        # Apply half points if this was a shortened race
                        if is_half_points_race(year, round_number):
                            race_points = race_points / 2

                        if fastest_lap_enabled and fastest_lap and position:
                            if year <= 1959 or position <= 10:
                                race_points += 1
                        total_points += race_points
                    elif session_type == 'Sprint Race' and position:
                        total_points += sprint_points_system.get(position, 0)

                season['points'] = total_points

                # Get championship position for this year
                cursor.execute("""
                    WITH driver_points AS (
                        SELECT
                            sr.driver_id,
                            SUM(
                                CASE
                                    WHEN rs.session_type = 'Race' AND sr.position IS NOT NULL THEN
                                        CASE sr.position
                                            WHEN 1 THEN ?
                                            WHEN 2 THEN ?
                                            WHEN 3 THEN ?
                                            WHEN 4 THEN ?
                                            WHEN 5 THEN ?
                                            WHEN 6 THEN ?
                                            WHEN 7 THEN ?
                                            WHEN 8 THEN ?
                                            WHEN 9 THEN ?
                                            WHEN 10 THEN ?
                                            ELSE 0
                                        END
                                    ELSE 0
                                END
                            ) as total_points
                        FROM session_results sr
                        JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                        JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                        WHERE r.year = ? AND rs.session_type = 'Race'
                        GROUP BY sr.driver_id
                    )
                    SELECT COUNT(*) + 1 as championship_position
                    FROM driver_points
                    WHERE total_points > (
                        SELECT total_points FROM driver_points WHERE driver_id = ?
                    )
                """, tuple(points_system.get(i, 0) for i in range(1, 11)) + (year, driver_id))

                result = cursor.fetchone()
                season['championship_position'] = result[0] if result else None

            # Get all race results (race-by-race)
            cursor.execute("""
                SELECT
                    r.year,
                    r.round_number,
                    r.event_name,
                    r.country,
                    rs.session_type,
                    sr.position,
                    sr.grid_position,
                    sr.fastest_lap,
                    t.display_name as team_name,
                    t.logo_url as team_logo
                FROM session_results sr
                JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                LEFT JOIN teams t ON sr.team_id = t.id
                WHERE sr.driver_id = ? AND rs.session_type = 'Race'
                ORDER BY r.year DESC, r.round_number DESC
            """, (driver_id,))

            race_results = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return json_safe({
                'driver': driver,
                'seasons': seasons,
                'raceResults': race_results
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting driver profile: {e}")
            raise HTTPException(500, str(e))

    @app.get("/drivers/season/{year}")
    def get_drivers_by_season(year: int, sort: Optional[str] = "points"):
        """Get all drivers for a specific season with their stats.

        Args:
            year: Season year
            sort: Sort by 'points', 'name', 'team', or 'nationality' (default: 'points')

        Returns:
            List of drivers with stats for that season
        """
        import sqlite3

        try:
            # Connect to database
            import os
            db_path = os.path.join(os.path.dirname(__file__), '../../../f1_data.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get drivers who participated in the season with stats
            cursor.execute("""
                WITH driver_stats AS (
                    SELECT
                        d.id as driver_id,
                        d.abbreviation,
                        d.display_name as driver_name,
                        d.first_name,
                        d.last_name,
                        d.nationality,
                        d.number as driver_number,
                        d.headshot_url,
                        d.flag_url,
                        t.id as team_id,
                        t.display_name as team_name,
                        t.logo_url as team_logo,
                        t.color as team_color,
                        r.round_number,
                        rs.session_type,
                        sr.position,
                        sr.fastest_lap,
                        ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY r.round_number DESC) as rn
                    FROM session_results sr
                    JOIN drivers d ON sr.driver_id = d.id
                    JOIN teams t ON sr.team_id = t.id
                    JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                    WHERE r.year = ? AND rs.session_type IN ('Race', 'Sprint Race')
                ),
                driver_latest_team AS (
                    SELECT
                        driver_id, abbreviation, driver_name, first_name, last_name,
                        nationality, driver_number, headshot_url, flag_url,
                        team_id, team_name, team_logo, team_color
                    FROM driver_stats
                    WHERE rn = 1
                )
                SELECT * FROM driver_latest_team
                ORDER BY driver_name
            """, (year,))

            drivers_data = [dict(row) for row in cursor.fetchall()]

            # Get points system for the year
            def get_points_system(year: int) -> dict:
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
                else:
                    return {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}

            def get_sprint_points_system(year: int) -> dict:
                if year >= 2021:
                    return {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
                return {}

            def has_fastest_lap_point(year: int) -> bool:
                return year <= 1959 or year >= 2019

            points_system = get_points_system(year)
            sprint_points_system = get_sprint_points_system(year)
            fastest_lap_enabled = has_fastest_lap_point(year)

            # Calculate stats for each driver
            drivers_list = []
            for driver_data in drivers_data:
                driver_id = driver_data['driver_id']

                # Get race results for this driver
                cursor.execute("""
                    SELECT
                        rs.session_type,
                        sr.position,
                        sr.fastest_lap,
                        r.round_number
                    FROM session_results sr
                    JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                    WHERE sr.driver_id = ? AND r.year = ? AND rs.session_type IN ('Race', 'Sprint Race')
                """, (driver_id, year))

                results = cursor.fetchall()

                # Calculate statistics
                total_points = 0
                wins = 0
                podiums = 0
                poles = 0
                races_entered = 0

                for result in results:
                    session_type = result['session_type']
                    position = result['position']

                    if session_type == 'Race':
                        races_entered += 1
                        race_points = points_system.get(position, 0)

                        if fastest_lap_enabled and result['fastest_lap'] and position:
                            if year <= 1959 or position <= 10:
                                race_points += 1

                        total_points += race_points

                        if position == 1:
                            wins += 1
                        if position <= 3:
                            podiums += 1

                    elif session_type == 'Sprint Race':
                        sprint_points = sprint_points_system.get(position, 0)
                        total_points += sprint_points

                # Get pole positions
                cursor.execute("""
                    SELECT COUNT(*) as pole_count
                    FROM session_results sr
                    JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
                    JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                    WHERE sr.driver_id = ? AND r.year = ?
                    AND rs.session_type = 'Qualifying' AND sr.position = 1
                """, (driver_id, year))

                poles = cursor.fetchone()['pole_count']

                drivers_list.append({
                    'driverId': driver_id,
                    'abbreviation': driver_data['abbreviation'],
                    'driverName': driver_data['driver_name'],
                    'firstName': driver_data['first_name'],
                    'lastName': driver_data['last_name'],
                    'nationality': driver_data['nationality'],
                    'driverNumber': driver_data['driver_number'],
                    'headshotUrl': driver_data['headshot_url'],
                    'flagUrl': driver_data['flag_url'],
                    'teamName': driver_data['team_name'],
                    'teamLogo': driver_data['team_logo'],
                    'teamColor': driver_data['team_color'],
                    'stats': {
                        'totalPoints': total_points,
                        'wins': wins,
                        'podiums': podiums,
                        'poles': poles,
                        'racesEntered': races_entered
                    }
                })

            # Sort based on parameter
            if sort == "points":
                drivers_list.sort(key=lambda x: x['stats']['totalPoints'], reverse=True)
            elif sort == "name":
                drivers_list.sort(key=lambda x: x['driverName'])
            elif sort == "team":
                drivers_list.sort(key=lambda x: x['teamName'])
            elif sort == "nationality":
                drivers_list.sort(key=lambda x: x['nationality'])

            # Add championship position after sorting by points
            if sort == "points":
                for i, driver in enumerate(drivers_list, 1):
                    driver['championshipPosition'] = i

            conn.close()

            return json_safe({
                'year': year,
                'drivers': drivers_list
            })

        except Exception as e:
            logger.error(f"Error getting drivers for season {year}: {e}")
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
