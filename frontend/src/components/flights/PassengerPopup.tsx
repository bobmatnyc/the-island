import { Dialog, DialogHeader, DialogTitle, DialogPortal } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MapPin, Plane, Calendar, Users, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { FlightRoute } from '@/lib/api';
import { formatEntityName } from '@/utils/nameFormat';
import { EntityTooltip } from '@/components/entity/EntityTooltip';
import * as DialogPrimitive from '@radix-ui/react-dialog';

/**
 * PassengerPopup Component
 *
 * Design Decision: ShadCN Dialog for passenger details
 * Rationale: Reuse existing Dialog component for consistency with app design.
 * Displays all flights for a clicked route with passenger manifests.
 *
 * Layout:
 * - Header: Route information (origin → destination)
 * - Body: Scrollable list of flights with dates, passengers, aircraft
 * - Each flight card shows: Date, passenger badges, aircraft tail number
 *
 * UX Considerations:
 * - ScrollArea for long passenger lists (some routes have 10+ flights)
 * - Badges for passengers to enable future entity page links
 * - Click outside or ESC key to close
 *
 * Performance: Renders up to ~20 flights per route efficiently with ScrollArea
 *
 * GUID Migration Limitation:
 * - Currently uses ID-based navigation: /entities/{id}
 * - Flight data only provides passenger names, not full entity objects with GUIDs
 * - Generates snake_case ID from passenger name for backward compatibility
 * - Backend EntityDetail page supports both ID and GUID lookup
 * - Future Enhancement: Backend API should include entity GUIDs in flight passenger data
 *   to enable GUID-based URLs with SEO slugs: /entities/{guid}/{name-slug}
 */

interface PassengerPopupProps {
  route: FlightRoute;
  onClose: () => void;
}

export function PassengerPopup({ route, onClose }: PassengerPopupProps) {
  const navigate = useNavigate();

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const handlePassengerClick = (passengerName: string) => {
    // Convert passenger name to entity ID (snake_case)
    const entityId = passengerName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
    onClose();
    navigate(`/entities/${entityId}`);
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogPortal>
        {/* High z-index overlay to appear above Leaflet map */}
        <DialogPrimitive.Overlay className="fixed inset-0 z-[9998] bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

        {/* High z-index content to appear above Leaflet map */}
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-[9999] grid w-full max-w-2xl translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-xl">
              <MapPin className="h-5 w-5 text-amber-400" />
              <span className="font-semibold">{route.origin.code}</span>
              <Plane className="h-4 w-4 text-muted-foreground" />
              <span className="font-semibold">{route.destination.code}</span>
            </DialogTitle>
            <div className="text-sm text-muted-foreground">
              {route.origin.city} → {route.destination.city}
            </div>
            <div className="flex items-center gap-2 text-sm pt-2">
              <Badge variant="default">
                {route.frequency} flight{route.frequency !== 1 ? 's' : ''}
              </Badge>
            </div>
          </DialogHeader>

          <ScrollArea className="max-h-[50vh] pr-4">
            <div className="space-y-3">
              {route.flights.map((flight, idx) => (
                <div
                  key={`${flight.id}-${idx}`}
                  className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{formatDate(flight.date)}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {flight.aircraft}
                    </Badge>
                  </div>

                  {flight.passengers.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Users className="h-4 w-4" />
                        <span>
                          {flight.passenger_count} passenger{flight.passenger_count !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {flight.passengers.map((passenger, pIdx) => {
                          const entityId = passenger.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
                          return (
                            <EntityTooltip
                              key={`${passenger}-${pIdx}`}
                              entityId={entityId}
                              entityName={formatEntityName(passenger)}
                            >
                              <Badge
                                variant="outline"
                                className="text-xs hover:bg-primary hover:text-primary-foreground cursor-pointer transition-colors"
                                onClick={() => handlePassengerClick(passenger)}
                              >
                                {formatEntityName(passenger)}
                              </Badge>
                            </EntityTooltip>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>

          <div className="text-xs text-muted-foreground pt-4 border-t">
            Click a passenger badge to view their entity profile
          </div>

          {/* Close button */}
          <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}
