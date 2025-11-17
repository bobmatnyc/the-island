"""
Flights API endpoints for visualizing flight paths and passenger data
"""

from fastapi import APIRouter, Query, Depends, Request
from typing import Optional
import json
from pathlib import Path

router = APIRouter()

# Paths (avoid importing from app to prevent circular imports)
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md"
METADATA_DIR = DATA_DIR / "metadata"

# Import get_current_user at runtime to avoid circular imports
def get_auth_dependency():
    from app import get_current_user
    return get_current_user


@router.get("/api/flights/all")
async def get_all_flights(username: str = Depends(get_current_user)):
    """Get all 1,167 flights grouped by route for map visualization.

    Returns:
        All flights with geocoded locations grouped by route:
        - routes: Array of unique routes with all flights on that route
        - total_flights: Total number of flights
        - date_range: First and last flight dates
        - unique_passengers: Count of unique passengers
    """
    try:
        # Load flight data
        flight_data_path = MD_DIR / "entities/flight_logs_by_flight.json"
        if not flight_data_path.exists():
            return {
                "routes": [],
                "total_flights": 0,
                "error": "Flight data not found"
            }

        with open(flight_data_path) as f:
            flight_data = json.load(f)

        # Load location database
        locations_path = METADATA_DIR / "flight_locations.json"
        if not locations_path.exists():
            return {
                "routes": [],
                "total_flights": 0,
                "error": "Location database not found"
            }

        with open(locations_path) as f:
            locations_db = json.load(f)
            airports = locations_db.get("airports", {})

        # Process all flights and group by route
        all_flights = flight_data.get("flights", [])
        route_map = {}  # Key: "ORIGIN-DEST", Value: {origin, destination, flights[]}
        all_dates = []
        unique_passengers_set = set()

        for flight in all_flights:
            route = flight.get("route", "")
            if "-" not in route:
                continue

            origin_code, dest_code = route.split("-", 1)

            # Get location data
            origin_data = airports.get(origin_code)
            dest_data = airports.get(dest_code)

            if not origin_data or not dest_data:
                continue

            # Track unique passengers
            for passenger in flight.get("passengers", []):
                unique_passengers_set.add(passenger)

            # Track dates
            flight_date = flight.get("date", "")
            if flight_date:
                all_dates.append(flight_date)

            # Group by route
            route_key = f"{origin_code}-{dest_code}"
            if route_key not in route_map:
                route_map[route_key] = {
                    "origin": {
                        "code": origin_code,
                        **origin_data
                    },
                    "destination": {
                        "code": dest_code,
                        **dest_data
                    },
                    "flights": []
                }

            # Add flight to route
            route_map[route_key]["flights"].append({
                "id": flight.get("id"),
                "date": flight_date,
                "passengers": flight.get("passengers", []),
                "passenger_count": flight.get("passenger_count", len(flight.get("passengers", []))),
                "aircraft": flight.get("tail_number", "")
            })

        # Convert route_map to array with frequency
        routes = []
        for route_key, route_data in route_map.items():
            routes.append({
                "origin": route_data["origin"],
                "destination": route_data["destination"],
                "flights": route_data["flights"],
                "frequency": len(route_data["flights"])
            })

        # Sort routes by frequency (most traveled routes first)
        routes.sort(key=lambda r: r["frequency"], reverse=True)

        # Calculate date range
        date_range = {}
        if all_dates:
            # Sort dates (handle MM/DD/YYYY format)
            sorted_dates = sorted(all_dates, key=lambda d: parse_date_for_sort(d))
            date_range = {
                "start": sorted_dates[0],
                "end": sorted_dates[-1]
            }

        return {
            "routes": routes,
            "total_flights": len(all_flights),
            "unique_routes": len(routes),
            "unique_passengers": len(unique_passengers_set),
            "date_range": date_range,
            "airports": airports
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "routes": [],
            "total_flights": 0,
            "error": str(e)
        }


def parse_date_for_sort(date_str: str) -> str:
    """Convert MM/DD/YYYY to YYYY-MM-DD for sorting"""
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3:
            month, day, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str


@router.get("/api/flights")
async def get_flights(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    passenger: Optional[str] = Query(None),
    username: str = Depends(get_current_user)
):
    """Get flight data with geocoded locations and filters.

    Query Parameters:
        start_date: Filter flights from this date (YYYY-MM-DD or MM/DD/YYYY)
        end_date: Filter flights until this date (YYYY-MM-DD or MM/DD/YYYY)
        passenger: Filter flights with specific passenger (case-insensitive)

    Returns:
        Flight data with geocoded locations, statistics, and filtering options
    """
    try:
        # Load flight data
        flight_data_path = MD_DIR / "entities/flight_logs_by_flight.json"
        if not flight_data_path.exists():
            return {
                "total_flights": 0,
                "flights": [],
                "locations": {},
                "error": "Flight data not found"
            }

        with open(flight_data_path) as f:
            flight_data = json.load(f)

        # Load location database
        locations_path = METADATA_DIR / "flight_locations.json"
        if not locations_path.exists():
            return {
                "total_flights": 0,
                "flights": [],
                "locations": {},
                "error": "Location database not found"
            }

        with open(locations_path) as f:
            locations_db = json.load(f)
            airports = locations_db.get("airports", {})

        # Process flights
        all_flights = flight_data.get("flights", [])
        processed_flights = []
        location_usage = {}

        for flight in all_flights:
            route = flight.get("route", "")
            if "-" not in route:
                continue

            origin_code, dest_code = route.split("-", 1)

            # Get location data
            origin_data = airports.get(origin_code)
            dest_data = airports.get(dest_code)

            if not origin_data or not dest_data:
                continue

            # Track location usage
            location_usage[origin_code] = location_usage.get(origin_code, 0) + 1
            location_usage[dest_code] = location_usage.get(dest_code, 0) + 1

            # Apply filters
            flight_date = flight.get("date", "")
            passengers = flight.get("passengers", [])

            # Date filtering (handle both YYYY-MM-DD and MM/DD/YYYY formats)
            if start_date or end_date:
                try:
                    # Convert flight date to comparable format
                    if "/" in flight_date:
                        # MM/DD/YYYY format
                        month, day, year = flight_date.split("/")
                        flight_date_obj = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        flight_date_obj = flight_date

                    if start_date and flight_date_obj < start_date:
                        continue
                    if end_date and flight_date_obj > end_date:
                        continue
                except (ValueError, AttributeError):
                    pass

            # Passenger filtering
            if passenger:
                passenger_lower = passenger.lower()
                if not any(passenger_lower in p.lower() for p in passengers):
                    continue

            processed_flights.append({
                "id": flight.get("id"),
                "date": flight_date,
                "origin": {
                    "code": origin_code,
                    **origin_data
                },
                "destination": {
                    "code": dest_code,
                    **dest_data
                },
                "passengers": passengers,
                "passenger_count": flight.get("passenger_count", len(passengers)),
                "aircraft": flight.get("tail_number", "")
            })

        # Calculate statistics
        unique_routes = set()
        passenger_counts = {}
        aircraft_usage = {}

        for flight in processed_flights:
            route_key = f"{flight['origin']['code']}-{flight['destination']['code']}"
            unique_routes.add(route_key)

            for passenger in flight["passengers"]:
                passenger_counts[passenger] = passenger_counts.get(passenger, 0) + 1

            aircraft = flight["aircraft"]
            if aircraft:
                aircraft_usage[aircraft] = aircraft_usage.get(aircraft, 0) + 1

        # Get top passengers
        top_passengers = sorted(
            passenger_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_flights": len(processed_flights),
            "flights": processed_flights,
            "locations": airports,
            "statistics": {
                "unique_routes": len(unique_routes),
                "unique_locations": len(location_usage),
                "top_passengers": [
                    {"name": name, "flights": count}
                    for name, count in top_passengers
                ],
                "aircraft_usage": dict(sorted(
                    aircraft_usage.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]),
                "busiest_airports": dict(sorted(
                    location_usage.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10])
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "total_flights": 0,
            "flights": [],
            "locations": {},
            "error": str(e)
        }
