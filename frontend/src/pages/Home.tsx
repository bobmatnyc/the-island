import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, type TimelineEvent } from '@/lib/api'
import type { AboutResponse, UpdatesResponse, Stats } from '@/lib/api'
import { newsApi } from '@/services/newsApi'
import type { NewsArticle } from '@/types/news'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { DashboardCards } from '@/components/layout/DashboardCards'
import { formatEntityName } from '@/utils/nameFormat'
import {
  FileText,
  Users,
  Plane,
  Network,
  Clock,
  AlertCircle,
  GitCommit,
  Calendar,
  Newspaper,
  ExternalLink
} from 'lucide-react'

// Combined activity item type
type ActivityItem = {
  type: 'timeline' | 'news'
  date: string
  data: TimelineEvent | NewsArticle
}

export function Home() {
  const [about, setAbout] = useState<AboutResponse | null>(null)
  const [updates, setUpdates] = useState<UpdatesResponse | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([])
  const [activityLoading, setActivityLoading] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        const [aboutData, updatesData, statsData] = await Promise.all([
          api.getAbout(),
          api.getUpdates(10),
          api.getStats()
        ])
        setAbout(aboutData)
        setUpdates(updatesData)
        setStats(statsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
        console.error('Error fetching home data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Fetch recent activity (timeline + news)
  useEffect(() => {
    async function fetchRecentActivity() {
      try {
        setActivityLoading(true)

        // Calculate date range for last 30 days
        const endDate = new Date()
        const startDate = new Date()
        startDate.setDate(startDate.getDate() - 30)

        const endDateStr = endDate.toISOString().split('T')[0]
        const startDateStr = startDate.toISOString().split('T')[0]

        // Fetch timeline events and news articles in parallel
        const [timelineData, newsArticles] = await Promise.all([
          api.getTimeline(),
          newsApi.getArticlesByDateRange(startDateStr, endDateStr, 10)
        ])

        // Take the 10 most recent timeline events
        const recentTimeline = timelineData.events
          .slice(0)
          .reverse()
          .slice(0, 10)

        // Combine and sort by date
        const combined: ActivityItem[] = [
          ...recentTimeline.map(event => ({
            type: 'timeline' as const,
            date: event.date,
            data: event
          })),
          ...newsArticles.map(article => ({
            type: 'news' as const,
            date: article.published_date.split('T')[0],
            data: article
          }))
        ]

        // Sort by date (most recent first) and take top 10
        combined.sort((a, b) => {
          const dateA = new Date(a.date)
          const dateB = new Date(b.date)
          return dateB.getTime() - dateA.getTime()
        })

        setRecentActivity(combined.slice(0, 10))
      } catch (err) {
        console.error('Error fetching recent activity:', err)
        // Don't set error state - just log it, this is supplementary content
      } finally {
        setActivityLoading(false)
      }
    }

    fetchRecentActivity()
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Hero Skeleton */}
        <div className="space-y-4">
          <Skeleton className="h-12 w-3/4" />
          <Skeleton className="h-6 w-full" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-6 w-24" />
          </div>
        </div>

        {/* Content Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-96 w-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-96 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  // Format time ago
  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays}d ago`
    if (diffHours > 0) return `${diffHours}h ago`
    if (diffMins > 0) return `${diffMins}m ago`
    return 'just now'
  }

  // Format date for display
  const formatDate = (dateString: string): string => {
    const parts = dateString.split('-')
    if (parts.length !== 3) return dateString

    const [year, month, day] = parts

    // Handle partial dates (00 for unknown day/month)
    if (day === '00' && month === '00') {
      return year
    } else if (day === '00') {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      return `${monthNames[parseInt(month) - 1]} ${year}`
    }

    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Category colors for timeline events
  const categoryColors: Record<string, string> = {
    biographical: 'bg-blue-100 text-blue-800 border-blue-300',
    case: 'bg-red-100 text-red-800 border-red-300',
    documents: 'bg-green-100 text-green-800 border-green-300',
    default: 'bg-gray-100 text-gray-800 border-gray-300',
  }

  const getCategoryColor = (category: string): string => {
    return categoryColors[category] || categoryColors.default
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'biographical':
        return <Users className="h-3 w-3" />
      case 'case':
        return <FileText className="h-3 w-3" />
      case 'documents':
        return <FileText className="h-3 w-3" />
      default:
        return <Clock className="h-3 w-3" />
    }
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          The Epstein Archive
        </h1>
        <p className="text-xl text-muted-foreground">
          A comprehensive digital archive documenting Jeffrey Epstein's network through public records
        </p>

        {/* Key Statistics Badges */}
        {stats && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="text-sm">
              <Users className="h-3 w-3 mr-1" />
              {stats.total_entities?.toLocaleString()} Entities
            </Badge>
            <Badge variant="secondary" className="text-sm">
              <Plane className="h-3 w-3 mr-1" />
              {stats.flight_count?.toLocaleString() || 0} Flight Logs
            </Badge>
            <Badge variant="secondary" className="text-sm">
              <FileText className="h-3 w-3 mr-1" />
              {stats.total_documents?.toLocaleString()} Documents
            </Badge>
            <Badge variant="secondary" className="text-sm">
              <Network className="h-3 w-3 mr-1" />
              {stats.network_nodes?.toLocaleString() || 0} Network Nodes
            </Badge>
          </div>
        )}
      </div>

      {/* Dashboard Cards Section */}
      <div className="my-12">
        <DashboardCards stats={stats} loading={loading} error={!!error} />
      </div>

      {/* Recent Activity Section */}
      <div className="my-12">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Recent Activity
                </CardTitle>
                <CardDescription>
                  Latest timeline events and news coverage
                </CardDescription>
              </div>
              <Link to="/timeline" className="text-sm text-primary hover:underline">
                View Full Timeline →
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {activityLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-start gap-3 pb-4 border-b last:border-0">
                    <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentActivity.length > 0 ? (
              <div className="space-y-4">
                {recentActivity.map((item, index) => {
                  if (item.type === 'timeline') {
                    const event = item.data as TimelineEvent
                    return (
                      <div
                        key={`timeline-${index}`}
                        className="flex items-start gap-3 pb-4 border-b last:border-0 last:pb-0 hover:bg-accent/50 -mx-2 px-2 py-2 rounded-md transition-colors"
                      >
                        <div className="flex-shrink-0 mt-1">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            {getCategoryIcon(event.category)}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0 space-y-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant="outline" className={getCategoryColor(event.category)}>
                              {event.category}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(event.date)}
                            </span>
                          </div>
                          <Link
                            to="/timeline"
                            className="block group"
                          >
                            <h4 className="font-medium text-sm leading-tight group-hover:text-primary transition-colors">
                              {event.title}
                            </h4>
                          </Link>
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                            {event.description}
                          </p>
                          {event.related_entities.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {event.related_entities.slice(0, 3).map((entity, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {formatEntityName(entity)}
                                </Badge>
                              ))}
                              {event.related_entities.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{event.related_entities.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  } else {
                    const article = item.data as NewsArticle
                    return (
                      <div
                        key={`news-${index}`}
                        className="flex items-start gap-3 pb-4 border-b last:border-0 last:pb-0 hover:bg-accent/50 -mx-2 px-2 py-2 rounded-md transition-colors"
                      >
                        <div className="flex-shrink-0 mt-1">
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <Newspaper className="h-4 w-4 text-blue-600" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0 space-y-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-300">
                              <Newspaper className="h-3 w-3 mr-1" />
                              News
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(article.published_date.split('T')[0])}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              • {article.publication}
                            </span>
                          </div>
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block group"
                          >
                            <h4 className="font-medium text-sm leading-tight group-hover:text-primary transition-colors flex items-center gap-1">
                              {article.title}
                              <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </h4>
                          </a>
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                            {article.content_excerpt}
                          </p>
                          {article.entities_mentioned.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {article.entities_mentioned.slice(0, 3).map((entity, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {formatEntityName(entity)}
                                </Badge>
                              ))}
                              {article.entities_mentioned.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{article.entities_mentioned.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  }
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No recent activity found</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* About Section (2/3 width) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>About This Archive</CardTitle>
              <CardDescription>
                {about && `Last updated ${formatTimeAgo(about.updated_at)}`}
              </CardDescription>
            </CardHeader>
            <CardContent className="max-h-[600px] overflow-y-auto">
              {about && (
                <div className="prose prose-slate dark:prose-invert max-w-none prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-p:leading-relaxed prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-strong:text-foreground prose-code:text-sm prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                    h1: ({ node, ...props }) => (
                      <h1 className="text-3xl font-bold mb-4 mt-6 first:mt-0" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2 className="text-2xl font-semibold mb-3 mt-6" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3 className="text-xl font-semibold mb-2 mt-4" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                      <p className="mb-4 leading-relaxed" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside mb-4 space-y-2" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />
                    ),
                    a: ({ node, ...props }) => (
                      <a
                        className="text-primary hover:underline font-medium"
                        target="_blank"
                        rel="noopener noreferrer"
                        {...props}
                      />
                    ),
                    code: ({ node, inline, ...props }: any) =>
                      inline ? (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                      ) : (
                        <code className="block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto" {...props} />
                      ),
                    }}
                  >
                    {about.content}
                  </ReactMarkdown>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Updates Section (1/3 width) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Latest Updates
              </CardTitle>
              <CardDescription>
                Recent changes to the archive
              </CardDescription>
            </CardHeader>
            <CardContent className="max-h-[600px] overflow-y-auto">
              {updates && updates.commits.length > 0 ? (
                <div className="space-y-4">
                  {updates.commits.map((commit) => (
                    <div
                      key={commit.hash}
                      className="flex items-start gap-3 pb-4 border-b last:border-0 last:pb-0"
                    >
                      <GitCommit className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium leading-relaxed">
                          {commit.message}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          <Badge variant="outline" className="font-mono text-xs">
                            {commit.hash.substring(0, 7)}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {commit.author}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            •
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatTimeAgo(commit.time)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No recent updates available</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
