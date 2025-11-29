import type { Entity } from '@/lib/api';

/**
 * Shared Biography Helper Utilities
 *
 * Design Decision: Extract shared biography logic for reuse
 *
 * Rationale: Both EntityTooltip and EntityBio need identical logic for:
 * - Biography summary extraction
 * - Source link generation
 * - Occupation/role formatting
 * - Data availability checks
 *
 * This avoids code duplication and ensures consistent behavior across components.
 *
 * Trade-offs:
 * - Maintainability: Single source of truth vs. component-specific logic
 * - Bundle Size: Shared utilities vs. duplicated code
 * - Testing: One place to test vs. multiple test suites
 */

export interface TimelineEvent {
  date: string;
  event: string;
}

export interface Relationship {
  entity: string;
  nature: string;
  description: string;
}

export interface SourceLink {
  type: 'flight_logs' | 'black_book' | 'documents';
  label: string;
  iconName: 'Plane' | 'BookOpen' | 'FileText';
  url: string;
  count?: number;
}

/**
 * Get biography summary (prefer summary, fallback to truncated biography)
 */
export function getBioSummary(entity: Entity): string {
  if (entity.bio?.summary) {
    return entity.bio.summary;
  }
  if (entity.bio?.biography) {
    // Truncate to ~150 characters (2-3 sentences)
    const bio = entity.bio.biography;
    if (bio.length <= 200) return bio;

    // Find sentence boundaries
    const truncated = bio.substring(0, 200);
    const lastPeriod = truncated.lastIndexOf('.');
    if (lastPeriod > 100) {
      return truncated.substring(0, lastPeriod + 1);
    }
    return truncated + '...';
  }
  return 'No biography available';
}

/**
 * Format entity occupation/role
 */
export function getOccupation(entity: Entity): string | null {
  if (entity.bio?.occupation) return entity.bio.occupation;
  if (entity.categories.length > 0) return entity.categories[0];
  return null;
}

/**
 * Parse and extract source links from biography data
 *
 * Sources can come from:
 * - biography_metadata.source_material (array)
 * - document_context (array of document references)
 * - document_sources (object with document IDs)
 */
export function getSourceLinks(entity: Entity): SourceLink[] {
  const sources: SourceLink[] = [];

  if (!entity.bio) return sources;

  // Check source_material from biography metadata
  const sourceMaterial = entity.bio.biography_metadata?.source_material || [];

  if (sourceMaterial.includes('flight_logs')) {
    sources.push({
      type: 'flight_logs',
      label: 'Flight Logs',
      iconName: 'Plane',
      url: `/flights?passenger=${entity.id}`
    });
  }

  if (sourceMaterial.includes('black_book')) {
    sources.push({
      type: 'black_book',
      label: 'Black Book',
      iconName: 'BookOpen',
      url: '#' // No specific page, just an indicator
    });
  }

  // Check for document references
  const documentContext = entity.bio.document_context as any[] || [];
  const documentSources = entity.bio.document_sources as Record<string, any> || {};
  const docCount = documentContext.length || Object.keys(documentSources).length;

  if (docCount > 0) {
    sources.push({
      type: 'documents',
      label: `${docCount} Document${docCount !== 1 ? 's' : ''}`,
      iconName: 'FileText',
      url: `/documents?entity=${entity.id}`,
      count: docCount
    });
  }

  return sources;
}

/**
 * Check if entity has expandable biography (summary + full bio)
 */
export function hasExpandableBio(entity: Entity): boolean {
  const hasSummary = !!entity.bio?.summary;
  const hasBiography = !!entity.bio?.biography;
  return hasSummary && hasBiography && entity.bio?.summary !== entity.bio?.biography;
}

/**
 * Check if entity has any biography content
 */
export function hasBioContent(entity: Entity): boolean {
  return !!entity.bio?.summary || !!entity.bio?.biography;
}

/**
 * Check if entity has enriched timeline data
 */
export function hasTimeline(entity: Entity): boolean {
  return !!(entity.bio?.timeline && (entity.bio.timeline as TimelineEvent[]).length > 0);
}

/**
 * Check if entity has enriched relationships data
 */
export function hasRelationships(entity: Entity): boolean {
  return !!(entity.bio?.relationships && (entity.bio.relationships as Relationship[]).length > 0);
}

/**
 * Check if entity has document references
 */
export function hasDocumentReferences(entity: Entity): boolean {
  return !!(entity.bio?.document_references && entity.bio.document_references.length > 0);
}
