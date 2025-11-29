/**
 * Format entity name to "Last, First" format
 * Handles both "First Last" and "Last, First" inputs
 * @param name - The entity name in any format
 * @returns Formatted name as "Last, First"
 */
export function formatEntityName(name: string): string {
  if (!name) return '';

  const trimmedName = name.trim();

  // Already in "Last, First" format
  if (trimmedName.includes(',')) {
    return trimmedName;
  }

  // Single word (organization, location, or single name)
  const parts = trimmedName.split(/\s+/);
  if (parts.length === 1) {
    return parts[0];
  }

  // Convert "First Last" to "Last, First"
  // Assume last word is last name, everything before is first name
  const lastName = parts[parts.length - 1];
  const firstName = parts.slice(0, -1).join(' ');
  return `${lastName}, ${firstName}`;
}
