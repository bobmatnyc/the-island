/**
 * Format entity name based on entity type
 * - For persons: Reverses "Last, First" to "First Last" for display
 * - For organizations/locations: Returns name as-is
 * @param name - The entity name in any format
 * @param entityType - The type of entity ('person', 'organization', 'location')
 * @returns Formatted name appropriate for entity type
 */
export function formatEntityName(name: string, entityType?: string): string {
  if (!name) return '';

  const trimmedName = name.trim();

  // For non-person entities (organizations/locations), return as-is
  if (entityType === 'organization' || entityType === 'location') {
    return trimmedName;
  }

  // For person entities, reverse "Last, First" to "First Last"
  if (trimmedName.includes(',')) {
    const parts = trimmedName.split(',').map(s => s.trim());
    return parts.reverse().join(' ');
  }

  // Already in correct format
  return trimmedName;
}
