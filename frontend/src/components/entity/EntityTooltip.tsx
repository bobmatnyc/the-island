import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import type { Entity } from '@/lib/api';
import { getEntityUrl } from '@/utils/entityUrls';
import { UnifiedBioView } from './UnifiedBioView';

/**
 * EntityTooltip Component - Clickable Bio Preview with Navigation
 *
 * Design Decision: HoverCard-based entity bio preview with clickable navigation
 *
 * Rationale: Selected Radix UI HoverCard over simple tooltip for richer content display.
 * Rejected simple tooltip due to limited styling and single-line text constraint.
 * HoverCard provides better UX with formatted bio summaries, metadata, and imagery.
 * Added clickable navigation to allow users to view full entity detail page.
 *
 * Trade-offs:
 * - UX: Rich content preview vs. simple text tooltip
 * - Performance: Lazy loading bio data vs. pre-loaded (optimized with caching)
 * - Accessibility: Full keyboard navigation vs. hover-only interaction
 * - Navigation: Click to view full profile vs. hover-only preview
 *
 * Performance:
 * - Time Complexity: O(1) hover trigger, O(1) API lookup (with cache)
 * - Space Complexity: O(N) cached entities in memory
 * - Expected Performance: <100ms bio fetch on first hover, instant on subsequent
 *
 * Bottleneck: API fetch on first hover. Mitigated with:
 * 1. In-memory cache to prevent duplicate fetches
 * 2. Lazy loading (fetch only on hover, not on mount)
 * 3. 300ms hover delay to avoid unnecessary fetches on quick mouse movements
 *
 * Navigation:
 * - Uses GUID-based URLs for stable, permanent links: /entities/{guid}/{slug}
 * - Falls back to ID-based URLs if GUID not available (backward compatibility)
 * - Visual indicators: hover effect, cursor pointer, "View full profile →" text
 *
 * Optimization Opportunities:
 * 1. Prefetch bios for visible entities (reduce perceived latency)
 * 2. IndexedDB persistence for bio cache across sessions
 * 3. GraphQL/batch API to fetch multiple bios in one request
 *
 * Scalability: Current design handles ~100 entity hovers/session efficiently.
 * For >1000 hovers, implement LRU cache eviction to prevent memory growth.
 *
 * Usage:
 * ```tsx
 * <EntityTooltip entityId="jeffrey_epstein">
 *   <span className="cursor-help underline decoration-dotted">
 *     Jeffrey Epstein
 *   </span>
 * </EntityTooltip>
 * ```
 */

interface EntityTooltipProps {
  /** Entity ID (snake_case) or display name */
  entityId: string;
  /** Optional display name override (if different from entityId) */
  entityName?: string;
  /** Child element to wrap with hover trigger */
  children: ReactNode;
  /** Optional: Pre-loaded entity bio data (skip fetch if provided) */
  entity?: Entity;
}

// In-memory cache for entity bio data (prevent duplicate API calls)
const bioCache = new Map<string, Entity | null>();

// In-memory cache for connections data (prevent duplicate API calls)
const connectionsCache = new Map<string, any[]>();

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

export function EntityTooltip({
  entityId,
  children,
  entity: preloadedEntity,
}: EntityTooltipProps) {
  const [entity, setEntity] = useState<Entity | null>(preloadedEntity || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connections, setConnections] = useState<any[]>([]);

  // Fetch entity bio data on first hover (lazy loading)
  const fetchEntityBio = async () => {
    // Skip if already loaded or pre-loaded
    if (entity || preloadedEntity) return;

    // Check cache first
    if (bioCache.has(entityId)) {
      const cached = bioCache.get(entityId);
      setEntity(cached || null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getEntity(entityId);
      setEntity(data || null);
      bioCache.set(entityId, data || null); // Cache for future hovers

      // Also fetch connections if entity has them
      if (data && data.connection_count > 0) {
        fetchConnections(entityId);
      }
    } catch (err) {
      console.error(`Failed to fetch entity bio for ${entityId}:`, err);
      setError('Biography not available');
      bioCache.set(entityId, null); // Cache failure to prevent retries
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch entity connections for display in tooltip
  const fetchConnections = async (id: string) => {
    // Check cache first
    if (connectionsCache.has(id)) {
      const cached = connectionsCache.get(id);
      setConnections(cached || []);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/entities/${id}/connections?limit=8`);
      if (response.ok) {
        const data = await response.json();
        const conns = data.connections || [];
        setConnections(conns);
        connectionsCache.set(id, conns);
      }
    } catch (err) {
      console.error(`Failed to fetch connections for ${id}:`, err);
      setConnections([]);
    }
  };

  // Update entity if preloaded data changes
  useEffect(() => {
    if (preloadedEntity) {
      setEntity(preloadedEntity);
      // Also fetch connections if entity has them
      if (preloadedEntity.connection_count > 0) {
        fetchConnections(entityId);
      }
    } else if (!entity) {
      // Reset state if entityId changes and no preloaded data
      setEntity(null);
      setConnections([]);
    }
  }, [entityId, preloadedEntity]);

  return (
    <HoverCard openDelay={300} closeDelay={100}>
      <HoverCardTrigger asChild onMouseEnter={fetchEntityBio}>
        {children}
      </HoverCardTrigger>
      <HoverCardContent
        className="w-[32rem] max-h-[80vh] overflow-y-auto"
        side="top"
        align="start"
      >
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-3">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : error ? (
          // Error state
          <div className="text-sm text-muted-foreground">{error}</div>
        ) : entity ? (
          // Biography content using UnifiedBioView in compact mode
          <>
            <UnifiedBioView
              entity={entity}
              mode="compact"
              maxHeight="80vh"
              connections={connections}
              showOccupation={true}
              showHeader={true}
            />

            {/* View Full Profile Link */}
            <Link
              to={getEntityUrl(entity)}
              className="flex items-center justify-center gap-1.5 text-xs text-primary font-medium pt-2 border-t hover:bg-accent rounded-md py-2 transition-colors mt-4"
            >
              <span>View full profile</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </>
        ) : (
          // No data state
          <div className="text-sm text-muted-foreground">
            No biography information available
          </div>
        )}
      </HoverCardContent>
    </HoverCard>
  );
}
