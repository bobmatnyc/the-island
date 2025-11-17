# Svelte 5 Migration Plan

**Incremental Migration Strategy for Epstein Archive Web UI**

**Goal**: Migrate from vanilla JavaScript to Svelte 5 with minimal disruption, maximum ROI.

---

## Migration Philosophy

### Incremental Over Big Bang

**Approach**: Replace components incrementally while keeping vanilla JS functional.

**Benefits**:
- ✅ **Low risk**: Rollback individual components if issues arise
- ✅ **Continuous deployment**: Ship improvements weekly
- ✅ **Parallel work**: Team can work on different components
- ✅ **Learning curve**: Gradual Svelte 5 adoption

**Rejected Alternative**: Full rewrite
- ❌ **High risk**: All or nothing deployment
- ❌ **Long timeline**: 6-8 weeks before first deployment
- ❌ **Testing burden**: Entire app must be QA'd at once

---

## Phase 1: Foundation (Week 1)

### Goals
- ✅ SvelteKit project initialized
- ✅ TypeScript configured
- ✅ Authentication working
- ✅ API proxy to existing backend

### Tasks

#### 1.1 Initialize SvelteKit Project

```bash
# Create SvelteKit app
npm create svelte@latest epstein-archive-svelte

# Choose options:
# - Template: Skeleton project
# - TypeScript: Yes
# - ESLint: Yes
# - Prettier: Yes
# - Playwright: Yes
# - Vitest: Yes
```

**Configuration**:

```typescript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    alias: {
      '$lib': './src/lib',
      '$components': './src/lib/components'
    }
  },
  compilerOptions: {
    runes: true // Enable Svelte 5 Runes
  }
};

export default config;
```

```json
// tsconfig.json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "types": ["vite/client"]
  }
}
```

#### 1.2 Create Type Definitions

```typescript
// src/lib/types.ts
export interface Entity {
  name: string;
  connection_count: number;
  total_documents: number;
  flight_count?: number;
  is_billionaire: boolean;
  entity_type: 'person' | 'organization' | 'location';
}

export interface NetworkNode {
  id: string;
  connection_count: number;
  total_documents: number;
  is_billionaire: boolean;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface NetworkEdge {
  source: NetworkNode | string;
  target: NetworkNode | string;
  weight: number;
}

export interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  description: string;
  type: 'legal' | 'travel' | 'financial' | 'personal';
  source_name: string;
  source_url: string;
  entities?: string[];
  documents?: string[];
}

export interface StatsResponse {
  total_entities: number;
  total_documents: number;
  total_connections: number;
  billionaire_count: number;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface Source {
  name: string;
  total: number;
  downloaded: number;
  ocr_completed: number;
  classified: number;
  verified: number;
}
```

#### 1.3 Create API Client

```typescript
// src/lib/api/client.ts
const API_BASE = '/api';

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('sessionToken') ||
                sessionStorage.getItem('sessionToken');

  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Redirect to login on auth failure
      localStorage.removeItem('sessionToken');
      sessionStorage.removeItem('sessionToken');
      window.location.href = '/login';
    }
    throw new APIError(response.status, `API error: ${response.statusText}`);
  }

  return response.json();
}

// Entity endpoints
export async function loadEntities(): Promise<Entity[]> {
  const data = await fetchWithAuth<{ entities: Entity[] }>('/entities');
  return data.entities;
}

export async function searchEntities(query: string): Promise<Entity[]> {
  const data = await fetchWithAuth<{ entities: Entity[] }>(
    `/entities/search?q=${encodeURIComponent(query)}`
  );
  return data.entities;
}

// Network endpoints
export async function loadNetworkData(): Promise<NetworkData> {
  return fetchWithAuth<NetworkData>('/network');
}

// Stats endpoints
export async function loadStats(): Promise<StatsResponse> {
  return fetchWithAuth<StatsResponse>('/stats');
}

// Timeline endpoints
export async function loadTimeline(): Promise<TimelineEvent[]> {
  const data = await fetchWithAuth<{ events: TimelineEvent[] }>('/timeline');
  return data.events;
}

// Chat endpoints
export async function sendChatMessage(message: string): Promise<string> {
  const data = await fetchWithAuth<{ response: string }>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message })
  });
  return data.response;
}

// Sources endpoints
export async function loadSources(): Promise<Source[]> {
  const data = await fetchWithAuth<{ sources: Source[] }>('/sources');
  return data.sources;
}
```

#### 1.4 Set Up Authentication Hook

```typescript
// src/hooks.server.ts
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Extract session token from cookie or header
  const sessionToken = event.cookies.get('sessionToken') ||
                       event.request.headers.get('Authorization')?.replace('Bearer ', '');

  if (sessionToken) {
    // Verify token with backend
    try {
      const response = await fetch('http://localhost:8000/api/verify-session', {
        headers: {
          'Authorization': `Bearer ${sessionToken}`
        }
      });

      if (response.ok) {
        event.locals.authenticated = true;
        event.locals.sessionToken = sessionToken;
      }
    } catch (error) {
      console.error('Auth verification failed:', error);
    }
  }

  // Public routes (no auth required)
  const publicRoutes = ['/login', '/static'];
  const isPublicRoute = publicRoutes.some(route => event.url.pathname.startsWith(route));

  if (!event.locals.authenticated && !isPublicRoute) {
    return new Response('Redirect', {
      status: 303,
      headers: {
        'Location': '/login'
      }
    });
  }

  return resolve(event);
};
```

#### 1.5 Create Login Page

```svelte
<!-- src/routes/login/+page.svelte -->
<script lang="ts">
  import { goto } from '$app/navigation';

  let username = $state('');
  let password = $state('');
  let rememberMe = $state(false);
  let error = $state<string | null>(null);
  let loading = $state(false);

  async function handleLogin() {
    error = null;
    loading = true;

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();

      // Store session token
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem('sessionToken', data.session_token);

      // Redirect to main app
      goto('/');
    } catch (e) {
      error = e instanceof Error ? e.message : 'Login failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="login-page">
  <div class="login-card">
    <h1>Epstein Archive</h1>
    <p class="subtitle">Secure Access Required</p>

    {#if error}
      <div class="error-message">{error}</div>
    {/if}

    <form on:submit|preventDefault={handleLogin}>
      <div class="form-group">
        <label for="username">Username</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          required
          disabled={loading}
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          required
          disabled={loading}
        />
      </div>

      <label class="checkbox-label">
        <input type="checkbox" bind:checked={rememberMe} disabled={loading} />
        <span>Remember me</span>
      </label>

      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  </div>
</div>

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .login-card {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    width: 400px;
    max-width: 90%;
  }

  h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
    color: #1f2937;
  }

  .subtitle {
    margin: 0 0 24px 0;
    color: #6b7280;
    font-size: 14px;
  }

  .error-message {
    background: #fee2e2;
    border: 1px solid #ef4444;
    color: #dc2626;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
  }

  .form-group {
    margin-bottom: 16px;
  }

  label {
    display: block;
    margin-bottom: 6px;
    color: #374151;
    font-size: 14px;
    font-weight: 500;
  }

  input[type="text"],
  input[type="password"] {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.2s;
  }

  input[type="text"]:focus,
  input[type="password"]:focus {
    outline: none;
    border-color: #667eea;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    cursor: pointer;
  }

  button {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  button:hover:not(:disabled) {
    opacity: 0.9;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
```

### Deliverables
- ✅ SvelteKit app running on localhost:5173
- ✅ TypeScript types for all API responses
- ✅ API client with authentication
- ✅ Login page functional
- ✅ Auth redirect working

### Testing Checklist
- [ ] SvelteKit dev server starts without errors
- [ ] Login page loads at `/login`
- [ ] Successful login redirects to `/`
- [ ] Invalid credentials show error
- [ ] Session token stored correctly
- [ ] API calls include auth headers

---

## Phase 2: High-Value Components (Week 2)

### Goals
- ✅ Migrate 4 most impactful components
- ✅ 70% code reduction in these areas
- ✅ Performance benchmarks show improvement

### Priority Components

**Selection Criteria**:
1. **High repetition**: Used many times (max ROI)
2. **Complex logic**: Manual DOM updates (most benefit from reactivity)
3. **User-facing**: Performance improvements visible

#### 2.1 EntityCard Component (Day 1)

**Current**: 60 lines string concatenation
**Target**: 40 lines Svelte component

See `COMPONENT_MOCKUPS.md` for full implementation.

**Testing**:
```typescript
// EntityCard.test.ts
import { render } from '@testing-library/svelte';
import EntityCard from './EntityCard.svelte';

test('renders entity name', () => {
  const { getByText } = render(EntityCard, {
    entity: {
      name: 'Test Entity',
      connection_count: 5,
      total_documents: 10,
      is_billionaire: false,
      entity_type: 'person'
    },
    onSelect: () => {}
  });

  expect(getByText('Test Entity')).toBeInTheDocument();
});

test('shows billionaire badge when is_billionaire true', () => {
  const { getByText } = render(EntityCard, {
    entity: {
      name: 'Rich Person',
      is_billionaire: true,
      // ... other props
    },
    onSelect: () => {}
  });

  expect(getByText('BILLIONAIRE')).toBeInTheDocument();
});
```

#### 2.2 EntityList Component (Day 2)

**Current**: 150 lines with manual filtering
**Target**: 90 lines with reactive filtering

**Integration**:
```svelte
<!-- src/routes/entities/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import EntityList from '$components/EntityList.svelte';
  import { loadEntities } from '$lib/api/client';
  import type { Entity } from '$lib/types';

  let entities = $state<Entity[]>([]);
  let loading = $state(true);

  onMount(async () => {
    entities = await loadEntities();
    loading = false;
  });

  function handleSelectEntity(entityName: string) {
    // Navigate to network view with entity selected
    window.location.href = `/?tab=network&selected=${encodeURIComponent(entityName)}`;
  }
</script>

{#if loading}
  <div class="loading">Loading entities...</div>
{:else}
  <EntityList {entities} onSelectEntity={handleSelectEntity} />
{/if}
```

#### 2.3 TimelineEvent Component (Day 3)

**Current**: 80 lines string template
**Target**: 50 lines Svelte component

See `COMPONENT_MOCKUPS.md` for implementation.

#### 2.4 ChatSidebar Component (Day 4-5)

**Current**: 200 lines with manual message rendering
**Target**: 120 lines with reactive messages

**State Management**:
```typescript
// src/lib/stores/chat.svelte.ts
import type { ChatMessage } from '$lib/types';
import { sendChatMessage } from '$lib/api/client';

function createChatStore() {
  let messages = $state<ChatMessage[]>([]);
  let loading = $state(false);

  async function send(text: string) {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      type: 'user',
      content: text,
      timestamp: new Date()
    };

    messages = [...messages, userMessage];
    loading = true;

    try {
      const response = await sendChatMessage(text);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        type: 'assistant',
        content: response,
        timestamp: new Date()
      };

      messages = [...messages, assistantMessage];
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        type: 'system',
        content: 'Error: Could not get response. Please try again.',
        timestamp: new Date()
      };

      messages = [...messages, errorMessage];
    } finally {
      loading = false;
    }
  }

  return {
    get messages() { return messages; },
    get loading() { return loading; },
    send
  };
}

export const chatStore = createChatStore();
```

### Deliverables
- ✅ 4 components migrated to Svelte
- ✅ Unit tests for each component
- ✅ Performance benchmarks documented

### Performance Benchmarks

**Metrics to Track**:
- Entity list render time (1,773 items)
- Filter update latency
- Memory usage
- Bundle size impact

**Benchmark Script**:
```typescript
// benchmark.ts
import { performance } from 'perf_hooks';

async function benchmarkEntityList() {
  const entities = await loadEntities(); // 1,773 entities

  // Measure vanilla JS render
  const vanillaStart = performance.now();
  renderEntitiesList(entities); // Current implementation
  const vanillaTime = performance.now() - vanillaStart;

  // Measure Svelte render
  const svelteStart = performance.now();
  // Render Svelte component
  const svelteTime = performance.now() - svelteStart;

  console.log(`Vanilla JS: ${vanillaTime.toFixed(2)}ms`);
  console.log(`Svelte: ${svelteTime.toFixed(2)}ms`);
  console.log(`Improvement: ${((1 - svelteTime / vanillaTime) * 100).toFixed(1)}%`);
}
```

**Expected Results**:
- Entity list render: 850ms → 180ms (79% faster)
- Filter update: 45ms → 8ms (82% faster)
- Memory usage: 38 MB → 22 MB (42% reduction)

---

## Phase 3: State Management (Week 3)

### Goals
- ✅ Replace 20+ globals with 4 stores
- ✅ Centralized state management
- ✅ Automatic reactivity across components

### Stores to Create

#### 3.1 Network Store

```typescript
// src/lib/stores/network.svelte.ts
import type { NetworkData, NetworkNode } from '$lib/types';
import { loadNetworkData } from '$lib/api/client';

function createNetworkStore() {
  let data = $state<NetworkData | null>(null);
  let selectedNode = $state<string | null>(null);
  let searchQuery = $state('');
  let filters = $state({
    billionaires: false,
    connectionThreshold: 0
  });

  // Derived: visible nodes based on filters
  let visibleNodes = $derived(
    data?.nodes.filter(node => {
      if (filters.billionaires && !node.is_billionaire) return false;
      if (node.connection_count < filters.connectionThreshold) return false;
      return true;
    }) ?? []
  );

  // Derived: search results
  let searchResults = $derived(
    searchQuery
      ? data?.nodes.filter(n =>
          n.id.toLowerCase().includes(searchQuery.toLowerCase())
        ) ?? []
      : []
  );

  async function load() {
    data = await loadNetworkData();
  }

  function selectNode(nodeId: string | null) {
    selectedNode = nodeId;
  }

  function updateFilters(newFilters: Partial<typeof filters>) {
    filters = { ...filters, ...newFilters };
  }

  return {
    // Getters
    get data() { return data; },
    get selectedNode() { return selectedNode; },
    get searchQuery() { return searchQuery; },
    get filters() { return filters; },
    get visibleNodes() { return visibleNodes; },
    get searchResults() { return searchResults; },

    // Actions
    load,
    selectNode,
    updateFilters,
    setSearchQuery: (query: string) => searchQuery = query
  };
}

export const networkStore = createNetworkStore();
```

#### 3.2 Entities Store

```typescript
// src/lib/stores/entities.svelte.ts
import type { Entity } from '$lib/types';
import { loadEntities, searchEntities } from '$lib/api/client';

function createEntitiesStore() {
  let entities = $state<Entity[]>([]);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function load() {
    loading = true;
    error = null;
    try {
      entities = await loadEntities();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load entities';
    } finally {
      loading = false;
    }
  }

  async function search(query: string) {
    loading = true;
    error = null;
    try {
      entities = await searchEntities(query);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Search failed';
    } finally {
      loading = false;
    }
  }

  return {
    get entities() { return entities; },
    get loading() { return loading; },
    get error() { return error; },
    load,
    search
  };
}

export const entitiesStore = createEntitiesStore();
```

#### 3.3 Timeline Store

```typescript
// src/lib/stores/timeline.svelte.ts
import type { TimelineEvent } from '$lib/types';
import { loadTimeline } from '$lib/api/client';

function createTimelineStore() {
  let events = $state<TimelineEvent[]>([]);
  let filters = $state({
    type: 'all' as 'all' | 'legal' | 'travel' | 'financial' | 'personal',
    startDate: null as string | null,
    endDate: null as string | null,
    search: ''
  });

  let filteredEvents = $derived(
    events.filter(event => {
      if (filters.type !== 'all' && event.type !== filters.type) return false;
      if (filters.startDate && event.date < filters.startDate) return false;
      if (filters.endDate && event.date > filters.endDate) return false;
      if (filters.search && !event.title.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      return true;
    })
  );

  async function load() {
    events = await loadTimeline();
  }

  return {
    get events() { return events; },
    get filters() { return filters; },
    get filteredEvents() { return filteredEvents; },
    load,
    updateFilters: (newFilters: Partial<typeof filters>) => {
      filters = { ...filters, ...newFilters };
    }
  };
}

export const timelineStore = createTimelineStore();
```

### Deliverables
- ✅ 4 stores implemented
- ✅ All components using stores instead of globals
- ✅ No global variables remaining

---

## Phase 4: D3 Integration (Week 4)

### Goals
- ✅ D3 network graph wrapped in Svelte
- ✅ Reactive updates on filter changes
- ✅ No memory leaks

### Implementation

See `COMPONENT_MOCKUPS.md` NetworkGraph.svelte for full code.

**Key Challenges**:

1. **D3 vs Svelte Reactivity**: D3 mutates DOM directly, Svelte expects control.
   - **Solution**: Use `$effect()` to re-run D3 setup when data changes
   - Store D3 objects (simulation, svg) in non-reactive variables

2. **Cleanup**: D3 simulations run indefinitely
   - **Solution**: Stop simulation in $effect cleanup function

3. **Performance**: Full re-render on every update is slow
   - **Solution**: Use $effect to update only changed attributes

**Testing**:
```typescript
// NetworkGraph.test.ts
import { render } from '@testing-library/svelte';
import NetworkGraph from './NetworkGraph.svelte';

test('renders network with correct number of nodes', () => {
  const networkData = {
    nodes: [
      { id: 'A', connection_count: 5, is_billionaire: false },
      { id: 'B', connection_count: 3, is_billionaire: true }
    ],
    edges: [
      { source: 'A', target: 'B', weight: 10 }
    ]
  };

  const { container } = render(NetworkGraph, {
    networkData,
    filters: { billionaires: false, connectionThreshold: 0 }
  });

  const nodes = container.querySelectorAll('circle');
  expect(nodes.length).toBe(2);
});
```

### Deliverables
- ✅ NetworkGraph.svelte component
- ✅ Reactive filtering working
- ✅ Memory leak tests passing

---

## Phase 5: Full Migration (Week 5)

### Goals
- ✅ All tabs migrated
- ✅ app.js deleted (2,700 lines → 0)
- ✅ Production deployment

### Remaining Work

#### 5.1 Overview Tab

```svelte
<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { loadStats } from '$lib/api/client';
  import type { StatsResponse } from '$lib/types';

  let stats = $state<StatsResponse | null>(null);
  let loading = $state(true);

  onMount(async () => {
    stats = await loadStats();
    loading = false;
  });
</script>

{#if loading}
  <p>Loading...</p>
{:else if stats}
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Entities</div>
      <div class="stat-value">{stats.total_entities.toLocaleString()}</div>
    </div>
    <!-- More stats... -->
  </div>
{/if}
```

#### 5.2 Sources Tab

Similar pattern to entities tab.

#### 5.3 Ingestion Tab

Status polling with reactive updates.

### Final Cleanup

**Delete Files**:
- ❌ `app.js` (2,700 lines)
- ❌ Inline `<style>` from index.html

**Update**:
- ✅ `package.json` (remove unused dependencies)
- ✅ `README.md` (update setup instructions)

### Production Checklist

- [ ] All features working
- [ ] Unit tests passing (90%+ coverage)
- [ ] E2E tests passing (Playwright)
- [ ] Performance benchmarks documented
- [ ] Lighthouse score 95+
- [ ] No console errors
- [ ] Authentication working
- [ ] All API endpoints tested

---

## Rollback Plan

**If migration fails**, each phase can be rolled back independently:

### Phase 1 Rollback
- Keep vanilla JS, delete SvelteKit project
- No user impact (SvelteKit not deployed)

### Phase 2-4 Rollback
- Deploy vanilla JS version
- Components can run side-by-side
- Feature flags to toggle Svelte components

### Phase 5 Rollback
- Git revert to pre-migration commit
- Vanilla JS fully functional as backup

---

## Success Metrics

### Code Quality
- ✅ **5,800 lines → 1,200 lines** (79% reduction)
- ✅ **100% type coverage** (TypeScript strict mode)
- ✅ **90%+ test coverage** (unit + E2E)
- ✅ **Zero ESLint errors**

### Performance
- ✅ **Initial load: 2.1s → 0.8s** (62% faster)
- ✅ **Entity list render: 850ms → 180ms** (79% faster)
- ✅ **Filter update: 45ms → 8ms** (82% faster)
- ✅ **Bundle size: 120 KB → 45 KB** (62% smaller)
- ✅ **Lighthouse score: 78 → 95+**

### Developer Experience
- ✅ **Hot module reload** (instant feedback)
- ✅ **TypeScript autocomplete** (better IDE support)
- ✅ **Component isolation** (easier testing)
- ✅ **Declarative UI** (easier to reason about)

---

## Timeline Summary

| Week | Phase | Deliverables | Risk |
|------|-------|--------------|------|
| 1 | Foundation | SvelteKit + TypeScript + Auth | Low |
| 2 | Components | 4 high-value components | Low |
| 3 | State | 4 Runes stores | Medium |
| 4 | D3 | Network graph | Medium |
| 5 | Complete | All tabs + deployment | Low |

**Total Time**: 5 weeks (1 developer)

**Parallel Work Opportunities**:
- Weeks 2-3: Multiple developers can work on different components
- Week 4-5: Backend team can optimize APIs based on new usage patterns

---

## Post-Migration

### Maintenance Benefits
- **2-3x faster** feature development
- **70% fewer bugs** (type safety + reactivity)
- **Easier onboarding** (component-based architecture)

### Future Enhancements
- Server-side rendering (SEO)
- Progressive web app (offline support)
- Advanced visualizations (3D network graph)
- Real-time updates (WebSocket integration)

---

**Next Steps**: Begin Phase 1 implementation. Review with team for approval.
