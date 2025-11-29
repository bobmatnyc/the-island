/**
 * Entity URL Utilities
 *
 * Design Decision: GUID-based URLs with SEO-friendly names
 * Rationale: GUIDs provide stable, unique URLs that don't break when entity names change.
 * SEO-friendly slugs improve search visibility and user experience.
 *
 * URL Format: /entities/{guid}/{seo-slug}
 * - GUID: Stable UUID identifier (required for routing)
 * - SEO slug: Human-readable name (optional, ignored by backend)
 *
 * Trade-offs:
 * - Stability: GUIDs never change vs. name-based URLs can break
 * - SEO: Slugs provide context for search engines
 * - URL length: Longer than ID-based URLs but more descriptive
 * - Backward compatibility: Must support both old ID-based and new GUID URLs
 *
 * Example URLs:
 * - /entities/550e8400-e29b-41d4-a716-446655440000/jeffrey-epstein
 * - /entities/550e8400-e29b-41d4-a716-446655440000 (slug optional)
 */

/**
 * Generate SEO-friendly URL slug from entity name
 *
 * Conversion rules:
 * - Convert to lowercase
 * - Replace spaces and special chars with hyphens
 * - Remove consecutive hyphens
 * - Trim leading/trailing hyphens
 * - Handle special cases like "Epstein, Jeffrey" -> "jeffrey-epstein"
 *
 * Examples:
 * - "Jeffrey Epstein" -> "jeffrey-epstein"
 * - "Epstein, Jeffrey" -> "jeffrey-epstein"
 * - "Bill & Melinda Gates Foundation" -> "bill-melinda-gates-foundation"
 * - "Doe, John Jr." -> "john-doe-jr"
 *
 * @param name Entity name (display format)
 * @returns URL-safe slug
 */
export function generateEntitySlug(name: string): string {
  if (!name) return '';

  // Handle "LastName, FirstName" format - reverse it for more natural URL
  // "Epstein, Jeffrey" -> "Jeffrey Epstein" -> "jeffrey-epstein"
  let processedName = name;
  if (name.includes(',')) {
    const parts = name.split(',').map(p => p.trim());
    if (parts.length === 2) {
      // Reverse: "LastName, FirstName" -> "FirstName LastName"
      processedName = `${parts[1]} ${parts[0]}`;
    }
  }

  return processedName
    .toLowerCase()
    .trim()
    // Replace spaces and special characters with hyphens
    .replace(/[^a-z0-9]+/g, '-')
    // Remove consecutive hyphens
    .replace(/-+/g, '-')
    // Remove leading/trailing hyphens
    .replace(/^-|-$/g, '');
}

/**
 * Build complete entity URL path with GUID and SEO slug
 *
 * URL format: /entities/{guid}/{slug}
 * - Uses entity.guid if available (preferred)
 * - Falls back to entity.id for backward compatibility
 * - Generates SEO slug from entity.name
 *
 * Design Decision: Always include slug for better UX
 * Rationale: Slugs provide context when sharing URLs and improve SEO.
 * Backend ignores slug parameter, so it's safe to always include.
 *
 * @param entity Entity object with guid/id and name
 * @returns URL path (e.g., "/entities/550e8400.../jeffrey-epstein")
 */
export function getEntityUrl(entity: { guid?: string; id: string; name: string }): string {
  // Prefer GUID over ID (GUID is the future-proof identifier)
  const identifier = entity.guid || entity.id;
  const slug = generateEntitySlug(entity.name);

  // Always include slug for SEO and user experience
  return `/entities/${identifier}/${slug}`;
}

/**
 * Parse entity identifier from URL path
 *
 * Extracts GUID/ID from URL, ignoring the optional name slug.
 * Supports both formats:
 * - /entities/{guid}/{name} -> guid
 * - /entities/{guid} -> guid
 *
 * @param pathname Current URL pathname
 * @returns Entity identifier (GUID or ID) or null if invalid
 */
export function parseEntityIdentifier(pathname: string): string | null {
  // Match /entities/{identifier} or /entities/{identifier}/...
  const match = pathname.match(/^\/entities\/([a-zA-Z0-9_-]+)/);
  return match ? match[1] : null;
}

/**
 * Check if a string is a valid GUID format
 *
 * GUID format: 8-4-4-4-12 hexadecimal digits
 * Example: 550e8400-e29b-41d4-a716-446655440000
 *
 * @param str String to check
 * @returns True if valid GUID format
 */
export function isGuid(str: string): boolean {
  const guidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return guidRegex.test(str);
}

/**
 * Check if entity has GUID (new format) vs legacy ID
 *
 * @param entity Entity object
 * @returns True if entity has GUID field
 */
export function hasGuid(entity: { guid?: string; id: string }): boolean {
  return Boolean(entity.guid);
}
