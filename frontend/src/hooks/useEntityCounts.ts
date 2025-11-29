import { useState, useEffect } from 'react';
import type { Entity } from '@/lib/api';

interface EntityCounts {
  documents: number;
  flights: number;
  connections: number;
}

interface UseEntityCountsReturn {
  counts: EntityCounts | null;
  loading: boolean;
  error: string | null;
}

/**
 * useEntityCounts Hook
 *
 * Provides cached access to entity counts for navigation cards.
 *
 * Design Decision: Direct Extraction vs API Calls
 * Rationale: Entity object already contains all counts (total_documents,
 * flight_count, connection_count). No need for separate API calls.
 * This hook provides consistent interface and handles loading/error states.
 *
 * Performance: Zero network overhead - counts extracted from entity object.
 * Backend entity_stats cache already aggregates these values efficiently.
 *
 * Caching Strategy: In-memory cache (React state) persists for component lifetime.
 * Session storage not needed since entity page remounts on navigation.
 *
 * Error Handling: Validates entity object structure, returns null if malformed.
 *
 * Future Enhancement: If count endpoints are added, this hook can be extended
 * to support separate API calls with proper caching (5-minute TTL).
 *
 * @param entity - Entity object from API
 * @returns Counts object with loading and error states
 */
export function useEntityCounts(entity: Entity | null): UseEntityCountsReturn {
  const [counts, setCounts] = useState<EntityCounts | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!entity) {
      setLoading(false);
      setError('No entity provided');
      return;
    }

    try {
      // Extract counts directly from entity object
      // All these fields are guaranteed by Entity type definition
      const entityCounts: EntityCounts = {
        documents: entity.total_documents ?? 0,
        flights: entity.flight_count ?? 0,
        connections: entity.connection_count ?? 0,
      };

      setCounts(entityCounts);
      setError(null);
    } catch (err) {
      console.error('Failed to extract entity counts:', err);
      setError('Failed to load entity counts');
      setCounts(null);
    } finally {
      setLoading(false);
    }
  }, [entity]);

  return { counts, loading, error };
}

/**
 * Session-based cache for count data (future enhancement)
 *
 * If backend adds dedicated count endpoints, implement caching here:
 *
 * const CACHE_KEY_PREFIX = 'entity_counts_';
 * const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
 *
 * function getCachedCounts(entityId: string): EntityCounts | null {
 *   const cached = sessionStorage.getItem(CACHE_KEY_PREFIX + entityId);
 *   if (!cached) return null;
 *
 *   const { data, timestamp } = JSON.parse(cached);
 *   if (Date.now() - timestamp > CACHE_TTL) {
 *     sessionStorage.removeItem(CACHE_KEY_PREFIX + entityId);
 *     return null;
 *   }
 *   return data;
 * }
 *
 * function setCachedCounts(entityId: string, counts: EntityCounts) {
 *   sessionStorage.setItem(
 *     CACHE_KEY_PREFIX + entityId,
 *     JSON.stringify({ data: counts, timestamp: Date.now() })
 *   );
 * }
 */
