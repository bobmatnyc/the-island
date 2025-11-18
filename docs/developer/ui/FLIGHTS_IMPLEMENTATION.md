# Flights Map Implementation Guide

## Status: ✅ Partially Complete

### Completed:
1. ✅ Backend API endpoint created (`/api/flights`)
2. ✅ Location database with 89 airports (flight_locations.json)
3. ✅ Frontend tab navigation added
4. ✅ HTML structure for flights view added
5. ✅ Leaflet.js CDN included

### Remaining Work:

#### 1. Add CSS Styles (insert before `</style>` at line 2624):

```css
/* Flights View Styles */
.flights-header {
    margin-bottom: 24px;
}

.flights-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}

.stat-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
}

.flights-filters {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
}

.flights-filters h3 {
    margin-bottom: 16px;
    font-size: 16px;
}

.filter-row {
    display: grid;
    grid-template-columns: 2fr 2fr 1fr;
    gap: 16px;
    align-items: end;
}

.filter-group label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
}

.flight-filter-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: var(--input-bg);
    color: var(--text-primary);
    font-size: 14px;
}

.flight-details-panel {
    position: fixed;
    right: 20px;
    top: 100px;
    width: 320px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 4px 12px var(--shadow-color);
    z-index: 1000;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
}

.flight-details-panel .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
}

.flight-info {
    padding: 16px;
}

.flight-info-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-color);
}

.flight-info-row:last-child {
    border-bottom: none;
}

.flight-info-label {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 600;
}

.flight-info-value {
    font-size: 13px;
    color: var(--text-primary);
}

.passengers-list {
    margin-top: 12px;
}

.passenger-item {
    padding: 6px;
    background: var(--bg-secondary);
    border-radius: 4px;
    margin-bottom: 4px;
    font-size: 13px;
}

.top-passengers {
    margin-top: 32px;
}

.top-passengers h3 {
    margin-bottom: 16px;
}

.passengers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 12px;
}

.passenger-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.passenger-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
}

.passenger-count {
    font-size: 16px;
    font-weight: 700;
    color: var(--accent-blue);
}

/* Leaflet map dark mode support */
[data-theme="dark"] .leaflet-container {
    background: #161b22;
}

[data-theme="dark"] .leaflet-popup-content-wrapper {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

[data-theme="dark"] .leaflet-popup-tip {
    background: var(--bg-secondary);
}
```

#### 2. Add JavaScript Functions (add to app.js):

```javascript
// Flight map variables
let flightMap = null;
let flightData = null;
let flightMarkers = [];
let flightPaths = [];

// Initialize flights view
async function loadFlightsView() {
    if (!flightMap) {
        initFlightMap();
    }

    try {
        const response = await fetch('/api/flights', {
            headers: {
                'Authorization': `Bearer ${getSessionToken()}`
            }
        });

        const data = await response.json();
        flightData = data;

        // Update statistics
        document.getElementById('flights-total').textContent = data.total_flights.toLocaleString();
        document.getElementById('flights-routes').textContent = data.statistics.unique_routes || 0;
        document.getElementById('flights-airports').textContent = data.statistics.unique_locations || 0;

        if (data.statistics.top_passengers && data.statistics.top_passengers.length > 0) {
            const topPassenger = data.statistics.top_passengers[0];
            document.getElementById('flights-top-passenger').textContent =
                `${topPassenger.name} (${topPassenger.flights} flights)`;
        }

        // Populate passenger filter
        const passengerSelect = document.getElementById('flight-passenger-filter');
        const passengers = new Set();
        data.flights.forEach(flight => {
            flight.passengers.forEach(p => passengers.add(p));
        });

        Array.from(passengers).sort().forEach(passenger => {
            const option = document.createElement('option');
            option.value = passenger;
            option.textContent = passenger;
            passengerSelect.appendChild(option);
        });

        // Render top passengers
        renderTopPassengers(data.statistics.top_passengers);

        // Plot flights on map
        plotFlights(data.flights);

    } catch (error) {
        console.error('Error loading flights:', error);
    }
}

// Initialize Leaflet map
function initFlightMap() {
    const mapContainer = document.getElementById('flight-map');
    if (!mapContainer) return;

    flightMap = L.map('flight-map').setView([25, -60], 3);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(flightMap);
}

// Plot flights on map
function plotFlights(flights) {
    // Clear existing markers and paths
    flightMarkers.forEach(marker => marker.remove());
    flightPaths.forEach(path => path.remove());
    flightMarkers = [];
    flightPaths = [];

    const locations = new Map();

    // Plot flight paths
    flights.forEach(flight => {
        const origin = [flight.origin.lat, flight.origin.lon];
        const dest = [flight.destination.lat, flight.destination.lon];

        // Draw curved line between origin and destination
        const path = L.polyline([origin, dest], {
            color: '#0969da',
            weight: 1,
            opacity: 0.6
        }).addTo(flightMap);

        // Add click handler to show flight details
        path.on('click', () => showFlightDetails(flight));

        flightPaths.push(path);

        // Track locations for markers
        locations.set(flight.origin.code, flight.origin);
        locations.set(flight.destination.code, flight.destination);
    });

    // Add markers for airports
    locations.forEach((location, code) => {
        const marker = L.circleMarker([location.lat, location.lon], {
            radius: 6,
            fillColor: '#0969da',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(flightMap);

        marker.bindPopup(`<b>${location.name}</b><br>${location.city}<br>Code: ${code}`);
        flightMarkers.push(marker);
    });

    // Fit map to show all markers
    if (flightMarkers.length > 0) {
        const group = L.featureGroup(flightMarkers);
        flightMap.fitBounds(group.getBounds().pad(0.1));
    }
}

// Show flight details panel
function showFlightDetails(flight) {
    const panel = document.getElementById('flight-details');
    const content = document.getElementById('flight-info-content');

    const passengersHTML = flight.passengers.map(p =>
        `<div class="passenger-item">${p}</div>`
    ).join('');

    content.innerHTML = `
        <div class="flight-info-row">
            <span class="flight-info-label">Date</span>
            <span class="flight-info-value">${flight.date}</span>
        </div>
        <div class="flight-info-row">
            <span class="flight-info-label">Route</span>
            <span class="flight-info-value">${flight.origin.code} → ${flight.destination.code}</span>
        </div>
        <div class="flight-info-row">
            <span class="flight-info-label">Origin</span>
            <span class="flight-info-value">${flight.origin.city}</span>
        </div>
        <div class="flight-info-row">
            <span class="flight-info-label">Destination</span>
            <span class="flight-info-value">${flight.destination.city}</span>
        </div>
        <div class="flight-info-row">
            <span class="flight-info-label">Aircraft</span>
            <span class="flight-info-value">${flight.aircraft}</span>
        </div>
        <div class="passengers-list">
            <div class="flight-info-label" style="margin-bottom: 8px;">Passengers (${flight.passenger_count})</div>
            ${passengersHTML}
        </div>
    `;

    panel.style.display = 'block';
}

// Close flight details panel
function closeFlightDetails() {
    document.getElementById('flight-details').style.display = 'none';
}

// Render top passengers
function renderTopPassengers(topPassengers) {
    const container = document.getElementById('top-passengers-list');
    if (!topPassengers) return;

    container.innerHTML = topPassengers.map(p => `
        <div class="passenger-card">
            <span class="passenger-name">${p.name}</span>
            <span class="passenger-count">${p.flights}</span>
        </div>
    `).join('');
}

// Apply flight filters
async function applyFlightFilters() {
    const startDate = document.getElementById('flight-date-start').value;
    const endDate = document.getElementById('flight-date-end').value;
    const passenger = document.getElementById('flight-passenger-filter').value;

    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (passenger) params.append('passenger', passenger);

    try {
        const response = await fetch(`/api/flights?${params}`, {
            headers: {
                'Authorization': `Bearer ${getSessionToken()}`
            }
        });

        const data = await response.json();

        // Update statistics
        document.getElementById('flights-total').textContent = data.total_flights.toLocaleString();
        document.getElementById('flights-routes').textContent = data.statistics.unique_routes || 0;

        // Replot flights
        plotFlights(data.flights);

    } catch (error) {
        console.error('Error applying filters:', error);
    }
}

// Clear flight filters
function clearFlightFilters() {
    document.getElementById('flight-date-start').value = '';
    document.getElementById('flight-date-end').value = '';
    document.getElementById('flight-passenger-filter').value = '';
    loadFlightsView();
}

// Add to switchTab function (find existing function and add case)
// Add after line for 'network':
case 'flights':
    loadFlightsView();
    break;
```

#### 3. Test the Implementation

1. Start the server: `python3 app.py`
2. Navigate to the Flights tab
3. Verify:
   - Map loads correctly
   - Flight paths are visible
   - Clicking on a path shows flight details
   - Filters work properly
   - Dark mode works on the map

## File Locations

- Backend API: `/Users/masa/Projects/Epstein/server/app.py` (endpoint already added)
- Location Data: `/Users/masa/Projects/Epstein/data/metadata/flight_locations.json` (created)
- Frontend HTML: `/Users/masa/Projects/Epstein/server/web/index.html` (tab added)
- Frontend JS: `/Users/masa/Projects/Epstein/server/web/app.js` (needs functions above)
- Frontend CSS: `/Users/masa/Projects/Epstein/server/web/index.html` (needs styles above)

## Next Steps

1. Copy CSS styles into index.html before `</style>` tag
2. Copy JavaScript functions into app.js
3. Add `case 'flights': loadFlightsView(); break;` to switchTab function
4. Test the implementation
5. Optional enhancements:
   - Add timeline slider to filter by date range
   - Add heatmap for frequently visited locations
   - Add flight animation along paths
   - Add clustering for overlapping markers
