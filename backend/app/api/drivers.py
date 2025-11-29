from fastapi import APIRouter, HTTPException
from ..services.espn_service import espn_service
from ..services.fastf1_service import FastF1Service
import fastf1
import pandas as pd

router = APIRouter()


@router.get("/drivers/{driver_name}/seasons")
async def get_driver_seasons(driver_name: str):
    """
    Get list of seasons a driver participated in

    Args:
        driver_name: Driver name in URL format (e.g., 'max-verstappen')
    """
    try:
        display_name = driver_name.replace('-', ' ').title()
        current_year = pd.Timestamp.now().year

        # Check FastF1 availability (2018-present)
        seasons = []

        # Try recent years with FastF1 (only check first completed race of each year)
        for year in range(current_year, 2017, -1):
            try:
                schedule = fastf1.get_event_schedule(year)

                # Find first completed race in this year
                for _, event in schedule.iterrows():
                    if pd.isna(event['EventDate']) or event['EventDate'] > pd.Timestamp.now():
                        continue

                    round_number = int(event['RoundNumber'])
                    if round_number == 0:  # Skip testing events
                        continue

                    try:
                        session = FastF1Service.get_session(year, round_number, 'R')
                        results = session.results

                        if results is not None and not results.empty:
                            # Check if driver participated in this race
                            for _, driver in results.iterrows():
                                driver_full_name = f"{driver.get('FirstName', '')} {driver.get('LastName', '')}".strip()
                                if driver_full_name.lower() == display_name.lower():
                                    seasons.append(year)
                                    break

                        # Only check first race, then move to next year
                        break
                    except:
                        # Try next race in this year
                        continue
            except:
                continue

        if not seasons:
            raise HTTPException(status_code=404, detail=f"No seasons found for driver '{display_name}'")

        return {
            'driver_name': display_name,
            'seasons': sorted(seasons, reverse=True),
            'debut_year': min(seasons) if seasons else None,
            'latest_year': max(seasons) if seasons else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch seasons: {str(e)}")


@router.get("/drivers/{driver_name}")
async def get_driver_details(driver_name: str, year: int = 2024):
    """
    Get comprehensive driver information including season stats and race-by-race results

    Args:
        driver_name: Driver name in URL format (e.g., 'max-verstappen')
        year: Season year
    """
    try:
        # Convert URL format to title case for matching
        display_name = driver_name.replace('-', ' ').title()

        # Get schedule
        schedule = fastf1.get_event_schedule(year)

        # Find driver abbreviation from first available race
        abbreviation = None
        for _, event in schedule.iterrows():
            try:
                if pd.isna(event['EventDate']) or event['EventDate'] > pd.Timestamp.now():
                    continue

                round_number = int(event['RoundNumber'])
                if round_number == 0:  # Skip testing events
                    continue
                session = FastF1Service.get_session(year, round_number, 'R')
                results = session.results

                if results is not None and not results.empty:
                    # Try to find driver by full name
                    for _, driver in results.iterrows():
                        driver_full_name = f"{driver.get('FirstName', '')} {driver.get('LastName', '')}".strip()
                        if driver_full_name.lower() == display_name.lower():
                            abbreviation = driver['Abbreviation']
                            break

                if abbreviation:
                    break
            except:
                continue

        if not abbreviation:
            raise HTTPException(status_code=404, detail=f"Driver '{display_name}' not found in {year} season")

        # Collect race results for this driver
        race_results = []
        driver_team = None
        driver_number = None

        for _, event in schedule.iterrows():
            try:
                # Skip future races and testing events (round 0)
                if pd.isna(event['EventDate']) or event['EventDate'] > pd.Timestamp.now():
                    continue

                round_number = int(event['RoundNumber'])
                if round_number == 0:
                    continue
                event_name = event['EventName']

                # Get race results
                session = FastF1Service.get_session(year, round_number, 'R')
                results = session.results

                if results is not None and not results.empty:
                    # Find this driver's result
                    driver_result = results[results['Abbreviation'] == abbreviation]
                    if not driver_result.empty:
                        result = driver_result.iloc[0]

                        # Store team and number from most recent race
                        if not driver_team:
                            driver_team = result.get('TeamName', '')
                            driver_number = result.get('DriverNumber', '')

                        # Get qualifying result
                        qual_position = None
                        try:
                            qual_session = FastF1Service.get_session(year, round_number, 'Q')
                            qual_results = qual_session.results
                            if qual_results is not None and not qual_results.empty:
                                qual_driver = qual_results[qual_results['Abbreviation'] == abbreviation]
                                if not qual_driver.empty:
                                    qual_position = int(qual_driver.iloc[0]['Position'])
                        except:
                            pass

                        race_results.append({
                            'round': round_number,
                            'race_name': event_name,
                            'circuit': event.get('Location', ''),
                            'date': str(event['EventDate'])[:10],
                            'grid_position': qual_position,
                            'finish_position': int(result['Position']) if pd.notna(result['Position']) else None,
                            'points': float(result['Points']) if pd.notna(result['Points']) else 0,
                            'status': result.get('Status', ''),
                            'team': result.get('TeamName', '')
                        })
            except Exception as e:
                print(f"Error getting results for round {round_number}: {e}")
                continue

        # Calculate season stats
        total_wins = sum(1 for r in race_results if r['finish_position'] == 1)
        total_podiums = sum(1 for r in race_results if r['finish_position'] and r['finish_position'] <= 3)
        total_points = sum(r['points'] for r in race_results)
        races_completed = len(race_results)

        # Calculate average qualifying vs race performance
        quali_positions = [r['grid_position'] for r in race_results if r['grid_position']]
        race_positions = [r['finish_position'] for r in race_results if r['finish_position']]

        avg_quali = sum(quali_positions) / len(quali_positions) if quali_positions else None
        avg_race = sum(race_positions) / len(race_positions) if race_positions else None

        # Get championship position from standings
        championship_position = None
        try:
            standings_data = await espn_service.get_driver_standings(year)
            for idx, standing in enumerate(standings_data.get('standings', []), 1):
                athlete = standing.get('athlete', {})
                if athlete.get('fullName', '').lower() == display_name.lower():
                    championship_position = idx
                    break
        except:
            pass

        return {
            'driver': {
                'name': display_name,
                'abbreviation': abbreviation,
                'team': driver_team or '',
                'number': str(driver_number) if driver_number else '',
            },
            'season_stats': {
                'year': year,
                'championship_position': championship_position,
                'points': total_points,
                'wins': total_wins,
                'podiums': total_podiums,
                'races_completed': races_completed,
                'avg_qualifying_position': round(avg_quali, 1) if avg_quali else None,
                'avg_race_position': round(avg_race, 1) if avg_race else None
            },
            'race_results': race_results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver details: {str(e)}")
