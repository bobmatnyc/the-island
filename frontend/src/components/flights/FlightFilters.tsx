import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Filter, X } from 'lucide-react';

/**
 * FlightFilters Component
 *
 * Design Decision: Card-based filter panel above map
 * Rationale: Cleaner separation between controls and map visualization.
 * Positioned above map in document flow rather than overlaying it.
 *
 * Phase 1 Features:
 * - Passenger dropdown filter (client-side)
 * - Clear filters button
 *
 * Phase 2 Deferred:
 * - Date range filtering
 * - Airport code filtering
 * - Server-side filtering with API calls
 *
 * Styling:
 * - Card component with consistent app styling
 * - Responsive layout with flexbox
 * - No absolute positioning needed
 *
 * Performance: Client-side filtering is instant for current data scale (387 passengers)
 */

interface FlightFiltersProps {
  passengers: string[];
  selectedPassenger: string;
  onPassengerChange: (passenger: string) => void;
  onClearFilters: () => void;
}

export function FlightFilters({
  passengers,
  selectedPassenger,
  onPassengerChange,
  onClearFilters
}: FlightFiltersProps) {
  return (
    <div className="w-full relative z-[600]">
      <div className="flex items-center gap-3 p-4 rounded-lg border bg-card shadow-sm">
        <div className="flex items-center gap-2 flex-1">
          <Filter className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium">Filter by Passenger:</span>
        </div>

        <Select value={selectedPassenger} onValueChange={onPassengerChange}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="All passengers" />
          </SelectTrigger>
          <SelectContent className="max-h-[300px]">
            <SelectItem value="__ALL__">All passengers</SelectItem>
            {passengers.map(passenger => (
              <SelectItem key={passenger} value={passenger}>
                {passenger}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedPassenger && selectedPassenger !== '__ALL__' && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearFilters}
          >
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}

        <div className="text-xs text-muted-foreground px-3 py-2 rounded border bg-background">
          Phase 2: Date range filter
        </div>
      </div>
    </div>
  );
}
