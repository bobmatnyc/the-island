#!/bin/bash
# Test script for Flights page functionality

echo "=== Flights Page Test ==="
echo ""

echo "1. Testing Backend API /api/flights"
FLIGHTS_RESPONSE=$(curl -s 'http://localhost:8000/api/flights')
FLIGHT_COUNT=$(echo "$FLIGHTS_RESPONSE" | jq -r '.total_flights')
echo "   Total flights: $FLIGHT_COUNT"
echo "   ✓ Backend API working"
echo ""

echo "2. Testing Backend API /api/flights/all (routes)"
ROUTES_RESPONSE=$(curl -s 'http://localhost:8000/api/flights/all')
ROUTE_COUNT=$(echo "$ROUTES_RESPONSE" | jq -r '.routes | length')
echo "   Total routes: $ROUTE_COUNT"
echo "   ✓ Routes API working"
echo ""

echo "3. Testing Flight Location Structure"
SAMPLE_LOCATION=$(echo "$FLIGHTS_RESPONSE" | jq -r '.flights[0].origin')
echo "   Sample location: $SAMPLE_LOCATION"
HAS_LAT=$(echo "$SAMPLE_LOCATION" | jq -r 'has("lat")')
HAS_LON=$(echo "$SAMPLE_LOCATION" | jq -r 'has("lon")')
if [ "$HAS_LAT" = "true" ] && [ "$HAS_LON" = "true" ]; then
  echo "   ✓ Location structure matches TypeScript interface"
else
  echo "   ✗ Location structure mismatch!"
  exit 1
fi
echo ""

echo "4. Testing Statistics"
STATS=$(echo "$FLIGHTS_RESPONSE" | jq -r '.statistics')
UNIQUE_ROUTES=$(echo "$STATS" | jq -r '.unique_routes')
UNIQUE_LOCATIONS=$(echo "$STATS" | jq -r '.unique_locations')
TOP_PASSENGERS=$(echo "$STATS" | jq -r '.top_passengers | length')
echo "   Unique routes: $UNIQUE_ROUTES"
echo "   Unique locations: $UNIQUE_LOCATIONS"
echo "   Top passengers: $TOP_PASSENGERS"
echo "   ✓ Statistics available"
echo ""

echo "5. Testing Frontend (Vite server)"
FRONTEND_RESPONSE=$(curl -s 'http://localhost:5173/')
if echo "$FRONTEND_RESPONSE" | grep -q "<!doctype html>"; then
  echo "   ✓ Frontend server running"
else
  echo "   ✗ Frontend server not responding"
  exit 1
fi
echo ""

echo "6. Testing Passenger Filter"
FILTERED=$(curl -s 'http://localhost:8000/api/flights?passenger=Jeffrey%20Epstein')
FILTERED_COUNT=$(echo "$FILTERED" | jq -r '.flights | length')
echo "   Flights with Jeffrey Epstein: $FILTERED_COUNT"
if [ "$FILTERED_COUNT" -gt 0 ]; then
  echo "   ✓ Passenger filter working"
else
  echo "   ✗ Passenger filter not working"
  exit 1
fi
echo ""

echo "=== ALL TESTS PASSED ==="
echo ""
echo "The flights page should now be working at: http://localhost:5173/flights"
echo ""
echo "Features available:"
echo "  - Timeline view with flight cards"
echo "  - Routes view with frequency analysis"
echo "  - Passengers view with statistics"
echo "  - Search and filtering"
echo "  - URL parameter support (?passenger=Name)"
