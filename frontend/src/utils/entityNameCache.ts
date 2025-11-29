/**
 * Entity Name Cache for GUID Hydration
 *
 * Design Decision: In-memory cache for GUID-to-name mappings
 * Rationale: Avoid repeated API calls for the same GUID within a session.
 * Entity names rarely change, so caching is safe and improves performance.
 *
 * Trade-offs:
 * - Performance: O(1) cache lookup vs. ~100ms API call
 * - Memory: Negligible (typical usage: <100 entities * ~50 bytes each = ~5KB)
 * - Freshness: Names cached until page reload (acceptable trade-off)
 * - Complexity: Simple Map implementation vs. more complex cache strategies
 *
 * Cache Strategy:
 * - Storage: In-memory Map (cleared on page reload)
 * - Eviction: None (session-based, cleared on unmount)
 * - Invalidation: Manual via clearEntityNameCache()
 * - Persistence: None (intentional - fresh data on each session)
 *
 * Performance:
 * - Cache hit: O(1) lookup, <1ms
 * - Cache miss: API call required (~100ms)
 * - Memory: O(n) where n = number of unique GUIDs accessed
 *
 * Example Usage:
 * ```typescript
 * // Check cache before API call
 * const cached = getCachedEntityName(guid);
 * if (cached) {
 *   return cached; // Fast path: <1ms
 * }
 *
 * // Cache miss: fetch from API
 * const name = await hydrateEntityName(guid);
 * cacheEntityName(guid, name); // Store for next time
 * ```
 *
 * Future Optimizations:
 * - TTL-based eviction if entity names change frequently (unlikely)
 * - LocalStorage persistence across sessions (if UX benefit is clear)
 * - LRU eviction if memory becomes a concern (at >10,000 entities)
 */

/**
 * In-memory cache for GUID -> entity name mappings
 *
 * Implementation: JavaScript Map for O(1) lookup
 * Scope: Module-level singleton, shared across all components
 * Lifecycle: Cleared on page reload
 */
const entityNameCache = new Map<string, string>();

/**
 * Get cached entity name for GUID
 *
 * @param guid Entity GUID to lookup
 * @returns Cached entity name or null if not in cache
 */
export function getCachedEntityName(guid: string): string | null {
  return entityNameCache.get(guid) || null;
}

/**
 * Store entity name in cache
 *
 * Cache updates are idempotent - safe to call multiple times.
 * Does not validate GUID format or entity name format.
 *
 * @param guid Entity GUID (cache key)
 * @param name Entity name (cache value)
 */
export function cacheEntityName(guid: string, name: string): void {
  entityNameCache.set(guid, name);
}

/**
 * Check if GUID is in cache
 *
 * @param guid Entity GUID to check
 * @returns True if GUID has cached name
 */
export function hasCachedEntityName(guid: string): boolean {
  return entityNameCache.has(guid);
}

/**
 * Get cache size (number of cached entities)
 *
 * Use case: Debugging, performance monitoring
 * @returns Number of cached GUID-to-name mappings
 */
export function getCacheSize(): number {
  return entityNameCache.size;
}

/**
 * Clear the entire cache
 *
 * Use cases:
 * - Testing: Reset cache state between tests
 * - Manual refresh: Force reload of entity names
 * - Memory management: Clear cache if it grows too large (unlikely)
 *
 * Note: Rarely needed in production - cache is session-scoped
 */
export function clearEntityNameCache(): void {
  entityNameCache.clear();
}

/**
 * Remove a specific entry from cache
 *
 * Use case: Entity name changed, invalidate specific entry
 * @param guid Entity GUID to remove from cache
 * @returns True if entry was removed, false if not in cache
 */
export function removeCachedEntityName(guid: string): boolean {
  return entityNameCache.delete(guid);
}

/**
 * Bulk cache population
 *
 * Use case: Pre-populate cache with known GUID-name pairs
 * Example: Load frequently accessed entities on app startup
 *
 * @param entries Array of [guid, name] pairs
 */
export function bulkCacheEntityNames(entries: Array<[string, string]>): void {
  entries.forEach(([guid, name]) => {
    entityNameCache.set(guid, name);
  });
}

/**
 * Get all cached entries (for debugging)
 *
 * Use case: Inspect cache contents during development
 * @returns Array of [guid, name] pairs
 */
export function getCachedEntries(): Array<[string, string]> {
  return Array.from(entityNameCache.entries());
}
