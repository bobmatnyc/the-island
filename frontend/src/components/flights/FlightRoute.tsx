import { useState } from 'react';
import { Polyline } from 'react-leaflet';
import type { FlightRoute as FlightRouteType } from '@/lib/api';
import type { LeafletMouseEvent } from 'leaflet';

/**
 * FlightRoute Component
 *
 * Design Decision: Straight line polylines with variable thickness and hover effects
 * Rationale: Phase 1 MVP uses straight lines for simplicity. Curved geodesic paths
 * deferred to Phase 2 with leaflet.curve plugin.
 *
 * Performance:
 * - Time Complexity: O(1) for rendering each route
 * - Space Complexity: O(1) per route (2 coordinate pairs)
 *
 * Thickness Calculation:
 * - 1-4 flights: 2px
 * - 5-9 flights: 3px
 * - 10+ flights: 4px
 *
 * Hover Behavior:
 * - Default opacity: 0.6
 * - Hover opacity: 1.0
 * - Smooth transition for better UX
 *
 * Future Enhancement: Replace Polyline with Curve component for geodesic arcs
 */

interface FlightRouteProps {
  route: FlightRouteType;
  onClick: (route: FlightRouteType, event: LeafletMouseEvent) => void;
}

export function FlightRoute({ route, onClick }: FlightRouteProps) {
  const [hovered, setHovered] = useState(false);

  // Calculate line weight based on frequency
  const getLineWeight = (frequency: number): number => {
    if (frequency >= 10) return 4;
    if (frequency >= 5) return 3;
    return 2;
  };

  const positions: [number, number][] = [
    [route.origin.lat, route.origin.lon],
    [route.destination.lat, route.destination.lon]
  ];

  const weight = getLineWeight(route.frequency);
  const opacity = hovered ? 1.0 : 0.6;

  return (
    <Polyline
      positions={positions}
      pathOptions={{
        color: '#58a6ff',
        weight: weight,
        opacity: opacity,
        lineCap: 'round',
        lineJoin: 'round'
      }}
      eventHandlers={{
        mouseover: () => setHovered(true),
        mouseout: () => setHovered(false),
        click: (e) => onClick(route, e)
      }}
    />
  );
}
