#!/usr/bin/env python3
"""
Initialize Audit Database - Setup audit logging database and indexes

Creates SQLite database for comprehensive login audit logging:
- Login events table with browser profiling
- Browser profiles table (deduplicated fingerprints)
- Security events table for anomaly detection
- Optimized indexes for query performance

Usage:
    python3 scripts/database/init_audit_db.py
"""

import sys
from pathlib import Path


# Add server directory to path for imports
SERVER_DIR = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(SERVER_DIR))

from services.audit_logger import AuditLogger


def main():
    """Initialize audit database with schema and indexes."""
    # Database path: data/logs/audit.db
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "logs" / "audit.db"

    print(f"Initializing audit database at: {db_path}")
    print()

    # Create audit logger (initializes database)
    logger = AuditLogger(db_path)

    print("✓ Database created successfully")
    print()
    print("Schema created:")
    print("  - login_events (with indexes on username, IP, timestamp)")
    print("  - browser_profiles (with fingerprint hash index)")
    print("  - security_events (with type and username indexes)")
    print()
    print(f"Database location: {db_path}")
    print(f"Database size: {db_path.stat().st_size if db_path.exists() else 0} bytes")
    print()
    print("Ready for audit logging!")


if __name__ == "__main__":
    main()
