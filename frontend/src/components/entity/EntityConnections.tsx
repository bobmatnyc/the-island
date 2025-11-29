import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users } from 'lucide-react';

/**
 * EntityConnections Component
 *
 * Design Decision: Network-based Relationship Display
 * Rationale: Show clickable connections to related entities based on co-occurrence
 * in flight logs and other documents. Provides quick navigation to related entities.
 *
 * Data Flow:
 * 1. Fetch connections from `/api/entities/{entity_id}/connections`
 * 2. Display top 5-8 connections with relationship context
 * 3. Click navigates to connected entity's detail page using GUID
 *
 * Trade-offs:
 * - UX: Quick navigation vs. potential information overload
 * - Performance: Additional API call vs. pre-loaded data in entity object
 * - Freshness: Always current connections vs. cached in entity data
 *
 * Error Handling:
 * - Network errors: Log and display empty state
 * - Missing GUID: Fallback to entity_id for navigation
 * - No connections: Display friendly "No connections" message
 *
 * Performance:
 * - Lazy loading: Only fetch when component mounts
 * - Cached by entity_id: Browser caches API responses
 * - Limited to 8 connections: Keeps UI clean and performant
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

interface Connection {
  entity_id: string;
  display_name: string;
  guid?: string;
  relationship_type?: string;
  strength?: number;
  shared_flights?: number;
}

interface ConnectionsResponse {
  entity_id: string;
  entity_name: string;
  total_connections: number;
  connections: Connection[];
}

interface EntityConnectionsProps {
  entityId: string;
  limit?: number;
}

export function EntityConnections({ entityId, limit = 8 }: EntityConnectionsProps) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchConnections = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/api/entities/${entityId}/connections?limit=${limit}`
        );

        if (!response.ok) {
          if (response.status === 404) {
            // Entity not found or no connections - not an error, just empty
            setConnections([]);
            return;
          }
          throw new Error(`API Error ${response.status}: ${response.statusText}`);
        }

        const data: ConnectionsResponse = await response.json();
        setConnections(data.connections || []);
      } catch (err) {
        console.error('[EntityConnections] Failed to fetch connections:', err);
        setError(err instanceof Error ? err.message : 'Failed to load connections');
        setConnections([]);
      } finally {
        setLoading(false);
      }
    };

    if (entityId) {
      fetchConnections();
    }
  }, [entityId, limit]);

  const handleConnectionClick = (connection: Connection) => {
    // Prefer GUID for navigation (stable URLs)
    const identifier = connection.guid || connection.entity_id;

    if (!identifier) {
      console.error('[EntityConnections] No identifier for connection:', connection);
      return;
    }

    // Generate slug from display name
    const slug = connection.display_name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');

    // Navigate to entity detail page
    navigate(`/entities/${identifier}/${slug}`);
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-3 pt-4 border-t">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Connections</h3>
        </div>
        <div className="text-sm text-muted-foreground">Loading connections...</div>
      </div>
    );
  }

  // Error state (non-blocking - show empty state instead)
  if (error) {
    console.warn('[EntityConnections] Error state:', error);
    // Don't show error to user - just show empty state
  }

  // No connections state
  if (connections.length === 0) {
    return (
      <div className="space-y-3 pt-4 border-t">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Connections</h3>
        </div>
        <div className="text-sm text-muted-foreground">
          No documented connections found in the network.
        </div>
      </div>
    );
  }

  // Display connections
  return (
    <div className="space-y-3 pt-4 border-t">
      <div className="flex items-center gap-2">
        <Users className="h-5 w-5 text-muted-foreground" />
        <h3 className="text-lg font-semibold">Connections</h3>
      </div>

      <div className="text-sm text-muted-foreground mb-2">
        Connected to {connections.length} {connections.length === 1 ? 'entity' : 'entities'} in the network:
      </div>

      <div className="flex flex-wrap gap-2">
        {connections.map((conn) => (
          <Button
            key={conn.entity_id}
            onClick={() => handleConnectionClick(conn)}
            variant="outline"
            size="sm"
            className="h-auto py-2 px-3 hover:bg-secondary/80 transition-colors"
          >
            <div className="flex flex-col items-start gap-1">
              <span className="font-medium text-sm">{conn.display_name}</span>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {conn.shared_flights && conn.shared_flights > 0 && (
                  <Badge variant="secondary" className="text-xs py-0 px-1.5">
                    {conn.shared_flights} flight{conn.shared_flights !== 1 ? 's' : ''}
                  </Badge>
                )}
                {conn.relationship_type && (
                  <span className="text-xs">{conn.relationship_type}</span>
                )}
              </div>
            </div>
          </Button>
        ))}
      </div>
    </div>
  );
}
