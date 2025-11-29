/**
 * GUID/UUID Utilities for Entity Hydration
 *
 * Design Decision: Client-side GUID hydration for better UX
 * Rationale: When users navigate to URLs with GUIDs (e.g., from external links),
 * we want to display human-readable entity names instead of raw UUIDs in the UI.
 *
 * Trade-offs:
 * - User Experience: Clear entity names vs. cryptic GUIDs
 * - Performance: Small API overhead vs. confusing UI
 * - Caching: In-memory cache minimizes repeated API calls
 *
 * Implementation:
 * - isGuid: Validates UUID/GUID format (already exists in entityUrls.ts)
 * - hydrateEntityName: Fetches entity name from GUID via API
 * - Graceful degradation: Returns original GUID if fetch fails
 *
 * Example Usage:
 * - URL: /news?entity=43886eef-f28a-549d-8ae0-8409c2be68c4
 * - Display: "Jeffrey Epstein" (hydrated from API)
 * - Fallback: GUID (if API call fails)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

/**
 * Check if a string is a valid UUID/GUID format
 *
 * GUID format: 8-4-4-4-12 hexadecimal digits
 * Example: 550e8400-e29b-41d4-a716-446655440000
 *
 * Performance: O(1) regex matching
 * @param value String to check
 * @returns True if valid GUID format
 */
export function isGuid(value: string): boolean {
  const guidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return guidRegex.test(value);
}

/**
 * Fetch entity name from GUID using the API
 *
 * Error Handling:
 * - Network errors: Log warning, return original GUID
 * - 404 Not Found: Log warning, return original GUID (entity may not exist)
 * - Other HTTP errors: Log warning, return original GUID
 * - Malformed response: Log error, return original GUID
 *
 * Performance:
 * - Average API call: ~50-100ms (depends on backend)
 * - Caching recommended to avoid repeated calls (see entityNameCache.ts)
 *
 * @param identifier Entity identifier (GUID or name)
 * @returns Entity name if GUID and API call succeeds, otherwise original identifier
 */
export async function hydrateEntityName(identifier: string): Promise<string> {
  // If not a GUID, return as-is (already a name or snake_case ID)
  if (!isGuid(identifier)) {
    return identifier;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v3/entities/${identifier}`);

    if (!response.ok) {
      // Don't treat 404 as an error - entity might not exist
      if (response.status === 404) {
        console.warn(`[GUID Hydration] Entity not found: ${identifier}`);
      } else {
        console.warn(`[GUID Hydration] API error for ${identifier}: ${response.status}`);
      }
      return identifier;
    }

    const data = await response.json();

    // Validate response has name field
    if (!data || typeof data.name !== 'string') {
      console.error('[GUID Hydration] Invalid response format:', data);
      return identifier;
    }

    return data.name;
  } catch (error) {
    // Network errors, CORS issues, etc.
    console.error('[GUID Hydration] Failed to fetch entity name:', error);
    return identifier;
  }
}

/**
 * Batch hydrate multiple GUIDs to entity names
 *
 * Optimization: Parallel API calls for better performance
 * Use case: Hydrating multiple entity filters at once
 *
 * Performance:
 * - Sequential: N * 100ms = slow for many entities
 * - Parallel: max(100ms) = fast regardless of count
 *
 * @param identifiers Array of entity identifiers (GUIDs or names)
 * @returns Array of entity names (same order as input)
 */
export async function hydrateEntityNames(identifiers: string[]): Promise<string[]> {
  return Promise.all(identifiers.map(id => hydrateEntityName(id)));
}
