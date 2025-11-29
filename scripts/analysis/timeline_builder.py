#!/usr/bin/env python3
"""
Timeline Builder
Extracts dates from documents and creates chronological timeline
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md"
METADATA_DIR = DATA_DIR / "metadata"


class TimelineBuilder:
    """Build chronological timeline from documents"""

    # Date patterns to match
    DATE_PATTERNS = [
        # MM/DD/YYYY or M/D/YYYY
        (r"(\d{1,2})/(\d{1,2})/(\d{4})", lambda m: f"{m[3]}-{m[1]:0>2}-{m[2]:0>2}"),
        # Month DD, YYYY
        (
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
            lambda m: f"{m[3]}-{TimelineBuilder.month_to_num(m[1]):0>2}-{m[2]:0>2}",
        ),
        # YYYY-MM-DD
        (r"(\d{4})-(\d{2})-(\d{2})", lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
        # DD Month YYYY
        (
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            lambda m: f"{m[3]}-{TimelineBuilder.month_to_num(m[2]):0>2}-{m[1]:0>2}",
        ),
    ]

    @staticmethod
    def month_to_num(month: str) -> int:
        """Convert month name to number"""
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        return months.get(month.lower(), 1)

    def __init__(self):
        """Initialize timeline builder"""
        self.events = []
        self.date_index = defaultdict(list)

    def extract_dates_from_text(self, text: str, doc_path: str) -> list[tuple[str, int]]:
        """
        Extract dates from text

        Returns:
            List of (date_string, position) tuples
        """
        dates_found = []

        for pattern, formatter in self.DATE_PATTERNS:
            for match in re.finditer(pattern, text):
                try:
                    # Format as YYYY-MM-DD
                    formatted_date = formatter(match.groups())

                    # Validate date
                    datetime.strptime(formatted_date, "%Y-%m-%d")

                    dates_found.append((formatted_date, match.start()))
                except (ValueError, IndexError):
                    continue

        return dates_found

    def extract_context(self, text: str, position: int, context_size: int = 200) -> str:
        """Extract text context around a position"""
        start = max(0, position - context_size)
        end = min(len(text), position + context_size)
        context = text[start:end].strip()

        # Clean up
        context = re.sub(r"\s+", " ", context)
        return context

    def process_document(self, doc_path: Path) -> list[dict]:
        """
        Process a document and extract timeline events

        Returns:
            List of timeline events
        """
        try:
            text = doc_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        dates = self.extract_dates_from_text(text, str(doc_path))

        events = []
        for date_str, position in dates:
            context = self.extract_context(text, position)

            event = {
                "date": date_str,
                "document": str(doc_path.relative_to(PROJECT_ROOT)),
                "context": context,
                "position": position,
            }

            events.append(event)

        return events

    def build_timeline(self, source_dirs: list[Path]) -> list[dict]:
        """
        Build timeline from multiple source directories

        Args:
            source_dirs: List of directories to scan for markdown files

        Returns:
            Sorted list of timeline events
        """
        print("Building timeline from documents...")

        all_events = []

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            md_files = list(source_dir.glob("**/*.md"))
            print(f"  Processing {len(md_files)} files from {source_dir.name}...")

            for md_file in md_files:
                events = self.process_document(md_file)
                all_events.extend(events)

        print(f"  Found {len(all_events)} dated events")

        # Sort by date
        all_events.sort(key=lambda e: e["date"])

        # Build date index
        for event in all_events:
            self.date_index[event["date"]].append(event)

        self.events = all_events
        return all_events

    def export_timeline(self, output_path: Path):
        """Export timeline to JSON"""
        timeline_data = {
            "generated": "2025-11-17T00:15:00",
            "total_events": len(self.events),
            "date_range": {
                "earliest": self.events[0]["date"] if self.events else None,
                "latest": self.events[-1]["date"] if self.events else None,
            },
            "events": self.events,
        }

        with open(output_path, "w") as f:
            json.dump(timeline_data, f, indent=2)

        print(f"\n✓ Exported timeline: {output_path}")

    def generate_summary(self) -> str:
        """Generate timeline summary"""
        if not self.events:
            return "No dated events found"

        # Group by year
        year_counts = defaultdict(int)
        for event in self.events:
            year = event["date"][:4]
            year_counts[year] += 1

        # Find most active periods
        sorted_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        report = [
            "=" * 70,
            "TIMELINE SUMMARY",
            "=" * 70,
            "",
            f"Total dated events: {len(self.events)}",
            f"Date range: {self.events[0]['date']} to {self.events[-1]['date']}",
            f"Unique dates: {len(self.date_index)}",
            "",
            "TOP 10 MOST ACTIVE YEARS:",
            "-" * 70,
        ]

        for year, count in sorted_years:
            report.append(f"  {year}: {count:4d} events")

        report.extend(["", "EARLIEST EVENTS:", "-" * 70])

        for event in self.events[:10]:
            context_preview = (
                event["context"][:80] + "..." if len(event["context"]) > 80 else event["context"]
            )
            report.append(f"  {event['date']}: {context_preview}")

        report.extend(["", "MOST RECENT EVENTS:", "-" * 70])

        for event in self.events[-10:]:
            context_preview = (
                event["context"][:80] + "..." if len(event["context"]) > 80 else event["context"]
            )
            report.append(f"  {event['date']}: {context_preview}")

        return "\n".join(report)


def main():
    """Build timeline"""
    print("=" * 70)
    print("TIMELINE BUILDER")
    print("=" * 70)

    builder = TimelineBuilder()

    # Scan entity documents and any OCR output
    source_dirs = [
        MD_DIR / "entities",
        MD_DIR / "house_oversight_nov2025",
        MD_DIR / "giuffre_maxwell",
        MD_DIR / "documentcloud_6506732",
        MD_DIR / "documentcloud_6250471",
    ]

    builder.build_timeline(source_dirs)

    # Export
    timeline_path = METADATA_DIR / "timeline.json"
    builder.export_timeline(timeline_path)

    # Generate summary
    summary = builder.generate_summary()
    summary_path = METADATA_DIR / "timeline_summary.txt"
    summary_path.write_text(summary)

    print(f"✓ Saved summary: {summary_path}")
    print("\n" + summary)

    print("\n" + "=" * 70)
    print("TIMELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
