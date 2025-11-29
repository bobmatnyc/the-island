#!/usr/bin/env python3
"""
Test Authentication System

Verifies cookie-based authentication works correctly.
"""

import requests
from requests.auth import HTTPBasicAuth


BASE_URL = "http://localhost:8000"

def test_root_redirect():
    """Test that root redirects to login (no HTTP Basic Auth popup)"""
    print("1. Testing root redirect...")
    response = requests.get(f"{BASE_URL}/", allow_redirects=False)

    if response.status_code == 307 and "/static/login.html" in response.headers.get("location", ""):
        print("   ✅ Root redirects to login page (no auth required)")
        return True
    print(f"   ❌ Expected redirect to login, got {response.status_code}")
    return False


def test_login_with_cookies():
    """Test login sets HTTP-only cookie"""
    print("\n2. Testing login with cookie...")

    # NOTE: Replace with actual credentials from .credentials file
    login_data = {
        "username": "admin",  # Change this
        "password": "password",  # Change this
        "remember": True,
        "tos_accepted": True,
        "browser_data": {
            "user_agent": "test-client",
            "screen_resolution": "1920x1080",
            "timezone": "America/New_York",
            "language": "en-US"
        }
    }

    session = requests.Session()
    response = session.post(f"{BASE_URL}/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Login successful: {data.get('username')}")

        # Check if cookie was set
        if "session_token" in session.cookies:
            print("   ✅ Session cookie set")
            return session
        print("   ❌ No session cookie found")
        return None
    print(f"   ❌ Login failed: {response.status_code} - {response.text}")
    return None


def test_verify_session(session):
    """Test session verification endpoint"""
    print("\n3. Testing session verification...")

    response = session.get(f"{BASE_URL}/api/verify-session")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Session verified: {data.get('username')}")
        return True
    print(f"   ❌ Verification failed: {response.status_code}")
    return False


def test_api_access(session):
    """Test API access with cookie"""
    print("\n4. Testing API access...")

    response = session.get(f"{BASE_URL}/api/stats")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API access granted: {data.get('total_entities')} entities")
        return True
    print(f"   ❌ API access denied: {response.status_code}")
    return False


def test_http_basic_auth():
    """Test HTTP Basic Auth still works for API clients"""
    print("\n5. Testing HTTP Basic Auth fallback...")

    # NOTE: Replace with actual credentials
    auth = HTTPBasicAuth("admin", "password")  # Change this
    response = requests.get(f"{BASE_URL}/api/stats", auth=auth)

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Basic Auth works: {data.get('total_entities')} entities")
        return True
    print(f"   ❌ Basic Auth failed: {response.status_code}")
    return False


def test_logout(session):
    """Test logout clears cookie"""
    print("\n6. Testing logout...")

    response = session.post(f"{BASE_URL}/api/logout")

    if response.status_code == 200:
        print("   ✅ Logout successful")

        # Verify cookie was cleared
        if "session_token" not in session.cookies:
            print("   ✅ Session cookie cleared")
            return True
        print("   ⚠️  Session cookie still present")
        return False
    print(f"   ❌ Logout failed: {response.status_code}")
    return False


def main():
    print("=" * 60)
    print("Authentication System Test")
    print("=" * 60)

    # Test 1: Root redirect
    test_root_redirect()

    # Test 2: Login
    session = test_login_with_cookies()
    if not session:
        print("\n❌ Login failed, cannot continue tests")
        return

    # Test 3: Verify session
    test_verify_session(session)

    # Test 4: API access with cookie
    test_api_access(session)

    # Test 5: HTTP Basic Auth
    test_http_basic_auth()

    # Test 6: Logout
    test_logout(session)

    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
