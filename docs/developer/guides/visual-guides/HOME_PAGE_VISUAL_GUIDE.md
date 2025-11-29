# Home Page Visual Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- 🎨 Component Hierarchy

---

## 🎨 Component Hierarchy

```
┌──────────────────────────────────────────────────────────────────┐
│                         HEADER (sticky)                          │
│  [Epstein Archive] | Home | Dashboard | Entities | Timeline...   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      HERO SECTION                                │
│                                                                  │
│  The Epstein Archive                                             │
│  A comprehensive digital archive documenting...                  │
│                                                                  │
│  [👥 1,639 Entities] [✈️ 0 Flight Logs] [📄 305 Documents]      │
│  [🔗 387 Network Nodes]                                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┬────────────────────────────┐
│  ABOUT THIS ARCHIVE (2/3 width)     │  LATEST UPDATES (1/3)      │
│  ────────────────────────────       │  ─────────────────────     │
│  Last updated 16 hours ago          │  Recent changes            │
│                                     │                            │
│  ┌────────────────────────────────┐ │  ┌──────────────────────┐ │
│  │ # The Epstein Archive          │ │  │ 🔀 [d93f750]         │ │
│  │                                │ │  │ docs: add migration  │ │
│  │ ## Overview                    │ │  │ Bob M. • 16h ago     │ │
│  │                                │ │  │                      │ │
│  │ The Epstein Archive is a      │ │  │ ──────────────────── │ │
│  │ comprehensive digital...       │ │  │                      │ │
│  │                                │ │  │ 🔀 [d7dc8ed]         │ │
│  │ ## Purpose                     │ │  │ docs: add React plan │ │
│  │                                │ │  │ Bob M. • 16h ago     │ │
│  │ **Why This Archive Exists:**   │ │  │                      │ │
│  │ - Transparency                 │ │  │ ──────────────────── │ │
│  │ - Research                     │ │  │                      │ │
│  │ - Accountability               │ │  │ 🔀 [a34dd53]         │ │
│  │                                │ │  │ fix: add defensive   │ │
│  │ [Scrollable content...]        │ │  │ Bob M. • 16h ago     │ │
│  │                                │ │  │                      │ │
│  └────────────────────────────────┘ │  └──────────────────────┘ │
│  ↕ max-height: 600px, scrollable   │  ↕ max-height: 600px      │
└─────────────────────────────────────┴────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    EXPLORE THE ARCHIVE                           │
│  Browse different aspects of the Epstein network                 │
│                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ 👥 Entities  │ ✈️ Flights   │ 📄 Documents │ 🔗 Network   │ │
│  │              │              │              │              │ │
│  │ Browse 1,639 │ Explore 0    │ Search 305   │ Visualize    │ │
│  │ individuals  │ documented   │ source docs  │ connections  │ │
│  │              │ flights      │              │              │ │
│  │          [→] │          [→] │          [→] │          [→] │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      CHAT SIDEBAR (right)                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📱 Responsive Breakpoints

### Mobile (<768px)
```
┌───────────────────────┐
│      HERO             │
│  [Epstein Archive]    │
│  [Stats badges wrap]  │
└───────────────────────┘

┌───────────────────────┐
│  ABOUT (full width)   │
│  [Markdown content]   │
└───────────────────────┘

┌───────────────────────┐
│  UPDATES (full width) │
│  [Git commits]        │
└───────────────────────┘

┌───────────────────────┐
│  ACTIONS (stacked)    │
│  [Entities]           │
│  [Flights]            │
│  [Documents]          │
│  [Network]            │
└───────────────────────┘
```

### Tablet (768px-1024px)
```
┌─────────────────────────────┐
│         HERO                │
│  [Epstein Archive]          │
│  [Stats badges in 2 rows]   │
└─────────────────────────────┘

┌─────────────────────────────┐
│  ABOUT (full width)         │
│  [Markdown content]         │
└─────────────────────────────┘

┌─────────────────────────────┐
│  UPDATES (full width)       │
│  [Git commits]              │
└─────────────────────────────┘

┌──────────────┬──────────────┐
│  ENTITIES    │  FLIGHTS     │
├──────────────┼──────────────┤
│  DOCUMENTS   │  NETWORK     │
└──────────────┴──────────────┘
```

### Desktop (>1024px)
```
Full layout as shown in main diagram above
```

---

## 🎨 Color Scheme (Dark Mode)

```
Background Colors:
├─ background: hsl(222.2 84% 4.9%)        [Main dark background]
├─ card: hsl(222.2 84% 4.9%)              [Card backgrounds]
└─ muted: hsl(217.2 32.6% 17.5%)          [Muted backgrounds]

Text Colors:
├─ foreground: hsl(210 40% 98%)           [Primary text]
├─ muted-foreground: hsl(215 20.2% 65.1%) [Secondary text]
└─ primary: hsl(217.2 91.2% 59.8%)        [Links, highlights]

Border Colors:
└─ border: hsl(217.2 32.6% 17.5%)         [Card borders]
```

---

## 🖼️ Component Styling Details

### Hero Section
```tsx
<div className="space-y-4">
  <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
    The Epstein Archive
  </h1>

  <p className="text-xl text-muted-foreground">
    A comprehensive digital archive...
  </p>

  <div className="flex flex-wrap gap-2">
    <Badge variant="secondary">
      <Users className="h-3 w-3 mr-1" />
      1,639 Entities
    </Badge>
    {/* More badges... */}
  </div>
</div>
```

### About Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>About This Archive</CardTitle>
    <CardDescription>Last updated 16h ago</CardDescription>
  </CardHeader>

  <CardContent className="max-h-[600px] overflow-y-auto">
    <div className="prose dark:prose-invert">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  </CardContent>
</Card>
```

### Updates Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>
      <Clock className="h-5 w-5" />
      Latest Updates
    </CardTitle>
  </CardHeader>

  <CardContent className="max-h-[600px] overflow-y-auto">
    {commits.map(commit => (
      <div className="flex gap-3 pb-4 border-b">
        <GitCommit className="h-4 w-4" />
        <div>
          <p>{commit.message}</p>
          <Badge variant="outline">{commit.hash}</Badge>
          <span>{commit.author} • {commit.time}</span>
        </div>
      </div>
    ))}
  </CardContent>
</Card>
```

### Quick Action Cards
```tsx
<Button variant="outline" className="w-full h-auto flex-col items-start p-4">
  <div className="flex items-center gap-2 mb-2">
    <Users className="h-5 w-5" />
    <span className="font-semibold">Entities</span>
  </div>
  <p className="text-xs text-muted-foreground text-left">
    Browse 1,639 individuals and organizations
  </p>
  <ArrowRight className="h-4 w-4 mt-2 self-end" />
</Button>
```

---

## 🔄 Loading States

### Skeleton Pattern
```tsx
{loading && (
  <div className="space-y-8">
    {/* Hero Skeleton */}
    <div className="space-y-4">
      <Skeleton className="h-12 w-3/4" />  {/* Title */}
      <Skeleton className="h-6 w-full" />   {/* Subtitle */}
      <div className="flex gap-2">
        <Skeleton className="h-6 w-24" />   {/* Badge */}
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-6 w-24" />
      </div>
    </div>

    {/* Content Skeleton */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Skeleton className="h-96 w-full" />
      </div>
      <Skeleton className="h-96 w-full" />
    </div>
  </div>
)}
```

---

## ⚠️ Error States

### Error Display
```tsx
{error && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>
      {error}
    </AlertDescription>
  </Alert>
)}
```

---

## 📊 Data Flow

```
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │
       ├─ useEffect() triggered on mount
       │
       ├─ Promise.all([
       │     api.getAbout(),
       │     api.getUpdates(10),
       │     api.getStats()
       │   ])
       │
       ├─ GET /api/about
       │  └─> {content, updated_at}
       │
       ├─ GET /api/updates?limit=10
       │  └─> {commits: [...], total}
       │
       └─ GET /api/stats
          └─> {total_entities, total_documents, ...}

       ↓

┌──────────────┐
│ State Update │
│ - setAbout() │
│ - setUpdates()│
│ - setStats() │
│ - setLoading()│
└──────────────┘

       ↓

┌──────────────┐
│   Render     │
│ - Hero       │
│ - About      │
│ - Updates    │
│ - Actions    │
└──────────────┘
```

---

## 🎯 Interactive Elements

### Hover States
```css
/* Navigation Cards */
.hover:bg-accent          /* Light background on hover */
.transition-colors        /* Smooth color transition */

/* Header Links */
.hover:text-foreground/80 /* Slightly fade on hover */

/* Quick Action Cards */
Button[variant="outline"]:hover
  └─ Background: accent color
  └─ Transform: none (no scale)
  └─ Cursor: pointer
```

### Focus States
```css
/* All interactive elements */
outline-none              /* Remove default */
focus-visible:ring-2      /* Custom focus ring */
focus-visible:ring-primary/* Primary color ring */
```

---

## 📐 Spacing System

```
Vertical Rhythm:
├─ space-y-8  [Hero to Content]        32px
├─ space-y-6  [Content sections]       24px
├─ space-y-4  [Card internals]         16px
├─ gap-6      [Grid gaps]              24px
├─ gap-4      [Card grids]             16px
├─ gap-3      [Commit items]           12px
└─ gap-2      [Badges, small items]     8px

Padding:
├─ p-6        [Card padding]           24px
├─ p-4        [Button padding]         16px
└─ py-6       [Main container]         24px vertical
```

---

## 🔤 Typography Scale

```
Font Sizes:
├─ text-4xl md:text-5xl    [Hero title]        36px / 48px
├─ text-xl                 [Subtitle]          20px
├─ text-lg                 [Large text]        18px
├─ text-sm                 [Body text]         14px
└─ text-xs                 [Small text]        12px

Font Weights:
├─ font-bold               [Headings]          700
├─ font-semibold           [Sub-headings]      600
└─ font-medium             [Medium text]       500
```

---

## 🎨 Badge Variants

### Secondary (Stats)
```tsx
<Badge variant="secondary">
  <Icon className="h-3 w-3 mr-1" />
  1,639 Entities
</Badge>
```
**Style:** Gray background, subtle border

### Outline (Commit Hashes)
```tsx
<Badge variant="outline" className="font-mono text-xs">
  d93f750
</Badge>
```
**Style:** Transparent background, border only, monospace font

---

## 📏 Content Constraints

```
Max Heights:
├─ About Card:    max-h-[600px] overflow-y-auto
├─ Updates Card:  max-h-[600px] overflow-y-auto
└─ Main Content:  container mx-auto (1280px max)

Max Widths:
├─ Prose:         max-w-none (full card width)
└─ Container:     container (responsive, 1280px max)
```

---

## 🌙 Dark Mode Specifics

### Markdown Prose
```tsx
className="prose prose-slate dark:prose-invert"
```

**Dark Mode Changes:**
- Headings: white text
- Body text: light gray
- Links: blue (primary color)
- Code blocks: darker muted background
- Borders: subtle gray

### Component Themes
All components automatically adapt via ShadCN theming system.

---

## 🔗 Navigation Flow

```
Home (/)
  ├─> Entities (/entities)
  ├─> Flights (/flights)
  ├─> Documents (/documents)
  ├─> Network (/network)
  └─> Dashboard (/dashboard)

Header Navigation:
  ├─ Home (/)
  ├─ Dashboard (/dashboard)
  ├─ Entities (/entities)
  ├─ Timeline (/timeline)
  ├─ Flights (/flights)
  ├─ Visualizations (dropdown)
  │   ├─ Network Graph
  │   ├─ Adjacency Matrix
  │   └─ Calendar Heatmap
  └─ Documents (/documents)
```

---

## 🎨 Icon Library (Lucide React)

```
Icons Used:
├─ Users         [Entities badge]
├─ Plane         [Flights badge]
├─ FileText      [Documents badge]
├─ Network       [Network badge]
├─ Clock         [Updates header]
├─ GitCommit     [Commit items]
├─ ArrowRight    [Action cards]
├─ AlertCircle   [Error alerts]
└─ ChevronDown   [Dropdown menus]
```

---

**Design System:** ShadCN UI + Tailwind CSS
**Component Library:** Radix UI (headless)
**Icon Library:** Lucide React
**Markdown Renderer:** react-markdown + remark-gfm
**Framework:** React 19 + TypeScript + Vite
