"""FastF1 wrapper client implementation."""

import fastf1
from typing import Optional, Union, Literal
import pandas as pd
from pathlib import Path


class FastF1Client:
    """Wrapper client for FastF1 library.

    Usage:
        client = FastF1Client(cache_dir='./cache')
        session = client.get_session(2024, 'Monaco', 'Q')
        fastest_lap = client.get_fastest_lap(session, 'VER')
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize FastF1 client.

        Args:
            cache_dir: Directory for caching data (optional but recommended)
        """
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            fastf1.Cache.enable_cache(cache_dir)

    # Session Management

    def get_session(
        self,
        year: int,
        gp: Union[str, int],
        identifier: Union[str, int],
        backend: Optional[Literal["fastf1", "f1timing", "ergast"]] = None,
    ):
        """Get a session object.

        Args:
            year: Championship year
            gp: Grand Prix name (fuzzy matching) or round number
            identifier: Session identifier ('FP1', 'FP2', 'FP3', 'Q', 'S', 'R')
            backend: Data source backend (default: 'fastf1')

        Returns:
            fastf1.core.Session object (not loaded yet)
        """
        return fastf1.get_session(year, gp, identifier, backend=backend)

    def load_session(
        self,
        year: int,
        gp: Union[str, int],
        identifier: Union[str, int],
        laps: bool = True,
        telemetry: bool = True,
        weather: bool = True,
        messages: bool = True,
    ):
        """Get and load a session with data.

        Args:
            year: Championship year
            gp: Grand Prix name or round number
            identifier: Session identifier
            laps: Load lap data
            telemetry: Load telemetry data
            weather: Load weather data
            messages: Load race control messages

        Returns:
            Loaded fastf1.core.Session object
        """
        session = self.get_session(year, gp, identifier)
        session.load(
            laps=laps,
            telemetry=telemetry,
            weather=weather,
            messages=messages
        )
        return session

    # Event & Schedule

    def get_event(self, year: int, gp: Union[str, int]):
        """Get event information.

        Args:
            year: Championship year
            gp: Grand Prix name or round number

        Returns:
            Event object
        """
        return fastf1.get_event(year, gp)

    def get_event_schedule(self, year: int) -> pd.DataFrame:
        """Get full season schedule.

        Args:
            year: Championship year

        Returns:
            DataFrame with all events in the season
        """
        return fastf1.get_event_schedule(year)

    # Lap Analysis

    def get_fastest_lap(self, session, driver: Optional[str] = None):
        """Get fastest lap from session.

        Args:
            session: Loaded session object
            driver: Driver abbreviation (e.g., 'VER'). If None, returns overall fastest.

        Returns:
            Lap object
        """
        if driver:
            return session.laps.pick_drivers(driver).pick_fastest()
        return session.laps.pick_fastest()

    def get_driver_laps(self, session, driver: str):
        """Get all laps for a driver.

        Args:
            session: Loaded session object
            driver: Driver abbreviation or number

        Returns:
            Laps DataFrame
        """
        return session.laps.pick_drivers(driver)

    def get_quick_laps(self, session, driver: Optional[str] = None):
        """Get quick laps (outliers removed).

        Args:
            session: Loaded session object
            driver: Optional driver filter

        Returns:
            Laps DataFrame
        """
        laps = session.laps.pick_quicklaps()
        if driver:
            laps = laps.pick_drivers(driver)
        return laps

    # Telemetry

    def get_lap_telemetry(
        self,
        lap,
        frequency: Union[int, Literal["original"], None] = None
    ):
        """Get telemetry for a lap.

        Args:
            lap: Lap object
            frequency: Resampling frequency (Hz) or 'original'

        Returns:
            Telemetry DataFrame
        """
        return lap.get_telemetry(frequency=frequency)

    def get_car_data(self, lap, pad: int = 0, pad_side: str = "both"):
        """Get car telemetry data.

        Args:
            lap: Lap object
            pad: Padding samples
            pad_side: Padding side ('both', 'before', 'after')

        Returns:
            Telemetry DataFrame with car data
        """
        return lap.get_car_data(pad=pad, pad_side=pad_side)

    def get_position_data(self, lap, pad: int = 0, pad_side: str = "both"):
        """Get position/GPS data.

        Args:
            lap: Lap object
            pad: Padding samples
            pad_side: Padding side

        Returns:
            Telemetry DataFrame with position data
        """
        return lap.get_pos_data(pad=pad, pad_side=pad_side)

    # Comparison & Analysis

    def compare_laps(self, lap1, lap2, channels: Optional[list] = None):
        """Compare telemetry between two laps.

        Args:
            lap1: First lap object
            lap2: Second lap object
            channels: Telemetry channels to compare (default: ['Speed', 'Throttle'])

        Returns:
            Dict with telemetry DataFrames
        """
        if channels is None:
            channels = ["Speed", "Throttle"]

        tel1 = lap1.get_telemetry()
        tel2 = lap2.get_telemetry()

        return {
            "lap1": {
                "driver": lap1["Driver"],
                "time": lap1["LapTime"],
                "telemetry": tel1[channels + ["Distance"]],
            },
            "lap2": {
                "driver": lap2["Driver"],
                "time": lap2["LapTime"],
                "telemetry": tel2[channels + ["Distance"]],
            },
        }

    # Weather & Conditions

    def get_weather(self, session) -> pd.DataFrame:
        """Get weather data for session.

        Args:
            session: Loaded session object

        Returns:
            Weather DataFrame
        """
        return session.weather_data

    def get_race_control_messages(self, session) -> pd.DataFrame:
        """Get race control messages.

        Args:
            session: Loaded session object

        Returns:
            Race control messages DataFrame
        """
        return session.race_control_messages

    # Results & Standings

    def get_session_results(self, session) -> pd.DataFrame:
        """Get session results.

        Args:
            session: Loaded session object

        Returns:
            Results DataFrame
        """
        return session.results

    def get_driver_info(self, session, driver: str) -> pd.Series:
        """Get driver information from session.

        Args:
            session: Loaded session object
            driver: Driver abbreviation

        Returns:
            Driver info Series
        """
        return session.get_driver(driver)


# Example usage
if __name__ == "__main__":
    # Initialize with cache
    client = FastF1Client(cache_dir="./f1_cache")

    # Load session
    session = client.load_session(2024, "Monaco", "Q")

    # Get fastest lap
    fastest = client.get_fastest_lap(session)
    print(f"Fastest: {fastest['Driver']} - {fastest['LapTime']}")

    # Get telemetry
    telemetry = client.get_lap_telemetry(fastest)
    print(f"\nTelemetry channels: {telemetry.columns.tolist()}")

    # Compare two drivers
    ver_lap = client.get_fastest_lap(session, "VER")
    lec_lap = client.get_fastest_lap(session, "LEC")
    comparison = client.compare_laps(ver_lap, lec_lap)
    print(f"\nVER: {comparison['lap1']['time']}")
    print(f"LEC: {comparison['lap2']['time']}")
