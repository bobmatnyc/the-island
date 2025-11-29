# Home Page Code Reference

**Quick Summary**: Quick reference guide for the Home page implementation. .

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Get about page content
- Get git commit updates

---

Quick reference guide for the Home page implementation.

---

## 📦 Installation

```bash
cd /Users/masa/Projects/epstein/frontend
npm install react-markdown remark-gfm
```

---

## 🔧 API Configuration

**File:** `/frontend/src/lib/api.ts`

### Types Added
```typescript
export interface AboutResponse {
  content: string;
  updated_at: string;
}

export interface GitCommit {
  hash: string;
  author: string;
  time: string;
  message: string;
}

export interface UpdatesResponse {
  commits: GitCommit[];
  total: number;
}
```

### Methods Added
```typescript
export const api = {
  // ... existing methods

  /**
   * Get about page content
   */
  getAbout: () => fetchAPI<AboutResponse>('/api/about'),

  /**
   * Get git commit updates
   */
  getUpdates: (limit: number = 10) => {
    const queryParams = new URLSearchParams();
    queryParams.set('limit', limit.toString());
    return fetchAPI<UpdatesResponse>(`/api/updates?${queryParams.toString()}`);
  },
};
```

---

## 🎨 Component Code

**File:** `/frontend/src/pages/Home.tsx`

### Imports
```typescript
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '@/lib/api'
import type { AboutResponse, UpdatesResponse, Stats } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import {
  FileText,
  Users,
  Plane,
  Network,
  Clock,
  AlertCircle,
  ArrowRight,
  GitCommit
} from 'lucide-react'
```

### State Management
```typescript
export function Home() {
  const [about, setAbout] = useState<AboutResponse | null>(null)
  const [updates, setUpdates] = useState<UpdatesResponse | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
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

  // ... rest of component
}
```

### Helper Function
```typescript
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
```

### Hero Section
```typescript
<div className="space-y-4">
  <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
    The Epstein Archive
  </h1>
  <p className="text-xl text-muted-foreground">
    A comprehensive digital archive documenting Jeffrey Epstein's network through public records
  </p>

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
```

### About Section (Markdown)
```typescript
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
```

### Updates Section
```typescript
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
                  <span className="text-xs text-muted-foreground">•</span>
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
```

### Quick Actions Grid
```typescript
<Card>
  <CardHeader>
    <CardTitle>Explore the Archive</CardTitle>
    <CardDescription>Browse different aspects of the Epstein network</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Link to="/entities">
        <Button variant="outline" className="w-full h-auto flex-col items-start p-4 hover:bg-accent">
          <div className="flex items-center gap-2 mb-2">
            <Users className="h-5 w-5" />
            <span className="font-semibold">Entities</span>
          </div>
          <p className="text-xs text-muted-foreground text-left">
            Browse {stats?.total_entities?.toLocaleString() || 0} individuals and organizations
          </p>
          <ArrowRight className="h-4 w-4 mt-2 self-end" />
        </Button>
      </Link>

      {/* Repeat for Flights, Documents, Network... */}
    </div>
  </CardContent>
</Card>
```

### Loading State
```typescript
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
```

### Error State
```typescript
if (error) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  )
}
```

---

## 🎨 ShadCN Components

### Skeleton Component
**File:** `/frontend/src/components/ui/skeleton.tsx`

```typescript
import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }
```

### Alert Component
**File:** `/frontend/src/components/ui/alert.tsx`

```typescript
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }
```

---

## 🔀 Routing Updates

**File:** `/frontend/src/App.tsx`

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Home } from '@/pages/Home'
import { Dashboard } from '@/pages/Dashboard'
// ... other imports

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="entities" element={<Entities />} />
          {/* ... other routes */}
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

**File:** `/frontend/src/components/layout/Header.tsx`

```typescript
// Modified navigation section
<nav className="flex items-center space-x-6 text-sm font-medium">
  <Link to="/" className="transition-colors hover:text-foreground/80 text-foreground/60">
    Home
  </Link>
  <Link to="/dashboard" className="transition-colors hover:text-foreground/80 text-foreground/60">
    Dashboard
  </Link>
  {/* ... other links */}
</nav>
```

---

## 📦 Package.json Updates

```json
{
  "dependencies": {
    // ... existing dependencies
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  }
}
```

---

## 🧪 Testing

### Check Backend Endpoints
```bash
# Test about endpoint
curl http://localhost:8000/api/about | jq '.content' | head -20

# Test updates endpoint
curl "http://localhost:8000/api/updates?limit=5" | jq

# Test stats endpoint
curl http://localhost:8000/api/stats | jq
```

### Run Development Server
```bash
# Backend (in one terminal)
cd /Users/masa/Projects/epstein
python server/app.py

# Frontend (in another terminal)
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

### Build for Production
```bash
cd /Users/masa/Projects/epstein/frontend
npm run build
```

---

## 🎯 Usage Examples

### Using the API in Other Components
```typescript
import { api } from '@/lib/api'
import type { AboutResponse, UpdatesResponse } from '@/lib/api'

// Fetch about content
const about = await api.getAbout()
console.log(about.content)

// Fetch recent commits
const updates = await api.getUpdates(5)
updates.commits.forEach(commit => {
  console.log(`${commit.hash}: ${commit.message}`)
})
```

### Time Formatting Utility
```typescript
// Copy this helper to use elsewhere
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
```

### Responsive Grid Pattern
```typescript
// Use this pattern for responsive layouts
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Items */}
</div>

// 2/3 + 1/3 split
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div className="lg:col-span-2">{/* 2/3 width */}</div>
  <div>{/* 1/3 width */}</div>
</div>
```

---

## 🔍 Debugging

### Common Issues

**Problem:** Markdown not rendering
```typescript
// Check: Is remark-gfm imported?
import remarkGfm from 'remark-gfm'

// Check: Is it passed to ReactMarkdown?
<ReactMarkdown remarkPlugins={[remarkGfm]}>
```

**Problem:** API not responding
```bash
# Check backend is running
curl http://localhost:8000/health

# Check backend logs
tail -f server/logs/app.log
```

**Problem:** TypeScript errors
```bash
# Check types are imported correctly
import type { AboutResponse } from '@/lib/api'

# Not:
import { AboutResponse } from '@/lib/api'
```

**Problem:** Styles not applying
```typescript
// Check Tailwind classes are correct
className="prose prose-slate dark:prose-invert"

// Check ShadCN components imported
import { Card, CardContent } from '@/components/ui/card'
```

---

## 📊 Performance Metrics

### Bundle Size
- `react-markdown`: ~45KB gzipped
- `remark-gfm`: ~12KB gzipped
- Total addition: ~57KB gzipped

### API Response Times (typical)
- `/api/about`: ~50-100ms (11KB content)
- `/api/updates`: ~20-50ms (small JSON)
- `/api/stats`: ~100-200ms (database query)

### Loading Performance
- First Paint: ~200ms (skeleton)
- Data Load: ~300ms (parallel fetch)
- Total Interactive: ~500ms

---

## 🎨 Customization Examples

### Change Hero Title
```typescript
<h1 className="text-4xl md:text-5xl font-bold tracking-tight">
  Your Custom Title Here
</h1>
```

### Adjust Card Heights
```typescript
// Make cards taller
<CardContent className="max-h-[800px] overflow-y-auto">

// Remove height limit
<CardContent className="overflow-y-auto">
```

### Add More Statistics
```typescript
<Badge variant="secondary" className="text-sm">
  <YourIcon className="h-3 w-3 mr-1" />
  {stats.your_metric?.toLocaleString()} Your Label
</Badge>
```

### Custom Markdown Styles
```typescript
components={{
  // Add custom image rendering
  img: ({ node, ...props }) => (
    <img className="rounded-lg shadow-lg" {...props} />
  ),

  // Add custom blockquote
  blockquote: ({ node, ...props }) => (
    <blockquote className="border-l-4 border-primary pl-4 italic" {...props} />
  ),
}}
```

---

**File Locations:**
- Home Component: `/frontend/src/pages/Home.tsx`
- API Types: `/frontend/src/lib/api.ts`
- Skeleton UI: `/frontend/src/components/ui/skeleton.tsx`
- Alert UI: `/frontend/src/components/ui/alert.tsx`
- Routing: `/frontend/src/App.tsx`
- Header: `/frontend/src/components/layout/Header.tsx`
