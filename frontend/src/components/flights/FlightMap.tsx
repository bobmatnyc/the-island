import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import { FlightRoute } from './FlightRoute';
import { AirportMarker } from './AirportMarker';
import { FlightFilters } from './FlightFilters';
import { FlightStats } from './FlightStats';
import { PassengerPopup } from './PassengerPopup';
import type { FlightRoute as FlightRouteType, FlightLocation } from '@/lib/api';

// Fix Leaflet default icon paths for Vite bundler
const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

/**
 * FlightMap Component
 *
 * Design Decision: Interactive map using Leaflet.js with filters above map
 * Rationale: Leaflet provides excellent performance for 177 routes with minimal overhead.
 * Selected dark CartoDB tiles for consistency with app theme.
 *
 * Layout Architecture:
 * - Filters positioned above map (not overlaying) for better UX
 * - Stats panel overlays bottom-right corner of map (collapsible)
 * - Passenger popup uses high z-index (9999) to appear above Leaflet
 *
 * Performance:
 * - Renders 177 polylines + 89 markers = ~440 DOM elements
 * - Expected initial load: <2 seconds
 * - Map interaction: Smooth 60fps on modern browsers
 *
 * Z-Index Hierarchy:
 * - Map container: 0 (explicit lower layer)
 * - Leaflet map: default (~400-500, contained within z-0 parent)
 * - Filter dropdown: 600 (above map)
 * - Stats overlay: 1000 (within map container)
 * - Popup overlay: 9998 (dialog backdrop)
 * - Popup content: 9999 (dialog)
 *
 * Trade-offs:
 * - Phase 1: Straight lines (not curved geodesic paths) for simplicity
 * - Deferred plane icon markers to Phase 2
 * - Client-side filtering sufficient for current data scale
 *
 * Future Enhancement: Add curved paths with leaflet.curve plugin in Phase 2
 */

interface FlightMapProps {
  routes: FlightRouteType[];
  airports: Record<string, FlightLocation>;
  dateRange: { start: string; end: string };
}

interface SelectedRoute {
  route: FlightRouteType;
  position: { x: number; y: number };
}

export function FlightMap({ routes, airports, dateRange }: FlightMapProps) {
  const [selectedRoute, setSelectedRoute] = useState<SelectedRoute | null>(null);
  const [passengerFilter, setPassengerFilter] = useState<string>('__ALL__');
  const [filteredRoutes, setFilteredRoutes] = useState<FlightRouteType[]>(routes);
  const [uniquePassengers, setUniquePassengers] = useState<string[]>([]);

  // Extract unique passengers from all routes
  useEffect(() => {
    const passengers = new Set<string>();
    routes.forEach(route => {
      route.flights.forEach(flight => {
        flight.passengers.forEach(passenger => passengers.add(passenger));
      });
    });
    setUniquePassengers(Array.from(passengers).sort());
  }, [routes]);

  // Apply passenger filter
  useEffect(() => {
    if (!passengerFilter || passengerFilter === '__ALL__') {
      setFilteredRoutes(routes);
      return;
    }

    const filtered = routes.filter(route =>
      route.flights.some(flight =>
        flight.passengers.some(passenger =>
          passenger.toLowerCase().includes(passengerFilter.toLowerCase())
        )
      )
    );
    setFilteredRoutes(filtered);
  }, [passengerFilter, routes]);

  const handleRouteClick = (route: FlightRouteType, event: L.LeafletMouseEvent) => {
    setSelectedRoute({
      route,
      position: { x: event.originalEvent.clientX, y: event.originalEvent.clientY }
    });
  };

  const handleClosePopup = () => {
    setSelectedRoute(null);
  };

  const handleClearFilters = () => {
    setPassengerFilter('');
  };

  // Calculate statistics for filtered routes
  const stats = {
    totalFlights: filteredRoutes.reduce((sum, route) => sum + route.frequency, 0),
    uniqueRoutes: filteredRoutes.length,
    uniquePassengers: new Set(
      filteredRoutes.flatMap(route =>
        route.flights.flatMap(flight => flight.passengers)
      )
    ).size,
    dateRange
  };

  return (
    <div className="space-y-4">
      {/* Filter bar above map */}
      <FlightFilters
        passengers={uniquePassengers}
        selectedPassenger={passengerFilter}
        onPassengerChange={setPassengerFilter}
        onClearFilters={handleClearFilters}
      />

      {/* Map container with stats overlay */}
      <div className="relative w-full h-[calc(100vh-300px)] rounded-lg overflow-hidden z-0">
        <MapContainer
          center={[20, 0]}
          zoom={3}
          minZoom={2}
          maxZoom={10}
          zoomControl={false}
          className="w-full h-full"
          style={{ background: '#0d1117' }}
        >
          {/* Dark theme tiles */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            subdomains={['a', 'b', 'c', 'd']}
            maxZoom={20}
          />

          {/* Zoom controls (bottom-left) */}
          <ZoomControl position="bottomleft" />

          {/* Flight routes */}
          {filteredRoutes.map((route, idx) => (
            <FlightRoute
              key={`${route.origin.code}-${route.destination.code}-${idx}`}
              route={route}
              onClick={handleRouteClick}
            />
          ))}

          {/* Airport markers */}
          {Object.entries(airports).map(([code, airport]) => (
            <AirportMarker
              key={code}
              code={code}
              position={[airport.lat, airport.lon]}
              name={airport.name}
              city={airport.city}
            />
          ))}
        </MapContainer>

        {/* Statistics panel overlay - positioned within map container */}
        <FlightStats stats={stats} />
      </div>

      {/* Passenger popup */}
      {selectedRoute && (
        <PassengerPopup
          route={selectedRoute.route}
          onClose={handleClosePopup}
        />
      )}
    </div>
  );
}
