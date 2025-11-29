# News Feature - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  NewsPage   │  │ ArticleDetailPage│  │  EntityDetail    │  │
│  │   (/news)   │  │ (/news/:id)      │  │ (/entities/:name)│  │
│  └─────────────┘  └──────────────────┘  └──────────────────┘  │
│         │                   │                      │            │
│         └───────────────────┴──────────────────────┘            │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Shared Components                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ ArticleCard │  │ FilterPanel  │  │    NewsStats       │    │
│  │  (Full +    │  │ (Search +    │  │ (Charts + Metrics) │    │
│  │  Compact)   │  │  Filters)    │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐         ┌─────────────────────────┐       │
│  │   newsApi.ts    │         │   Utility Functions     │       │
│  │  - searchNews() │         │  - filterArticlesByEntity│      │
│  │  - getArticle() │         │  - sortArticlesByDate   │       │
│  │  - getSimilar() │         │  - getArticlesNearDate  │       │
│  │  - getStats()   │         └─────────────────────────┘       │
│  └─────────────────┘                                           │
│         │                                                       │
│  ┌─────────────────┐                                           │
│  │ useTimelineNews │   (Custom Hook)                           │
│  │  - Groups by    │                                           │
│  │    date         │                                           │
│  │  - Loading      │                                           │
│  │    states       │                                           │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GET  /api/rag/news-search?query=&filters...                   │
│  GET  /api/rag/similar-news/:id?limit=5                        │
│  GET  /api/news/list?publication=&entity=&limit=               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Data Layer (ChromaDB + RAG)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App (Router)
│
├── Layout
│   ├── Header (with /news link)
│   └── Outlet
│       │
│       ├── NewsPage
│       │   ├── FilterPanel
│       │   │   ├── Search Input
│       │   │   ├── Entity Filter
│       │   │   ├── Credibility Slider
│       │   │   ├── Date Range Picker
│       │   │   ├── Publication List
│       │   │   ├── Tag Selection
│       │   │   └── Active Filters
│       │   │
│       │   ├── NewsStats (conditional)
│       │   │   ├── Overview Cards
│       │   │   ├── Publications Chart
│       │   │   ├── Credibility Chart
│       │   │   └── Top Entities List
│       │   │
│       │   └── Article List
│       │       ├── ArticleCard (full)
│       │       ├── ArticleCard (full)
│       │       └── Pagination
│       │
│       ├── ArticleDetailPage
│       │   ├── Back Button
│       │   ├── Article Header
│       │   │   ├── Title
│       │   │   ├── Metadata Row
│       │   │   └── Credibility Badge
│       │   ├── Article Content
│       │   │   ├── Full Excerpt
│       │   │   ├── Action Buttons
│       │   │   └── Share Buttons
│       │   ├── Entity Mentions
│       │   ├── Topic Tags
│       │   └── Similar Articles
│       │       └── ArticleCard (full) × N
│       │
│       └── EntityDetail
│           ├── Entity Header
│           ├── Stats Grid
│           ├── Top Connections
│           └── News Coverage (new)
│               ├── Loading State
│               ├── Empty State
│               ├── Article Grid
│               │   └── ArticleCard (compact) × N
│               └── View All Button
```

## Data Flow

### 1. News Search Flow
```
User Input (search box)
    │
    ├─ Debounce (300ms)
    │
    ▼
FilterPanel onChange
    │
    ├─ Build NewsSearchParams
    ├─ Update URL query params
    │
    ▼
newsApi.searchNews()
    │
    ├─ Fetch /api/rag/news-search
    ├─ Convert search results to NewsArticle[]
    │
    ▼
NewsPage setState
    │
    ├─ Update articles array
    ├─ Reset pagination
    │
    ▼
Render ArticleCard components
```

### 2. Article Detail Flow
```
User clicks ArticleCard
    │
    ▼
Navigate to /news/:articleId
    │
    ▼
ArticleDetailPage useEffect
    │
    ├─ newsApi.getArticle(id)
    ├─ newsApi.getSimilarArticles(id, 5)
    │
    ▼
Display article + similar articles
```

### 3. Entity Integration Flow
```
EntityDetail page load
    │
    ├─ Load entity details (existing)
    │
    ▼
loadNewsArticles() (async, non-blocking)
    │
    ├─ newsApi.getArticlesByEntity(name, 10)
    ├─ Fallback: searchNews + filterArticlesByEntity
    ├─ sortArticlesByDate
    │
    ▼
Display News Coverage section
```

## State Management

### NewsPage State
```typescript
{
  articles: NewsArticle[],        // Current search results
  stats: NewsStats | null,        // Statistics data
  publications: string[],         // Available publications
  tags: string[],                 // Available tags
  loading: boolean,               // Loading indicator
  error: string | null,           // Error message
  currentPage: number,            // Pagination state
  showStats: boolean,             // Stats toggle
  filters: NewsSearchParams       // Active filters
}
```

### ArticleDetailPage State
```typescript
{
  article: NewsArticle | null,    // Main article
  similarArticles: NewsArticle[], // Related articles
  loading: boolean,               // Loading indicator
  error: string | null,           // Error message
  copied: boolean                 // Clipboard copy state
}
```

### EntityDetail State (News Section)
```typescript
{
  newsArticles: NewsArticle[],    // Entity-related articles
  newsLoading: boolean            // Loading indicator (separate)
}
```

## API Service Architecture

```typescript
newsApi
│
├── Core Methods
│   ├── fetchAPI<T>()              // Wrapper with error handling
│   └── convertSearchResultToArticle()  // Type conversion
│
├── Search & Retrieval
│   ├── searchNews(params)         // Main search
│   ├── getArticle(id)             // Single article
│   └── getSimilarArticles(id, limit)  // Related articles
│
├── Filtering & Aggregation
│   ├── getArticlesByEntity(name, limit)
│   ├── getArticlesByDateRange(start, end, limit)
│   ├── getArticlesNearDate(date, windowDays, limit)
│   ├── getPublications()          // All publications
│   ├── getTags()                  // All tags
│   └── getStats()                 // Statistics calculation
│
└── Helper Methods
    ├── getSources()               // Source metadata
    └── (Future expansion points)
```

## Filter Pipeline

```
Raw Articles Array
    │
    ├─ Text Search (query)
    │  └─ Backend RAG search (semantic)
    │
    ├─ Entity Filter (entity)
    │  └─ Backend: entities_mentioned field
    │
    ├─ Publication Filter (publication)
    │  └─ Backend: publication field
    │
    ├─ Credibility Filter (min_credibility)
    │  └─ Backend: credibility_score >= threshold
    │
    ├─ Date Range Filter (start_date, end_date)
    │  └─ Backend: published_date between dates
    │
    ├─ Tag Filter (tags)
    │  └─ Client-side: tags array intersection
    │
    └─ Limit & Offset
       └─ Backend pagination
```

## Type System

```typescript
Core Types
│
├── NewsArticle                    // Main article type
│   ├── id: string
│   ├── title: string
│   ├── publication: string
│   ├── author?: string
│   ├── published_date: string
│   ├── url: string
│   ├── archive_url?: string
│   ├── content_excerpt: string
│   ├── word_count: number
│   ├── entities_mentioned: string[]
│   ├── entity_mention_counts: Record<string, number>
│   ├── credibility_score: number
│   ├── tags: string[]
│   ├── language: string
│   └── access_type: string
│
├── NewsSearchParams               // Search filters
│   ├── query?: string
│   ├── entity?: string
│   ├── publication?: string
│   ├── start_date?: string
│   ├── end_date?: string
│   ├── min_credibility?: number
│   ├── tags?: string[]
│   ├── limit?: number
│   └── offset?: number
│
├── NewsStats                      // Statistics data
│   ├── total_articles: number
│   ├── date_range: { earliest, latest }
│   ├── publications: Array<{ name, count }>
│   ├── credibility_tiers: { high, medium, low }
│   ├── top_entities: Array<{ name, mention_count }>
│   └── timeline: Array<{ month, count }>
│
└── NewsSearchResult               // RAG API response
    ├── id: string
    ├── similarity: number
    ├── text_excerpt: string
    └── metadata: { ... }
```

## Routing Structure

```
/news
│
├── /news                          → NewsPage
│   └── Query params:
│       ├── ?query=arrest
│       ├── ?entity=Jeffrey+Epstein
│       ├── ?publication=NPR
│       └── ?min_credibility=0.8
│
├── /news/:articleId               → ArticleDetailPage
│   └── Params:
│       └── articleId (required)
│
└── /entities/:name                → EntityDetail
    └── Includes: News Coverage section
        └── Links: /news?entity=:name
```

## Performance Optimizations

### 1. Frontend Optimizations
```
- Debounced search input (300ms)
- Client-side pagination (20 per page)
- Lazy loading statistics dashboard
- Memoized filter calculations
- Efficient React re-renders
```

### 2. API Optimizations
```
- Limit default query results (20-100)
- Backend RAG semantic search
- ChromaDB vector indexing
- Cached publication/tag lists
- Parallel API calls (Promise.all)
```

### 3. Bundle Optimizations
```
- Code splitting (Recharts lazy loaded)
- Tree shaking (unused code removed)
- Minification (production build)
- Gzip compression (374kB)
```

## Error Handling Strategy

### Levels
```
1. API Level (newsApi.ts)
   └── try/catch → throw Error

2. Component Level (useEffect)
   └── try/catch → setState(error)

3. UI Level (render)
   └── Conditional: error ? <Alert /> : <Content />

4. Fallback Level
   └── Empty states, loading states
```

### Error Types
```
- Network errors (fetch failures)
- 404 Not Found (article not found)
- 500 Server errors (backend issues)
- Validation errors (invalid params)
- Timeout errors (slow responses)
```

## Testing Strategy

### Unit Tests (Future)
```
- newsApi service methods
- Utility functions (filtering, sorting)
- Type conversions
- Date calculations
```

### Integration Tests (Future)
```
- Component interactions
- Filter application
- Pagination behavior
- Navigation flows
```

### E2E Tests (Future)
```
- Search workflow
- Article detail view
- Entity page integration
- Cross-browser compatibility
```

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         CDN / Static Hosting            │
│  (Vercel, Netlify, S3 + CloudFront)     │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│        React SPA (frontend/dist)        │
│  - index.html                           │
│  - assets/index-*.js (1.2MB gzipped)    │
│  - assets/index-*.css (41KB)            │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Backend API Server              │
│     (http://localhost:8000)             │
│  - FastAPI application                  │
│  - RAG endpoints                        │
│  - ChromaDB integration                 │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          ChromaDB Database              │
│  - Vector embeddings                    │
│  - News article metadata                │
│  - Semantic search index                │
└─────────────────────────────────────────┘
```

## Scalability Considerations

### Current Limits
- Client-side pagination: ~1000 articles
- Statistics calculation: All articles in memory
- No caching layer (refetch on every filter change)

### Future Scaling
1. **Backend Pagination**: Implement true server-side pagination
2. **Caching**: Add Redis for statistics/filter lists
3. **Infinite Scroll**: Replace client pagination
4. **CDN**: Cache API responses for public data
5. **Database Indexing**: Optimize ChromaDB queries

## Security Considerations

### Implemented
- No sensitive data in frontend
- External links open in new tab (rel="noopener noreferrer")
- Type-safe API calls
- Input sanitization (React XSS protection)

### Future Enhancements
- Rate limiting on API calls
- CSRF token for mutations
- Content Security Policy headers
- API authentication/authorization

## Monitoring & Analytics

### Recommended Metrics
- Page load time
- Search response time
- Error rate by endpoint
- Most searched queries
- Most viewed articles
- Filter usage patterns
- User navigation paths

### Integration Points
- Google Analytics / Plausible
- Sentry (error tracking)
- LogRocket (session replay)
- Custom backend logging

---

**Architecture Version**: 1.0
**Last Updated**: 2025-11-20
**Status**: Production Ready
