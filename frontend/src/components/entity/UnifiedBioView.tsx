import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, Plane, FileText, BookOpen, Users, Briefcase } from 'lucide-react';
import type { Entity } from '@/lib/api';
import { formatEntityName } from '@/utils/nameFormat';
import {
  getOccupation,
  getSourceLinks,
  hasExpandableBio,
  hasBioContent,
  hasTimeline,
  hasRelationships,
  hasDocumentReferences,
  type TimelineEvent,
  type Relationship,
  type SourceLink,
} from '@/utils/bioHelpers';

/**
 * UnifiedBioView Component - Single Source of Truth for Biography Rendering
 *
 * Design Decision: Consolidate bio rendering into ONE component
 *
 * Rationale: Previously had duplicate bio rendering in EntityTooltip AND EntityBio.
 * This violates DRY principle and creates maintenance burden. Any change to bio
 * display required changes in TWO places, risking inconsistency.
 *
 * Trade-offs:
 * - Maintainability: Single source of truth vs. duplicate code
 * - Flexibility: Shared component with mode prop vs. specialized components
 * - Bundle Size: One component vs. two (minor savings ~2-3KB)
 *
 * Architecture:
 * - UnifiedBioView: Contains ALL bio rendering logic (this component)
 * - EntityTooltip: Wrapper with HoverCard + UnifiedBioView (compact mode)
 * - EntityBio: Wrapper for detail page + UnifiedBioView (full mode)
 *
 * Display Modes:
 * - compact: For tooltips/hover cards (limited items, scrollable)
 *   • Biography: Full text with expansion
 *   • Timeline: First 5 events
 *   • Relationships: First 3 relationships
 *   • Connections: Top 8 connections
 *   • Document Refs: First 10 references
 *
 * - full: For entity detail pages (all items, no limits)
 *   • Biography: Full text with expansion
 *   • Timeline: All events
 *   • Relationships: All relationships
 *   • Connections: All connections
 *   • Document Refs: All references
 *
 * Usage:
 * ```tsx
 * // In EntityTooltip
 * <HoverCard>
 *   <HoverCardContent>
 *     <UnifiedBioView entity={entity} mode="compact" maxHeight="80vh" />
 *   </HoverCardContent>
 * </HoverCard>
 *
 * // In EntityBio
 * <Card>
 *   <CardContent>
 *     <UnifiedBioView entity={entity} mode="full" />
 *   </CardContent>
 * </Card>
 * ```
 */

interface UnifiedBioViewProps {
  /** Entity with bio data */
  entity: Entity;
  /** Display mode: 'compact' for tooltips, 'full' for detail pages */
  mode: 'compact' | 'full';
  /** Max height for scrollable container (compact mode) */
  maxHeight?: string;
  /** Optional connections data (if pre-loaded) */
  connections?: any[];
  /** Show occupation/role in header */
  showOccupation?: boolean;
  /** Show entity name header (true for tooltip, false for detail page) */
  showHeader?: boolean;
}

export function UnifiedBioView({
  entity,
  mode,
  connections = [],
  showOccupation = true,
  showHeader = true,
}: UnifiedBioViewProps) {
  const navigate = useNavigate();

  // Auto-expand biography in full mode (bio view), collapsed in compact mode (tooltips)
  const [showFullBio, setShowFullBio] = useState(mode === 'full');

  // Get derived data from entity
  const hasSummary = entity?.bio?.summary;
  const hasBiography = entity?.bio?.biography;
  const isExpandable = entity ? hasExpandableBio(entity) : false;
  const sourceLinks = entity ? getSourceLinks(entity) : [];

  // Handle category badge click - navigate to entities page with filter
  const handleCategoryClick = (categoryType: string) => {
    navigate(`/entities?category=${categoryType}`);
  };

  // Determine item limits based on mode
  const timelineLimit = mode === 'compact' ? 5 : undefined;
  const relationshipLimit = mode === 'compact' ? 3 : undefined;
  const connectionLimit = mode === 'compact' ? 8 : undefined;
  const documentRefLimit = mode === 'compact' ? 10 : undefined;

  // Helper to render icon based on name
  const renderIcon = (iconName: SourceLink['iconName']) => {
    const iconProps = { className: mode === 'compact' ? "h-3 w-3" : "h-3 w-3" };
    switch (iconName) {
      case 'Plane':
        return <Plane {...iconProps} />;
      case 'BookOpen':
        return <BookOpen {...iconProps} />;
      case 'FileText':
        return <FileText {...iconProps} />;
    }
  };

  // Text size classes based on mode
  const textSizes = {
    heading: mode === 'compact' ? 'text-sm font-semibold' : 'text-lg font-semibold',
    body: mode === 'compact' ? 'text-sm' : 'text-base',
    small: mode === 'compact' ? 'text-xs' : 'text-sm',
    badge: mode === 'compact' ? 'text-xs' : 'text-sm',
  };

  return (
    <div className="space-y-4">
      {/* Entity Header (shown in compact/tooltip mode) */}
      {showHeader && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h4 className={`${mode === 'compact' ? 'text-base' : 'text-2xl'} font-semibold leading-none`}>
              {entity.name}
            </h4>
          </div>

          {/* Entity Classification Badge - Primary Category - CLICKABLE */}
          {entity.bio?.relationship_categories && entity.bio.relationship_categories.length > 0 && (() => {
            // Get primary category (lowest priority number = highest priority)
            const primaryCategory = entity.bio.relationship_categories.reduce((prev, curr) =>
              curr.priority < prev.priority ? curr : prev
            );
            return (
              <Badge
                className={`${mode === 'compact' ? 'text-xs' : 'text-sm'} font-medium w-fit cursor-pointer hover:opacity-80 transition-opacity`}
                style={{
                  backgroundColor: primaryCategory.bg_color,
                  color: primaryCategory.color,
                  border: `1px solid ${primaryCategory.color}40`
                }}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleCategoryClick(primaryCategory.type);
                }}
                title={`Click to filter entities by ${primaryCategory.label}`}
              >
                {primaryCategory.label}
              </Badge>
            );
          })()}

          {/* Occupation/Role */}
          {showOccupation && getOccupation(entity) && (
            <div className={`flex items-center gap-2 ${textSizes.small} text-muted-foreground`}>
              <Briefcase className={mode === 'compact' ? "h-3 w-3" : "h-4 w-4"} />
              <span>{getOccupation(entity)}</span>
            </div>
          )}
        </div>
      )}

      {/* Special Badges */}
      <div className="flex flex-wrap gap-2">
        {entity.is_billionaire && (
          <Badge variant="default" className={textSizes.badge}>
            💰 Billionaire
          </Badge>
        )}
        {entity.in_black_book && (
          <Badge variant="default" className={textSizes.badge}>
            📖 Black Book
          </Badge>
        )}
        {entity.sources?.includes('flight_logs') && (
          <Badge variant="default" className={textSizes.badge}>
            ✈️ Flight Logs
          </Badge>
        )}
        {entity.news_articles_count && entity.news_articles_count > 0 && (
          <Badge variant="default" className={textSizes.badge}>
            📰 News ({entity.news_articles_count})
          </Badge>
        )}
        {entity.timeline_events_count && entity.timeline_events_count > 0 && (
          <Badge variant="default" className={textSizes.badge}>
            📅 Timeline ({entity.timeline_events_count})
          </Badge>
        )}
        {entity.appears_in_multiple_sources && (
          <Badge variant="default" className={textSizes.badge}>
            Multiple Sources
          </Badge>
        )}
      </div>

      {/* Biography Section */}
      {hasBioContent(entity) ? (
        <div className="space-y-3 pt-2 border-t">
          {/* Display summary first */}
          {hasSummary && entity.bio && (
            <p className={`${textSizes.body} text-foreground leading-relaxed whitespace-pre-wrap`}>
              {entity.bio.summary}
            </p>
          )}

          {/* Show "Read More" button if full biography exists and is different */}
          {isExpandable && (
            <div>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setShowFullBio(!showFullBio);
                }}
                className={`gap-2 ${mode === 'compact' ? 'text-xs h-7' : 'text-sm'}`}
              >
                {showFullBio ? (
                  <>
                    <ChevronUp className={mode === 'compact' ? "h-3 w-3" : "h-4 w-4"} />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className={mode === 'compact' ? "h-3 w-3" : "h-4 w-4"} />
                    Read Full Biography
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Display full biography when expanded or if no summary exists */}
          {(showFullBio || (!hasSummary && hasBiography)) && entity.bio && (
            <div className="pt-2 border-t">
              <p className={`${textSizes.body} text-foreground leading-relaxed whitespace-pre-wrap`}>
                {entity.bio.biography}
              </p>
            </div>
          )}

          {/* Biography Metadata */}
          {entity.bio?.biography_metadata && (
            <div className={`pt-2 border-t ${textSizes.small} text-muted-foreground space-y-1`}>
              <div className="flex items-center gap-4 flex-wrap">
                <span>
                  Quality: {(entity.bio.biography_metadata.quality_score * 100).toFixed(0)}%
                </span>
                <span>
                  Words: {entity.bio.biography_metadata.word_count}
                </span>
                {entity.bio.biography_metadata.source_material && (
                  <span>
                    Sources: {entity.bio.biography_metadata.source_material.join(', ')}
                  </span>
                )}
              </div>
              {mode === 'full' && (
                <p className="italic">
                  AI-generated biography from publicly available documents
                </p>
              )}
            </div>
          )}

          {/* Source Attribution Links */}
          {sourceLinks.length > 0 && (
            <div className="pt-2 border-t">
              <div className={`${textSizes.small} font-medium text-muted-foreground mb-2`}>
                Information sourced from:
              </div>
              <div className="flex flex-wrap gap-2">
                {sourceLinks.map((source) => (
                  source.url === '#' ? (
                    <Badge
                      key={source.type}
                      variant="secondary"
                      className={`${textSizes.small} px-2 py-1 gap-1.5`}
                    >
                      {renderIcon(source.iconName)}
                      {source.label}
                    </Badge>
                  ) : (
                    <Link
                      key={source.type}
                      to={source.url}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-block"
                    >
                      <Badge
                        variant="outline"
                        className={`${textSizes.small} px-2 py-1 gap-1.5 hover:bg-secondary hover:border-primary transition-colors cursor-pointer`}
                      >
                        {renderIcon(source.iconName)}
                        {source.label}
                      </Badge>
                    </Link>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="pt-2 border-t">
          <p className={`${textSizes.body} text-muted-foreground`}>
            {formatEntityName(entity.name)} appears in the Epstein archive documentation with {entity.flight_count} flight{entity.flight_count !== 1 ? 's' : ''} logged
            {entity.connection_count > 0 && ` and ${entity.connection_count} connection${entity.connection_count !== 1 ? 's' : ''} in the network`}.
          </p>
        </div>
      )}

      {/* Timeline Section */}
      {hasTimeline(entity) && (
        <div className="space-y-2 pt-2 border-t">
          <h3 className={textSizes.heading}>Timeline</h3>
          <div className={`space-y-1.5 ${mode === 'compact' ? 'max-h-40 overflow-y-auto' : ''}`}>
            {(entity.bio!.timeline as TimelineEvent[])
              .slice(0, timelineLimit)
              .map((event, idx) => (
                <div key={idx} className={`flex gap-3 ${textSizes.small}`}>
                  <span className="text-muted-foreground min-w-20">
                    {new Date(event.date).toLocaleDateString()}
                  </span>
                  <span>{event.event}</span>
                </div>
              ))}
            {timelineLimit && (entity.bio!.timeline as TimelineEvent[]).length > timelineLimit && (
              <p className={`${textSizes.small} text-muted-foreground italic`}>
                +{(entity.bio!.timeline as TimelineEvent[]).length - timelineLimit} more events
              </p>
            )}
          </div>
        </div>
      )}

      {/* Relationships Section */}
      {hasRelationships(entity) && (
        <div className="space-y-2 pt-2 border-t">
          <h3 className={textSizes.heading}>Key Relationships</h3>
          <div className="space-y-2">
            {(entity.bio!.relationships as Relationship[])
              .slice(0, relationshipLimit)
              .map((rel, idx) => (
                <div key={idx} className={`rounded-md bg-secondary/50 ${mode === 'compact' ? 'p-2' : 'p-3'}`}>
                  <div className={`${mode === 'compact' ? 'text-sm' : 'text-base'} font-medium`}>{rel.entity}</div>
                  <div className={`${textSizes.small} text-muted-foreground`}>{rel.nature}</div>
                  <div className={`${textSizes.small} mt-1`}>{rel.description}</div>
                </div>
              ))}
            {relationshipLimit && (entity.bio!.relationships as Relationship[]).length > relationshipLimit && (
              <p className={`${textSizes.small} text-muted-foreground italic`}>
                +{(entity.bio!.relationships as Relationship[]).length - relationshipLimit} more relationships
              </p>
            )}
          </div>
        </div>
      )}

      {/* Network Connections */}
      {connections.length > 0 && (
        <div className="space-y-2 pt-2 border-t">
          <div className="flex items-center gap-2">
            <Users className={mode === 'compact' ? "h-4 w-4 text-muted-foreground" : "h-5 w-5 text-muted-foreground"} />
            <h3 className={textSizes.heading}>Connections</h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {connections.slice(0, connectionLimit).map((conn) => (
              <Link
                key={conn.entity_id}
                to={`/entities/${conn.guid || conn.entity_id}/${conn.display_name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                onClick={(e) => e.stopPropagation()}
              >
                <Badge
                  variant="outline"
                  className={`${textSizes.small} hover:bg-secondary cursor-pointer`}
                >
                  {conn.display_name}
                  {conn.shared_flights > 0 && ` (${conn.shared_flights})`}
                </Badge>
              </Link>
            ))}
            {connectionLimit && connections.length > connectionLimit && (
              <Badge variant="secondary" className={textSizes.small}>
                +{connections.length - connectionLimit} more
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Document References Section */}
      {hasDocumentReferences(entity) && (
        <div className="space-y-2 pt-2 border-t">
          <h3 className={textSizes.heading}>Document References</h3>
          <div className="flex flex-wrap gap-1.5">
            {entity.bio!.document_references
              .slice(0, documentRefLimit)
              .map((ref: string, idx: number) => (
                <Badge key={idx} variant="outline" className={textSizes.small}>{ref}</Badge>
              ))}
            {documentRefLimit && entity.bio!.document_references.length > documentRefLimit && (
              <Badge variant="secondary" className={textSizes.small}>
                +{entity.bio!.document_references.length - documentRefLimit} more
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Entity Metadata */}
      <div className="pt-2 border-t">
        <div className={`grid grid-cols-3 gap-3 text-center`}>
          <div>
            <div className={`${textSizes.small} text-muted-foreground`}>Documents</div>
            <div className={`${mode === 'compact' ? 'text-lg' : 'text-2xl'} font-bold`}>{entity.total_documents}</div>
          </div>
          <div>
            <div className={`${textSizes.small} text-muted-foreground`}>Flights</div>
            <div className={`${mode === 'compact' ? 'text-lg' : 'text-2xl'} font-bold`}>{entity.flight_count}</div>
          </div>
          <div>
            <div className={`${textSizes.small} text-muted-foreground`}>Connections</div>
            <div className={`${mode === 'compact' ? 'text-lg' : 'text-2xl'} font-bold`}>{entity.connection_count}</div>
          </div>
        </div>
      </div>

      {/* Full mode only: Additional sections */}
      {mode === 'full' && (
        <>
          {/* Data Sources */}
          {entity.sources.length > 0 && (
            <div className="space-y-3 pt-4 border-t">
              <h3 className={textSizes.heading}>Data Sources</h3>
              <div className="flex flex-wrap gap-2">
                {entity.sources.map((source, idx) => (
                  <Badge key={idx} variant="secondary" className={textSizes.badge}>
                    {source}
                  </Badge>
                ))}
              </div>
              <p className={`${textSizes.small} text-muted-foreground`}>
                All information is sourced from publicly available documents and records.
              </p>
            </div>
          )}

          {/* Document Types */}
          {Object.keys(entity.document_types).length > 0 && (
            <div className="space-y-3 pt-4 border-t">
              <h3 className={textSizes.heading}>Document Types</h3>
              <div className="space-y-2">
                {Object.entries(entity.document_types).map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between py-2 px-3 rounded-md bg-secondary/50"
                  >
                    <span className="font-medium">{type}</span>
                    <Badge variant="secondary" className={textSizes.badge}>
                      {count} document{count !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
