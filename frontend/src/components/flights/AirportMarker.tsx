import { Marker, Tooltip } from 'react-leaflet';
import { divIcon } from 'leaflet';

/**
 * AirportMarker Component
 *
 * Design Decision: Custom div icon with 3-letter airport code
 * Rationale: Div icons provide better styling control than default Leaflet markers.
 * Using airport codes (TEB, PBI, etc.) instead of generic pin icons for clarity.
 *
 * Styling:
 * - Background: Amber (#fbbf24) for high visibility against dark map
 * - Font: Bold, small caps for professional appearance
 * - Size: 40x24px for optimal readability without cluttering
 *
 * Tooltip:
 * - Shows full airport name and city on hover
 * - Positioned above marker for clear association
 *
 * Performance: Div icons are lightweight, minimal rendering overhead for 89 airports
 */

interface AirportMarkerProps {
  code: string;
  position: [number, number];
  name: string;
  city: string;
}

export function AirportMarker({ code, position, name, city }: AirportMarkerProps) {
  const icon = divIcon({
    html: `
      <div class="airport-marker-content">
        ${code}
      </div>
    `,
    className: 'airport-marker',
    iconSize: [40, 24],
    iconAnchor: [20, 12]
  });

  return (
    <>
      <style>{`
        .airport-marker {
          background: transparent;
          border: none;
        }
        .airport-marker-content {
          background: #fbbf24;
          color: #0d1117;
          font-weight: 700;
          font-size: 11px;
          text-align: center;
          padding: 4px 6px;
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          white-space: nowrap;
          font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace;
          letter-spacing: 0.5px;
        }
      `}</style>
      <Marker position={position} icon={icon}>
        <Tooltip direction="top" offset={[0, -12]} opacity={0.95}>
          <div className="text-xs">
            <div className="font-semibold">{name}</div>
            <div className="text-muted-foreground">{city}</div>
            <div className="text-amber-400 font-mono">{code}</div>
          </div>
        </Tooltip>
      </Marker>
    </>
  );
}
