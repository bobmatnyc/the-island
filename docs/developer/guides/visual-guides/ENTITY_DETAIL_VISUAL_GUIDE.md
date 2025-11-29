# Entity Detail Page - Visual Layout Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Navigation Flow Diagram

---

## Navigation Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   ENTITY DETAIL PAGE                       │
└────────────────────────────────────────────────────────────┘

┌─────────────────────── HEADER CARD ────────────────────────┐
│  [User Icon]  Jeffrey Epstein                    [Person]  │
│               Also known as: Je Je Epstein                  │
│                                                             │
│  [Billionaire] [Black Book] [Multiple Sources]             │
└─────────────────────────────────────────────────────────────┘

                    ┌─── VIEW MODE ───┐
                    │                 │
            ┌───────▼─────┐   ┌──────▼──────┐
            │ LINKS VIEW  │   │  BIO VIEW   │
            │  (default)  │   │ (expanded)  │
            └─────────────┘   └─────────────┘


═══════════════════════════════════════════════════════════════
                        LINKS VIEW
═══════════════════════════════════════════════════════════════

┌────────────────────┐  ┌────────────────────┐
│  [User Icon]       │  │  [Eye Icon]        │
│  Bio               │  │  Docs              │
│  View full bio →   │  │  45 items →        │
│                    │  │                    │
│  [Click: Toggle]   │  │  [Click: Navigate] │
└────────────────────┘  └────────────────────┘
         │                       │
         │                       └──→ /documents?entity=Jeffrey%20Epstein
         │
         └──→ Toggle to Bio View

┌────────────────────┐  ┌────────────────────┐
│  [Plane Icon]      │  │  [Network Icon]    │
│  Flights           │  │  Network           │
│  127 items →       │  │  89 items →        │
│                    │  │                    │
│  [Click: Navigate] │  │  [Click: Navigate] │
└────────────────────┘  └────────────────────┘
         │                       │
         │                       └──→ /network?focus=Jeffrey%20Epstein
         │
         └──→ /flights?passenger=Jeffrey%20Epstein


┌──────────────── TOP CONNECTIONS CARD ──────────────────┐
│  [Users Icon]  Top Connections                         │
│                                                         │
│  → Ghislaine Maxwell              [123 flights]        │
│  → Prince Andrew                  [89 flights]         │
│  → Bill Clinton                   [67 flights]         │
│  → ...                                                  │
└─────────────────────────────────────────────────────────┘

┌──────────────── NEWS COVERAGE CARD ────────────────────┐
│  [Newspaper Icon]  News Coverage     [10 articles]     │
│                                                         │
│  ┌────────────────┐  ┌────────────────┐               │
│  │ Article Card 1 │  │ Article Card 2 │               │
│  └────────────────┘  └────────────────┘               │
│                                                         │
│  [ View All News for Jeffrey Epstein → ]               │
└─────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════
                         BIO VIEW
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  [User Icon]  Jeffrey Epstein              [← Back]         │
│               [Person] [Billionaire] [Black Book]           │
│                                                             │
│  Biography                                                  │
│  ───────────────────────────────────────────────────────── │
│  Jeffrey Epstein appears in the Epstein archive             │
│  documentation with 127 flights logged and 89 connections   │
│  in the network...                                          │
│                                                             │
│  Details                                                    │
│  ───────────────────────────────────────────────────────── │
│  Documents: 45    Flights: 127    Connections: 89          │
│                                                             │
│  Data Sources                                               │
│  ───────────────────────────────────────────────────────── │
│  [flight_logs] [black_book] [court_documents]              │
│  All information is sourced from publicly available docs    │
│                                                             │
│  Document Types                                             │
│  ───────────────────────────────────────────────────────── │
│  Flight Logs                           [25 documents]       │
│  Court Documents                       [15 documents]       │
│  Depositions                          [5 documents]        │
└─────────────────────────────────────────────────────────────┘
```

## Navigation Patterns

### 1. Bio Card Click Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ LINKS VIEW   │      │   CLICK      │      │  BIO VIEW    │
│              │─────▶│   "Bio"      │─────▶│              │
│ 4 cards      │      │   Card       │      │ Full bio     │
│ visible      │      │              │      │ + metadata   │
└──────────────┘      └──────────────┘      └──────────────┘
                                                    │
                                                    │ Click
                                                    │ "Back"
                                                    ▼
                                            ┌──────────────┐
                                            │ LINKS VIEW   │
                                            │              │
                                            │ Returns to   │
                                            │ cards        │
                                            └──────────────┘
```

### 2. Docs Card Click Flow

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ ENTITY DETAIL    │      │   CLICK "Docs"   │      │ DOCUMENTS PAGE   │
│                  │─────▶│                  │─────▶│                  │
│ Docs: 45 items   │      │ Navigate with    │      │ ?entity=Jeffrey  │
│                  │      │ entity filter    │      │ Epstein          │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                             │
                                                             │ Auto-apply
                                                             ▼
                                                     ┌──────────────────┐
                                                     │ FILTERED VIEW    │
                                                     │                  │
                                                     │ Search: Jeffrey  │
                                                     │ Epstein          │
                                                     │                  │
                                                     │ [Document 1]     │
                                                     │ [Document 2]     │
                                                     └──────────────────┘
```

### 3. Flights Card Click Flow

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ ENTITY DETAIL    │      │ CLICK "Flights"  │      │ FLIGHTS PAGE     │
│                  │─────▶│                  │─────▶│                  │
│ Flights: 127     │      │ Navigate with    │      │ ?passenger=      │
│                  │      │ passenger filter │      │ Jeffrey Epstein  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                             │
                                                             │ Auto-apply
                                                             ▼
                                                     ┌──────────────────┐
                                                     │ FILTERED VIEW    │
                                                     │                  │
                                                     │ Passenger:       │
                                                     │ Jeffrey Epstein  │
                                                     │                  │
                                                     │ [Flight 1]       │
                                                     │ [Flight 2]       │
                                                     └──────────────────┘
```

### 4. Network Card Click Flow

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ ENTITY DETAIL    │      │ CLICK "Network"  │      │ NETWORK PAGE     │
│                  │─────▶│                  │─────▶│                  │
│ Network: 89      │      │ Navigate with    │      │ ?focus=Jeffrey   │
│                  │      │ focus param      │      │ Epstein          │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                             │
                                                             │ Auto-select
                                                             │ + Center
                                                             │ + Zoom
                                                             ▼
                                                     ┌──────────────────┐
                                                     │ NETWORK GRAPH    │
                                                     │                  │
                                                     │     [Node]       │
                                                     │    ╱  │  ╲       │
                                                     │  [●] [●] [●]     │
                                                     │                  │
                                                     │ Centered on      │
                                                     │ Jeffrey Epstein  │
                                                     └──────────────────┘
```

## Card Hover States

### Default State
```
┌────────────────────┐
│  [Icon]            │
│  Label             │
│  Count →           │
│                    │
│  border: default   │
│  shadow: none      │
└────────────────────┘
```

### Hover State
```
┌────────────────────┐
│  [Icon]  ← scale   │
│  Label             │
│  Count → ← slide   │
│                    │
│  border: primary   │
│  shadow: md        │
└────────────────────┘
```

## Responsive Layout

### Desktop (≥1024px)
```
┌─────────────────────────────────────────────┐
│              HEADER CARD                    │
└─────────────────────────────────────────────┘

┌────────────────────┐  ┌────────────────────┐
│  Bio              │  │  Docs              │
└────────────────────┘  └────────────────────┘

┌────────────────────┐  ┌────────────────────┐
│  Flights          │  │  Network           │
└────────────────────┘  └────────────────────┘

2x2 Grid (50% each)
```

### Tablet (768px - 1023px)
```
┌─────────────────────────────────────────────┐
│              HEADER CARD                    │
└─────────────────────────────────────────────┘

┌────────────────────┐  ┌────────────────────┐
│  Bio              │  │  Docs              │
└────────────────────┘  └────────────────────┘

┌────────────────────┐  ┌────────────────────┐
│  Flights          │  │  Network           │
└────────────────────┘  └────────────────────┘

2x2 Grid (50% each)
```

### Mobile (<768px)
```
┌───────────────────────────┐
│      HEADER CARD          │
└───────────────────────────┘

┌───────────────────────────┐
│  Bio                      │
└───────────────────────────┘

┌───────────────────────────┐
│  Docs                     │
└───────────────────────────┘

┌───────────────────────────┐
│  Flights                  │
└───────────────────────────┘

┌───────────────────────────┐
│  Network                  │
└───────────────────────────┘

Single Column (100%)
```

## Icon Reference

```
Bio Card:       [User Icon]      - lucide-react/User
Docs Card:      [Eye Icon]       - lucide-react/Eye
Flights Card:   [Plane Icon]     - lucide-react/Plane
Network Card:   [Network Icon]   - lucide-react/Network
Arrow:          [→]              - lucide-react/ArrowRight
```

## Color Scheme

```
Card Background:     bg-card (theme-dependent)
Card Border:         border (default)
Card Border Hover:   border-primary
Text Primary:        text-foreground
Text Secondary:      text-muted-foreground
Icon Color:          text-primary (hover: scaled)
Badge Background:    bg-secondary
```

## Animation Timings

```
Card Hover:          transition-all duration-200
Icon Scale:          group-hover:scale-110 transition-transform duration-200
Arrow Slide:         group-hover:translate-x-1 transition-all duration-200
Bio Toggle:          instant (no animation)
Network Camera:      1000ms smooth animation
Network Zoom:        1000ms smooth animation
```

## Count Display Examples

```
Zero Count:        "0 items"     (still shown)
Single Count:      "1 item"      (singular)
Multiple Count:    "45 items"    (plural)
Large Count:       "1,234 items" (formatted with commas)
```

## URL Parameter Patterns

```
Documents:  /documents?entity={encodeURIComponent(name)}
            Example: /documents?entity=Jeffrey%20Epstein

Flights:    /flights?passenger={encodeURIComponent(name)}
            Example: /flights?passenger=Jeffrey%20Epstein

Network:    /network?focus={encodeURIComponent(name)}
            Example: /network?focus=Jeffrey%20Epstein
```

## Component Hierarchy

```
EntityDetail.tsx (Page)
├── Card (Header)
│   ├── Entity Name + Type Badge
│   ├── Name Variations
│   └── Special Badges
│
├── ViewMode = "links"
│   ├── EntityLinks.tsx
│   │   ├── LinkCard (Bio)
│   │   ├── LinkCard (Docs)
│   │   ├── LinkCard (Flights)
│   │   └── LinkCard (Network)
│   │
│   ├── Card (Top Connections)
│   │   └── Connection List
│   │
│   └── Card (News Coverage)
│       └── Article Cards
│
└── ViewMode = "bio"
    └── EntityBio.tsx
        ├── Header (Name + Type + Back)
        ├── Biography Section
        ├── Details Grid (Counts)
        ├── Data Sources
        └── Document Types
```

## State Management

```
Component State:
├── entity: Entity | null
├── viewMode: 'links' | 'bio'
├── newsArticles: NewsArticle[]
├── loading: boolean
├── newsLoading: boolean
└── error: string | null

Hook State (useEntityCounts):
├── counts: EntityCounts | null
├── loading: boolean
└── error: string | null

URL State (useSearchParams):
└── searchParams: URLSearchParams
```

---

*Visual Guide for Entity Detail Page Redesign*
*Generated by Claude Code*
*November 20, 2025*
