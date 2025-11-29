#!/usr/bin/env python3
"""
Improved flight log parser that handles the structured table format.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path("/Users/masa/Projects/Epstein/data/sources/raw_entities")
RAW_TEXT = BASE_DIR / "flight_logs_raw.txt"

def parse_flight_logs():
    """Parse structured flight log data."""

    with open(RAW_TEXT, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    trips = []
    passenger_stats = defaultdict(lambda: {"trips": 0, "routes": set(), "dates": []})

    # Skip header line
    for line in lines[2:]:  # Skip first 2 header lines
        if not line.strip():
            continue

        # Parse the structured format
        # Columns: ID, Date, Year, Aircraft Model, Tail #, Type, Seats, DEP Code, ARR Code, DEP, ARR, Flight_No, Pass #, Unique ID, First Name, Last Name, Last First, First Last, Comment, Initials, Known Data, Source

        parts = line.split()
        if len(parts) < 10:
            continue

        # Extract key fields
        try:
            # Find date pattern
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if not date_match:
                continue

            date = date_match.group(1)

            # Find tail number
            tail_match = re.search(r'(N\d{3,5}[A-Z]{0,2})', line)
            tail = tail_match.group(1) if tail_match else ""

            # Find departure and arrival codes (3-letter airport codes)
            airport_matches = re.findall(r'\b([A-Z]{3})\b', line)
            dep = airport_matches[0] if len(airport_matches) > 0 else ""
            arr = airport_matches[1] if len(airport_matches) > 1 else ""

            # Extract passenger name - look for pattern "First Name Last Name"
            # The format has columns: First Name, Last Name, Last First, First Last
            # Find "Flight Log" at end and work backwards

            if "Flight Log" not in line:
                continue

            # Split on "Flight Log" and get the part before it
            before_source = line.split("Flight Log")[0]

            # Look for name patterns - capitalize words before initials
            # Pattern: "FirstName LastName LastName, FirstName FirstName LastName Initials"

            # Extract the "First Last" column which is most reliable
            # It appears after "Last, First" and before initials

            # Use regex to find name in "First Last" format
            name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z]{1,3})\s+(?:Yes|No)\s+Flight Log', line)

            if name_match:
                full_name = name_match.group(1).strip()
                initials = name_match.group(2).strip()
            else:
                # Try alternate pattern for names like "Female (1)", "Male (3)", etc.
                alt_match = re.search(r'((?:Female|Male|Nanny)\s*\(\d+\))\s+\1\s+([?])\s+No\s+Flight Log', line)
                if alt_match:
                    full_name = alt_match.group(1).strip()
                    initials = "?"
                else:
                    # Try to extract from columns manually
                    # Look for pattern with two name columns before initials
                    cols_match = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+\2,\s+\1\s+\1\s+\2\s+([A-Z?]{1,3})\s+(?:Yes|No)', line)
                    if cols_match:
                        first = cols_match.group(1)
                        last = cols_match.group(2)
                        full_name = f"{first} {last}"
                        initials = cols_match.group(3)
                    else:
                        continue

            # Skip non-person entries
            if not full_name or full_name in ["Unknown", "Aircraft Model", "Aircraft Tail", "Aircraft Type", "First Name", "Last Name", "Comment Initials", "Known Data"]:
                continue

            trip = {
                "date": date,
                "tail_number": tail,
                "departure": dep,
                "arrival": arr,
                "passenger": full_name,
                "initials": initials
            }

            trips.append(trip)

            # Update passenger stats
            passenger_stats[full_name]["trips"] += 1
            passenger_stats[full_name]["routes"].add(f"{dep}-{arr}")
            passenger_stats[full_name]["dates"].append(date)

        except Exception as e:
            # Skip problematic lines
            continue

    return trips, passenger_stats

def create_flight_logs_markdown(trips, passenger_stats):
    """Create comprehensive flight logs markdown."""

    total_trips = len(trips)
    unique_passengers = len(passenger_stats)

    # Get date range
    dates = [t["date"] for t in trips if t.get("date")]
    if dates:
        first_date = min(dates)
        last_date = max(dates)
    else:
        first_date = last_date = "Unknown"

    md = f"""---
source_type: "flight_log"
source_name: "Epstein Flight Logs (Unredacted)"
source_url: "Court documents"
download_date: "{datetime.now().strftime('%Y-%m-%d')}"
total_trips: {total_trips}
unique_passengers: {unique_passengers}
date_range: "{first_date} to {last_date}"
extraction_method: "structured_table_parse"
---

# Epstein Flight Logs (Unredacted)

## Metadata
- **Total Flight Records**: {total_trips}
- **Unique Passengers**: {unique_passengers}
- **Date Range**: {first_date} to {last_date}
- **Aircraft**: Multiple tail numbers including N908JE

## Frequent Flyers (Top 50)

| Rank | Passenger Name | Total Trips | Unique Routes |
|------|---------------|-------------|---------------|
"""

    # Add top frequent flyers
    ranked = sorted(passenger_stats.items(), key=lambda x: x[1]["trips"], reverse=True)

    for i, (passenger, stats) in enumerate(ranked[:50], 1):
        trips_count = stats["trips"]
        routes_count = len(stats["routes"])
        md += f"| {i} | {passenger} | {trips_count} | {routes_count} |\n"

    # Add detailed passenger sections
    md += "\n## Passenger Details\n\n"

    for passenger, stats in sorted(ranked[:50], key=lambda x: x[1]["trips"], reverse=True):
        trips_count = stats["trips"]
        routes = sorted(stats["routes"])
        dates_list = sorted(set(stats["dates"]))

        md += f"### {passenger}\n\n"
        md += f"- **Total Trips**: {trips_count}\n"
        md += f"- **Unique Routes**: {len(routes)}\n"
        md += f"- **Date Range**: {dates_list[0]} to {dates_list[-1]}\n"

        if len(routes) <= 10:
            md += f"- **Routes**: {', '.join(routes)}\n"
        else:
            md += f"- **Common Routes**: {', '.join(routes[:10])} ... and {len(routes)-10} more\n"

        md += "\n"

    # Add sample trip log
    md += "## Sample Flight Records (First 50)\n\n"

    for trip in trips[:50]:
        md += f"- **{trip['date']}**: {trip['tail_number']} | {trip['departure']} → {trip['arrival']} | {trip['passenger']}\n"

    if len(trips) > 50:
        md += f"\n*... and {len(trips) - 50} more flight records*\n"

    return md

def main():
    print("Parsing flight logs...")

    trips, passenger_stats = parse_flight_logs()

    print(f"Found {len(trips)} flight records")
    print(f"Found {len(passenger_stats)} unique passengers")

    # Create markdown
    md = create_flight_logs_markdown(trips, passenger_stats)
    output_file = BASE_DIR / "flight_logs.md"
    output_file.write_text(md)

    print(f"Saved to {output_file}")

    # Save passenger statistics as JSON
    stats_json = {
        "total_flights": len(trips),
        "unique_passengers": len(passenger_stats),
        "passengers": {
            name: {
                "trips": stats["trips"],
                "routes": list(stats["routes"]),
                "first_flight": min(stats["dates"]),
                "last_flight": max(stats["dates"])
            }
            for name, stats in passenger_stats.items()
        }
    }

    json_file = BASE_DIR / "flight_logs_stats.json"
    with open(json_file, 'w') as f:
        json.dump(stats_json, f, indent=2)

    print(f"Saved statistics to {json_file}")

    # Print top 20 frequent flyers
    print("\nTop 20 Frequent Flyers:")
    for i, (passenger, stats) in enumerate(sorted(passenger_stats.items(), key=lambda x: x[1]["trips"], reverse=True)[:20], 1):
        print(f"  {i}. {passenger}: {stats['trips']} trips")

if __name__ == "__main__":
    main()
