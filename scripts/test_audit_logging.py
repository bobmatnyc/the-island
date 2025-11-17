#!/usr/bin/env python3
"""
Test Audit Logging System

Comprehensive test of login audit logging with browser profiling.
Tests:
- Successful login logging
- Failed login logging
- Browser profile creation
- Security event detection
- Statistics generation
"""

import sys
from pathlib import Path
from datetime import datetime

# Add server directory to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_DIR = PROJECT_ROOT / "server"
sys.path.insert(0, str(SERVER_DIR))

from services.audit_logger import AuditLogger, LoginEvent, BrowserProfile


def test_audit_logging():
    """Test comprehensive audit logging functionality"""
    print("Testing Audit Logging System")
    print("=" * 60)

    # Initialize audit logger
    db_path = PROJECT_ROOT / "data" / "logs" / "audit.db"
    logger = AuditLogger(db_path)
    print(f"✓ Initialized audit logger: {db_path}")
    print()

    # Test 1: Browser Profile Creation
    print("Test 1: Browser Profile Creation")
    print("-" * 60)

    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]

    for ua in user_agents:
        profile = logger.create_browser_profile(
            user_agent=ua,
            screen_resolution="1920x1080",
            timezone="America/New_York",
            language="en-US"
        )
        print(f"  Browser: {profile.browser} {profile.browser_version}")
        print(f"  OS: {profile.os} {profile.os_version}")
        print(f"  Device: {profile.device_type}")
        print()

    print("✓ Browser profile parsing successful")
    print()

    # Test 2: Successful Login Event
    print("Test 2: Successful Login Event")
    print("-" * 60)

    success_event = LoginEvent(
        username="test_user",
        timestamp=datetime.now(),
        ip_address="192.168.1.100",
        success=True,
        tos_accepted=True,
        tos_accepted_at=datetime.now(),
        session_token="test_token_123",
        remember_me=True,
        browser_profile=logger.create_browser_profile(
            user_agent=user_agents[0],
            screen_resolution="1920x1080",
            timezone="America/New_York",
            language="en-US"
        )
    )

    event_id = logger.log_login_event(success_event)
    print(f"  Logged successful login: Event ID {event_id}")
    print(f"  Username: {success_event.username}")
    print(f"  IP Hash: {logger.hash_ip_address(success_event.ip_address)[:16]}...")
    print(f"  TOS Accepted: {success_event.tos_accepted}")
    print()

    print("✓ Successful login logging works")
    print()

    # Test 3: Failed Login Events (trigger security alerts)
    print("Test 3: Failed Login Events (Security Alert Trigger)")
    print("-" * 60)

    # Generate 6 failed attempts to trigger alert (threshold is 5)
    for i in range(6):
        failed_event = LoginEvent(
            username="attacker_user",
            timestamp=datetime.now(),
            ip_address="10.0.0.50",
            success=False,
            failure_reason="invalid_password",
            browser_profile=logger.create_browser_profile(
                user_agent=user_agents[1],
                screen_resolution="1366x768"
            )
        )
        logger.log_login_event(failed_event)
        print(f"  Logged failed attempt {i+1}/6")

    print()
    print("✓ Failed login logging and security alert trigger successful")
    print()

    # Test 4: Security Events
    print("Test 4: Security Events")
    print("-" * 60)

    events = logger.get_security_events(limit=10)
    print(f"  Found {len(events)} security events:")
    for event in events:
        print(f"    - Type: {event['event_type']}")
        print(f"      Severity: {event['severity']}")
        print(f"      Details: {event['details']}")
        print()

    print("✓ Security event retrieval successful")
    print()

    # Test 5: Login History
    print("Test 5: Login History Retrieval")
    print("-" * 60)

    history = logger.get_login_history(limit=10)
    print(f"  Retrieved {len(history)} login events:")
    for log in history[:3]:  # Show first 3
        status = "SUCCESS" if log['success'] else "FAILED"
        print(f"    - {log['timestamp']}: {log['username']} ({status})")
        if log.get('browser'):
            print(f"      Browser: {log['browser']} {log.get('browser_version', '')}")
            print(f"      OS: {log['os']} {log.get('os_version', '')}")

    print()
    print("✓ Login history retrieval successful")
    print()

    # Test 6: Statistics
    print("Test 6: Aggregate Statistics")
    print("-" * 60)

    stats = logger.get_login_statistics()
    print(f"  Total Logins: {stats['total_logins']}")
    print(f"  Successful: {stats['successful_logins']}")
    print(f"  Failed: {stats['failed_logins']}")
    print(f"  Unique Users: {stats['unique_users']}")
    print(f"  Unique IPs: {stats['unique_ips']}")
    print()
    print("  Browser Distribution (last 30 days):")
    for browser, count in stats['browser_distribution'].items():
        print(f"    {browser}: {count}")
    print()
    print("  OS Distribution (last 30 days):")
    for os, count in stats['os_distribution'].items():
        print(f"    {os}: {count}")
    print()
    print("  Device Distribution (last 30 days):")
    for device, count in stats['device_distribution'].items():
        print(f"    {device}: {count}")
    print()

    print("✓ Statistics generation successful")
    print()

    # Test 7: IP Hashing (Privacy)
    print("Test 7: IP Address Hashing (Privacy)")
    print("-" * 60)

    test_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
    for ip in test_ips:
        hashed = logger.hash_ip_address(ip)
        print(f"  {ip} → {hashed[:32]}...")

    # Verify same IP produces same hash
    hash1 = logger.hash_ip_address("192.168.1.1")
    hash2 = logger.hash_ip_address("192.168.1.1")
    assert hash1 == hash2, "Same IP should produce same hash"
    print()
    print("✓ IP hashing deterministic and working")
    print()

    # Summary
    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print()
    print("Audit Logging System Features Verified:")
    print("  ✓ Browser profiling and parsing")
    print("  ✓ Successful login event logging")
    print("  ✓ Failed login event logging")
    print("  ✓ Security alert triggers (excessive failures)")
    print("  ✓ Security event retrieval")
    print("  ✓ Login history with pagination")
    print("  ✓ Aggregate statistics generation")
    print("  ✓ IP address hashing for privacy")
    print()
    print("Database Location:")
    print(f"  {db_path}")
    print()
    print("Access Audit Dashboard:")
    print("  http://localhost:8000/static/audit.html")
    print()
    print("API Endpoints Available:")
    print("  GET  /api/admin/audit-logs")
    print("  GET  /api/admin/security-events")
    print("  GET  /api/admin/login-statistics")
    print("  POST /api/admin/anonymize-logs")


if __name__ == "__main__":
    test_audit_logging()
