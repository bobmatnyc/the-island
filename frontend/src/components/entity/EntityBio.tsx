import { ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Entity } from '@/lib/api';
import { EntityConnections } from './EntityConnections';
import { UnifiedBioView } from './UnifiedBioView';
import { RelatedEntities } from './RelatedEntities';

interface EntityBioProps {
  entity: Entity;
  onBack: () => void;
}

/**
 * EntityBio Component - Biography View for Entity Detail Page
 *
 * Design Decision: Wrapper Component Using UnifiedBioView
 *
 * Rationale: Consolidate duplicate bio rendering logic into single component.
 * Previously EntityBio had ~250 lines of duplicate code from EntityTooltip.
 * This violated DRY principle and created maintenance burden.
 *
 * New Architecture:
 * - EntityBio: Thin wrapper providing Card UI + UnifiedBioView in "full" mode
 * - UnifiedBioView: Single source of truth for all biography rendering
 * - No duplicate bio rendering code across codebase
 *
 * Trade-offs:
 * - Maintainability: One place to update bio logic vs. two separate components
 * - Consistency: Guaranteed identical display logic between tooltip and detail page
 * - Bundle Size: ~3KB saved by eliminating duplicate code
 *
 * Data Flow:
 * 1. EntityDetail page passes entity to EntityBio
 * 2. EntityBio wraps UnifiedBioView with Card UI and Back button
 * 3. UnifiedBioView renders all bio content in "full" mode (no limits)
 * 4. EntityConnections fetches and displays network connections
 */
export function EntityBio({ entity, onBack }: EntityBioProps) {

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <CardTitle className="text-2xl">Biography</CardTitle>
          <Button variant="ghost" onClick={onBack} size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Show Navigation
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Use UnifiedBioView in full mode (no item limits) */}
        <UnifiedBioView
          entity={entity}
          mode="full"
          showOccupation={false}
          showHeader={false}
        />

        {/* Network Connections - Keep separate for interactive functionality */}
        {entity.connection_count > 0 && (
          <EntityConnections entityId={entity.id} limit={8} />
        )}

        {/* Related Entities - Semantic similarity based discovery */}
        <RelatedEntities entityId={entity.id} limit={8} minSimilarity={0.4} />
      </CardContent>
    </Card>
  );
}
