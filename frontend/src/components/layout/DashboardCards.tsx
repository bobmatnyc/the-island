import { Link } from 'react-router-dom'
import {
  FileText,
  Users,
  Plane,
  Network,
  Clock
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import type { Stats } from '@/lib/api'

interface DashboardCardsProps {
  stats: Stats | null
  loading?: boolean
  error?: boolean
}

interface CardData {
  to: string
  icon: React.ComponentType<{ className?: string }>
  count: number | string
  label: string
  description: string
  color: string
}

/**
 * Dashboard Cards Component
 *
 * Design Decision: Extracted from Dashboard page for reusability
 * Rationale: Home page needed dashboard functionality without duplicating code
 *
 * Accessibility:
 * - Cards are keyboard navigable via Link wrapper
 * - ARIA labels provide context for screen readers
 * - Focus indicators for keyboard navigation
 *
 * Performance:
 * - Minimal re-renders via React.memo (if needed)
 * - Lazy loading of count data via parent
 * - CSS transitions for smooth hover effects
 */
export function DashboardCards({ stats, loading = false, error = false }: DashboardCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[160px] rounded-lg" />
        ))}
      </div>
    )
  }

  const cards: CardData[] = [
    {
      to: '/timeline',
      icon: Clock,
      count: ((stats?.timeline_events || 0) + (stats?.news_articles || 0)).toLocaleString(),
      label: 'Timeline & News',
      description: 'Explore chronological events, flights, and news coverage',
      color: 'text-green-600 dark:text-green-400'
    },
    {
      to: '/entities',
      icon: Users,
      count: stats?.total_entities?.toLocaleString() || 'N/A',
      label: 'Entities',
      description: 'View people and organizations in the network',
      color: 'text-purple-600 dark:text-purple-400'
    },
    {
      to: '/flights',
      icon: Plane,
      count: stats?.flight_count?.toLocaleString() || 'N/A',
      label: 'Flights',
      description: 'Analyze flight logs and passenger manifests',
      color: 'text-orange-600 dark:text-orange-400'
    },
    {
      to: '/documents',
      icon: FileText,
      count: stats?.total_documents?.toLocaleString() || 'N/A',
      label: 'Documents',
      description: 'Access court documents and legal filings',
      color: 'text-blue-600 dark:text-blue-400'
    },
    {
      to: '/network',
      icon: Network,
      count: stats?.network_nodes?.toLocaleString() || 'N/A',
      label: 'Visualizations',
      description: 'Interactive charts and network graphs',
      color: 'text-cyan-600 dark:text-cyan-400'
    }
  ]

  return (
    <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon
        const isUnavailable = error || card.count === 'N/A'

        return (
          <Link
            key={card.to}
            to={card.to}
            className="group"
            aria-label={`View ${card.count} ${card.label}`}
          >
            <div
              className={`
                h-full min-h-[160px] p-6 rounded-lg border bg-card
                transition-all duration-200
                hover:shadow-lg hover:scale-[1.02]
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                cursor-pointer
                ${isUnavailable ? 'opacity-60' : ''}
              `}
              role="button"
              tabIndex={-1}
            >
              <div className="flex flex-col h-full justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Icon className={`h-6 w-6 ${card.color}`} />
                  <span className="text-sm text-muted-foreground font-medium">
                    {card.label}
                  </span>
                </div>
                <div className="text-3xl font-bold tracking-tight">
                  {card.count}
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {card.description}
                </p>
              </div>
            </div>
          </Link>
        )
      })}
    </div>
  )
}
