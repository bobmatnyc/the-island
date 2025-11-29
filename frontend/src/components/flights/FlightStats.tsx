import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, Plane, MapPin, Users, Calendar } from 'lucide-react';

/**
 * FlightStats Component
 *
 * Design Decision: Collapsible statistics panel in bottom-right corner
 * Rationale: Provides real-time statistics without obstructing map view.
 * Users can minimize panel when focusing on route exploration.
 *
 * Statistics Displayed:
 * - Total flights (updates with filters)
 * - Unique routes (updates with filters)
 * - Unique passengers (updates with filters)
 * - Date range (static, from API)
 *
 * Styling:
 * - Semi-transparent background for dark theme consistency
 * - Backdrop blur for depth
 * - Compact cards with icons for visual hierarchy
 *
 * UX:
 * - Minimize button to collapse panel
 * - Smooth transitions for expand/collapse
 * - Keyboard accessible (space/enter to toggle)
 *
 * Performance: Statistics are pre-calculated in parent, no computation overhead
 */

interface FlightStatsProps {
  stats: {
    totalFlights: number;
    uniqueRoutes: number;
    uniquePassengers: number;
    dateRange: { start: string; end: string };
  };
}

export function FlightStats({ stats }: FlightStatsProps) {
  const [minimized, setMinimized] = useState(false);

  const formatDate = (dateStr: string): string => {
    try {
      // Handle MM/DD/YYYY format
      const [month, day, year] = dateStr.split('/');
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="absolute bottom-4 right-4 z-[1000]">
      <div
        className="rounded-lg shadow-lg transition-all duration-300"
        style={{
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          minWidth: minimized ? '200px' : '280px'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-white/10">
          <h3 className="text-sm font-semibold text-white">Flight Statistics</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMinimized(!minimized)}
            className="h-6 w-6 p-0 text-white hover:bg-white/10"
          >
            {minimized ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Stats Grid */}
        {!minimized && (
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Plane className="h-4 w-4 text-amber-400" />
                <span className="text-xs text-white/80">Total Flights</span>
              </div>
              <span className="text-sm font-bold text-white">
                {stats.totalFlights.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-amber-400" />
                <span className="text-xs text-white/80">Routes</span>
              </div>
              <span className="text-sm font-bold text-white">
                {stats.uniqueRoutes.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-amber-400" />
                <span className="text-xs text-white/80">Passengers</span>
              </div>
              <span className="text-sm font-bold text-white">
                {stats.uniquePassengers.toLocaleString()}
              </span>
            </div>

            <div className="pt-2 border-t border-white/10">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="h-4 w-4 text-amber-400" />
                <span className="text-xs text-white/80">Date Range</span>
              </div>
              <div className="text-xs text-white/70 pl-6">
                {formatDate(stats.dateRange.start)}
                <br />
                to {formatDate(stats.dateRange.end)}
              </div>
            </div>
          </div>
        )}

        {/* Minimized view */}
        {minimized && (
          <div className="p-3 text-center">
            <div className="text-lg font-bold text-white">
              {stats.totalFlights.toLocaleString()}
            </div>
            <div className="text-xs text-white/60">flights</div>
          </div>
        )}
      </div>
    </div>
  );
}
