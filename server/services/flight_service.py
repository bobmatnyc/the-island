"""
Flight Service - Business logic for flight log operations

Design Decision: Centralized Flight Data Management
Rationale: All flight-related filtering, searching, and statistics
consolidated in one service for consistency and maintainability.

Handles:
- Flight filtering (passenger, route, date range)
- Route grouping and frequency analysis
- Passenger statistics
- Location geocoding integration
"""

import json
from pathlib import Path
from typing import Optional


class FlightService:
    """Service for flight data operations"""

    def __init__(self, data_path: Path):
        """Initialize flight service

        Args:
            data_path: Path to data directory
        """
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"
        self.md_dir = data_path / "md"

        # Data caches
        self.flight_data: dict = {}
        self.locations_db: dict = {}

        # Load data
        self.load_data()

    def load_data(self):
        """Load flight logs and location database"""
        # Load flight data
        flight_data_path = self.md_dir / "entities/flight_logs_by_flight.json"
        if flight_data_path.exists():
            with open(flight_data_path) as f:
                self.flight_data = json.load(f)

        # Load location database
        locations_path = self.metadata_dir / "flight_locations.json"
        if locations_path.exists():
            with open(locations_path) as f:
                self.locations_db = json.load(f)

    def parse_date_for_sort(self, date_str: str) -> str:
        """Convert MM/DD/YYYY to YYYY-MM-DD for sorting

        Args:
            date_str: Date string in MM/DD/YYYY format

        Returns:
            Date string in YYYY-MM-DD format
        """
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

    def get_all_flights(
        self,
        passenger: Optional[str] = None,
        from_airport: Optional[str] = None,
        to_airport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get flights with optional filtering

        Args:
            passenger: Filter by passenger name (partial match)
            from_airport: Filter by origin airport code
            to_airport: Filter by destination airport code
            start_date: Filter by start date (MM/DD/YYYY)
            end_date: Filter by end date (MM/DD/YYYY)
            limit: Results per page
            offset: Pagination offset

        Returns:
            {
                "flights": List of matching flights,
                "total": Total matching flights,
                "filters": {
                    "passengers": Unique passengers,
                    "airports": Unique airport codes
                }
            }
        """
        flights = self.flight_data.get("flights", [])

        # Filter by passenger
        if passenger:
            passenger_lower = passenger.lower()
            flights = [
                f
                for f in flights
                if any(passenger_lower in p.lower() for p in f.get("passengers", []))
            ]

        # Filter by origin airport
        if from_airport:
            flights = [f for f in flights if f.get("route", "").startswith(from_airport + "-")]

        # Filter by destination airport
        if to_airport:
            flights = [f for f in flights if f.get("route", "").endswith("-" + to_airport)]

        # Filter by date range
        if start_date or end_date:
            filtered = []
            for flight in flights:
                flight_date = self.parse_date_for_sort(flight.get("date", ""))
                if start_date and flight_date < self.parse_date_for_sort(start_date):
                    continue
                if end_date and flight_date > self.parse_date_for_sort(end_date):
                    continue
                filtered.append(flight)
            flights = filtered

        # Get unique passengers and airports for filters
        unique_passengers = set()
        unique_airports = set()
        for flight in self.flight_data.get("flights", []):
            unique_passengers.update(flight.get("passengers", []))
            route = flight.get("route", "")
            if "-" in route:
                origin, dest = route.split("-", 1)
                unique_airports.add(origin)
                unique_airports.add(dest)

        # Sort by date
        flights.sort(key=lambda f: self.parse_date_for_sort(f.get("date", "")))

        # Paginate
        total = len(flights)
        flights_page = flights[offset : offset + limit]

        return {
            "flights": flights_page,
            "total": total,
            "offset": offset,
            "limit": limit,
            "filters": {
                "passengers": sorted(unique_passengers),
                "airports": sorted(unique_airports),
            },
        }

    def get_flights_grouped_by_route(self) -> dict:
        """Get all flights grouped by route for map visualization

        Returns:
            {
                "routes": [{origin, destination, flights[], frequency}],
                "total_flights": Total count,
                "unique_routes": Unique routes count,
                "unique_passengers": Unique passengers count,
                "date_range": {start, end},
                "airports": Location database
            }
        """
        all_flights = self.flight_data.get("flights", [])
        airports = self.locations_db.get("airports", {})

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
                    "origin": {"code": origin_code, **origin_data},
                    "destination": {"code": dest_code, **dest_data},
                    "flights": [],
                }

            # Add flight to route
            route_map[route_key]["flights"].append(
                {
                    "id": flight.get("id"),
                    "date": flight_date,
                    "passengers": flight.get("passengers", []),
                    "passenger_count": flight.get(
                        "passenger_count", len(flight.get("passengers", []))
                    ),
                    "aircraft": flight.get("tail_number", ""),
                }
            )

        # Convert route_map to array with frequency
        routes = []
        for route_key, route_data in route_map.items():
            routes.append(
                {
                    "origin": route_data["origin"],
                    "destination": route_data["destination"],
                    "flights": route_data["flights"],
                    "frequency": len(route_data["flights"]),
                }
            )

        # Sort routes by frequency (most traveled routes first)
        routes.sort(key=lambda r: r["frequency"], reverse=True)

        # Calculate date range
        date_range = {}
        if all_dates:
            sorted_dates = sorted(all_dates, key=lambda d: self.parse_date_for_sort(d))
            date_range = {"start": sorted_dates[0], "end": sorted_dates[-1]}

        return {
            "routes": routes,
            "total_flights": len(all_flights),
            "unique_routes": len(routes),
            "unique_passengers": len(unique_passengers_set),
            "date_range": date_range,
            "airports": airports,
        }

    def get_flights_by_passenger(self, passenger_name: str) -> dict:
        """Get all flights for a specific passenger

        Args:
            passenger_name: Passenger name (partial match)

        Returns:
            {
                "passenger": Passenger name,
                "flights": List of flights,
                "total_flights": Count,
                "routes": Unique routes,
                "date_range": {start, end}
            }
        """
        passenger_lower = passenger_name.lower()
        all_flights = self.flight_data.get("flights", [])

        # Find matching flights
        matching_flights = [
            f
            for f in all_flights
            if any(passenger_lower in p.lower() for p in f.get("passengers", []))
        ]

        # Get unique routes
        routes = {f.get("route", "") for f in matching_flights}

        # Get date range
        dates = [f.get("date", "") for f in matching_flights if f.get("date")]
        date_range = {}
        if dates:
            sorted_dates = sorted(dates, key=lambda d: self.parse_date_for_sort(d))
            date_range = {"start": sorted_dates[0], "end": sorted_dates[-1]}

        # Sort by date
        matching_flights.sort(key=lambda f: self.parse_date_for_sort(f.get("date", "")))

        return {
            "passenger": passenger_name,
            "flights": matching_flights,
            "total_flights": len(matching_flights),
            "routes": sorted(routes),
            "date_range": date_range,
        }

    def get_statistics(self) -> dict:
        """Get flight statistics

        Returns:
            {
                "total_flights": Total count,
                "unique_passengers": Count,
                "unique_routes": Count,
                "unique_airports": Count,
                "date_range": {start, end},
                "most_frequent_passenger": {name, count},
                "most_frequent_route": {route, count}
            }
        """
        all_flights = self.flight_data.get("flights", [])

        # Unique passengers
        unique_passengers = set()
        for flight in all_flights:
            unique_passengers.update(flight.get("passengers", []))

        # Unique routes and airports
        unique_routes = set()
        unique_airports = set()
        for flight in all_flights:
            route = flight.get("route", "")
            unique_routes.add(route)
            if "-" in route:
                origin, dest = route.split("-", 1)
                unique_airports.add(origin)
                unique_airports.add(dest)

        # Date range
        dates = [f.get("date", "") for f in all_flights if f.get("date")]
        date_range = {}
        if dates:
            sorted_dates = sorted(dates, key=lambda d: self.parse_date_for_sort(d))
            date_range = {"start": sorted_dates[0], "end": sorted_dates[-1]}

        # Most frequent passenger
        passenger_counts = {}
        for flight in all_flights:
            for passenger in flight.get("passengers", []):
                passenger_counts[passenger] = passenger_counts.get(passenger, 0) + 1

        most_frequent_passenger = {}
        if passenger_counts:
            top_passenger = max(passenger_counts.items(), key=lambda x: x[1])
            most_frequent_passenger = {"name": top_passenger[0], "count": top_passenger[1]}

        # Most frequent route
        route_counts = {}
        for flight in all_flights:
            route = flight.get("route", "")
            route_counts[route] = route_counts.get(route, 0) + 1

        most_frequent_route = {}
        if route_counts:
            top_route = max(route_counts.items(), key=lambda x: x[1])
            most_frequent_route = {"route": top_route[0], "count": top_route[1]}

        return {
            "total_flights": len(all_flights),
            "unique_passengers": len(unique_passengers),
            "unique_routes": len(unique_routes),
            "unique_airports": len(unique_airports),
            "date_range": date_range,
            "most_frequent_passenger": most_frequent_passenger,
            "most_frequent_route": most_frequent_route,
        }
