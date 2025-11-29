from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class EventSchedule(Base):
    """Cache for season schedules"""
    __tablename__ = "event_schedules"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, index=True)
    round_number = Column(Integer)
    event_name = Column(String(100))
    location = Column(String(100))
    country = Column(String(100))
    event_date = Column(DateTime)
    event_format = Column(String(50))
    session1_date = Column(DateTime)
    session2_date = Column(DateTime)
    session3_date = Column(DateTime)
    qualifying_date = Column(DateTime)
    sprint_date = Column(DateTime)
    race_date = Column(DateTime)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('year', 'round_number', name='uq_year_round'),
        Index('idx_year_event', 'year', 'event_name'),
    )


class Session(Base):
    """Cache for session metadata"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    race = Column(String(100), nullable=False)  # Race name or number
    session_type = Column(String(10), nullable=False)  # FP1, FP2, FP3, Q, S, R
    session_name = Column(String(100))
    event_name = Column(String(100))
    circuit = Column(String(100))
    session_date = Column(DateTime)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('year', 'race', 'session_type', name='uq_session'),
        Index('idx_year_race', 'year', 'race'),
    )


class SessionResult(Base):
    """Cache for session results (race/qualifying finishing order)"""
    __tablename__ = "session_results"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False, index=True)
    position = Column(Integer)
    driver_number = Column(String(10))
    driver_abbreviation = Column(String(3))
    driver_name = Column(String(100))
    team_name = Column(String(100))
    grid_position = Column(Integer)
    q1_time = Column(Float)  # seconds
    q2_time = Column(Float)
    q3_time = Column(Float)
    race_time = Column(Float)  # seconds
    status = Column(String(50))
    points = Column(Float)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_session_position', 'session_id', 'position'),
    )


class LapTime(Base):
    """Cache for lap times"""
    __tablename__ = "lap_times"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False, index=True)
    driver_abbreviation = Column(String(3), nullable=False)
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(Float)  # seconds
    sector1_time = Column(Float)
    sector2_time = Column(Float)
    sector3_time = Column(Float)
    compound = Column(String(20))
    tyre_life = Column(Integer)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('session_id', 'driver_abbreviation', 'lap_number', name='uq_lap'),
        Index('idx_session_driver', 'session_id', 'driver_abbreviation'),
    )


class TelemetryData(Base):
    """Cache for telemetry data"""
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    driver_abbreviation = Column(String(3), nullable=False)
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(Float)
    # Store telemetry as JSON text
    telemetry_json = Column(Text, nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('session_id', 'driver_abbreviation', 'lap_number', name='uq_telemetry'),
        Index('idx_telemetry_session', 'session_id', 'driver_abbreviation', 'lap_number'),
    )


class DriverStanding(Base):
    """Cache for driver championship standings"""
    __tablename__ = "driver_standings"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    driver_name = Column(String(100))
    team_name = Column(String(100))
    points = Column(Float)
    wins = Column(Integer)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('year', 'position', name='uq_driver_standing'),
        Index('idx_year_driver', 'year', 'driver_name'),
    )


class ConstructorStanding(Base):
    """Cache for constructor championship standings"""
    __tablename__ = "constructor_standings"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    team_name = Column(String(100))
    points = Column(Float)
    wins = Column(Integer)
    cached_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('year', 'position', name='uq_constructor_standing'),
        Index('idx_year_constructor', 'year', 'team_name'),
    )
