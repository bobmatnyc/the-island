import { useNavigate } from 'react-router-dom';
import { Eye, Plane, Network, User, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { Entity } from '@/lib/api';

interface EntityLinksProps {
  entity: Entity;
  onBioClick: () => void;
}

interface LinkCardProps {
  icon: React.ReactNode;
  label: string;
  count?: number;
  onClick: () => void;
  variant?: 'default' | 'bio';
}

function LinkCard({ icon, label, count, onClick, variant = 'default' }: LinkCardProps) {
  const isBio = variant === 'bio';

  return (
    <Card
      className="cursor-pointer hover:border-primary transition-all duration-200 hover:shadow-md group"
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-primary group-hover:scale-110 transition-transform duration-200">
              {icon}
            </div>
            <div>
              <div className="font-semibold text-lg">{label}</div>
              {count !== undefined && !isBio && (
                <div className="text-sm text-muted-foreground">
                  {count.toLocaleString()} item{count !== 1 ? 's' : ''}
                </div>
              )}
              {isBio && (
                <div className="text-sm text-muted-foreground">
                  View full biography
                </div>
              )}
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all duration-200" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * EntityLinks Component
 *
 * Navigation cards showing counts and linking to filtered views.
 *
 * Design Decision: Count-Based Navigation Cards
 * Rationale: Users need to see data volume before navigating. Showing counts
 * helps users decide which view to explore first (e.g., "89 documents" vs "2 flights").
 *
 * Performance: Counts come from Entity object already loaded, no extra API calls needed.
 * All counts are available immediately from entity_stats backend cache.
 *
 * Navigation Strategy:
 * - Bio: Toggle expanded view in same page (no navigation)
 * - Docs: Navigate to /documents with entity filter pre-applied
 * - Flights: Navigate to /flights with passenger filter pre-applied
 * - Network: Navigate to /network with focus entity parameter
 *
 * GUID Migration:
 * - Prefer entity.guid over entity.id for query parameters
 * - Falls back to entity.id for backward compatibility with older entities
 * - Backend supports both GUID and ID-based filtering
 *
 * Future Enhancement: Add loading skeletons if counts become async.
 */
export function EntityLinks({ entity, onBioClick }: EntityLinksProps) {
  const navigate = useNavigate();

  // Prefer GUID over ID for query parameters (new format), fallback to ID (legacy)
  const entityIdentifier = entity.guid || entity.id;

  const handleDocsClick = () => {
    // Navigate to documents page with entity filter (using GUID if available, else ID)
    navigate(`/documents?entity=${entityIdentifier}`);
  };

  const handleFlightsClick = () => {
    // Navigate to flights page with passenger filter (using GUID if available, else ID)
    navigate(`/flights?passenger=${entityIdentifier}`);
  };

  const handleNetworkClick = () => {
    // Navigate to network page with focus entity (using GUID if available, else ID)
    navigate(`/network?focus=${entityIdentifier}`);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Biography Card */}
      <LinkCard
        icon={<User className="h-6 w-6" />}
        label="Bio"
        onClick={onBioClick}
        variant="bio"
      />

      {/* Documents Card */}
      <LinkCard
        icon={<Eye className="h-6 w-6" />}
        label="Docs"
        count={entity.total_documents}
        onClick={handleDocsClick}
      />

      {/* Flights Card */}
      <LinkCard
        icon={<Plane className="h-6 w-6" />}
        label="Flights"
        count={entity.flight_count}
        onClick={handleFlightsClick}
      />

      {/* Network Card */}
      <LinkCard
        icon={<Network className="h-6 w-6" />}
        label="Network"
        count={entity.connection_count}
        onClick={handleNetworkClick}
      />
    </div>
  );
}
