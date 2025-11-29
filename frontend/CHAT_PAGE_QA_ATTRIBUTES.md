# Chat Page - Semantic HTML & QA Test Attributes

## Overview
The Chat/Search page has been enhanced with semantic HTML elements and comprehensive test attributes for improved accessibility and automated testing.

## Semantic HTML Elements

### Document Structure
- `<header>` - Page header with title and description
- `<section>` - Messages container with ARIA label
- `<article>` - Individual message bubbles
- `<time>` - Message timestamps with ISO datetime attributes
- `<dl>`, `<dt>`, `<dd>` - Document metadata in description lists
- `<form role="search">` - Search form with appropriate role

### Accessibility Features
- `aria-label` - Labels for screen readers on sections and inputs
- `aria-describedby` - Description for search input
- `aria-live="polite"` - Live region for loading indicator
- `aria-hidden` - Decorative icons hidden from screen readers
- `role="status"` - Loading indicator status
- `role="list"` and `role="listitem"` - Entity badges as semantic lists
- `sr-only` class - Screen reader only text for button labels

## Test Attributes (data-testid)

### Page Structure
| Element | data-testid | Description |
|---------|-------------|-------------|
| Main container | `chat-page` | Root page container |
| Header | `chat-header` | Page header section |
| Title | `page-title` | "Document Search" heading |
| Subtitle | `page-subtitle` | RAG description |
| Messages container | `messages-container` | Scrollable messages area |

### Empty State
| Element | data-testid | Description |
|---------|-------------|-------------|
| Empty state | `empty-state` | Initial state before any searches |
| Search icon | `empty-state-icon` | Magnifying glass icon |
| Title | `empty-state-title` | "Start a Search" heading |
| Description | `empty-state-description` | Explanation text |
| Example queries | `example-queries` | Container for examples |
| Query 1 | `example-query-1` | "Ghislaine Maxwell's activities" |
| Query 2 | `example-query-2` | "Prince Andrew connections" |
| Query 3 | `example-query-3` | "Flight logs to islands" |

### Messages
| Element | data-testid | Description |
|---------|-------------|-------------|
| Messages list | `messages-list` | Container for all messages |
| User message | `message-user` | User's query message |
| Assistant message | `message-assistant` | System response message |
| Message bubble | `message-bubble` | Individual message container |
| Message content | `message-content` | Text content of message |
| Timestamp | `message-timestamp` | Time the message was sent |

### Search Results
| Element | data-testid | Additional Attributes | Description |
|---------|-------------|---------------------|-------------|
| Results container | `search-results` | - | Container for all result cards |
| Result card | `search-result-card` | `data-result-index`, `data-doc-id` | Individual document result |
| Similarity score | `similarity-score` | `data-similarity` | Match percentage badge |
| Document ID | `doc-id` | - | Document identifier |
| Filename | `doc-filename` | - | Document filename |
| Text excerpt | `text-excerpt` | - | Document text snippet |
| Metadata | `metadata` | - | Document metadata container |
| Source | `doc-source` | - | Document source |
| Date | `doc-date` | - | Extraction date |
| File size | `doc-size` | - | File size in KB |
| Entity mentions | `entity-mentions` | - | Container for entity badges |
| Entity badge | `entity-badge` | `data-entity` | Individual entity name |

### Form Elements
| Element | data-testid | Description |
|---------|-------------|-------------|
| Search form | `search-form` | Main search form |
| Search input | `search-input` | Text input field |
| Submit button | `search-submit` | Search submit button |
| Loading indicator | `loading-indicator` | Searching status |

### Message Data Attributes
| Attribute | Usage | Example |
|-----------|-------|---------|
| `data-message-id` | Unique message identifier | `"1731972345678"` |
| `data-result-index` | Result position (0-based) | `"0"`, `"1"`, `"2"` |
| `data-doc-id` | Document identifier | `"DOJ-OGR-00002076"` |
| `data-similarity` | Similarity score (0-1) | `"0.371"` |
| `data-entity` | Entity name | `"Maxwell, Ghislaine"` |
| `datetime` | ISO timestamp | `"2025-11-19T18:09:00.000Z"` |

## Playwright Selectors Guide

### Common Selectors
```javascript
// Page elements
await page.getByTestId('chat-page')
await page.getByTestId('page-title')
await page.getByRole('search')

// Search interaction
await page.getByTestId('search-input').fill('Ghislaine Maxwell')
await page.getByTestId('search-submit').click()

// Wait for results
await page.getByTestId('search-results').waitFor()
await page.getByTestId('loading-indicator').waitFor({ state: 'hidden' })

// Check result cards
const cards = await page.getByTestId('search-result-card').all()
const firstCard = cards[0]
await firstCard.getByTestId('similarity-score').textContent()
await firstCard.getByTestId('doc-filename').textContent()

// Entity badges
const entities = await page.getByTestId('entity-badge').all()
const entityNames = await Promise.all(
  entities.map(e => e.getAttribute('data-entity'))
)

// Messages
const userMessages = await page.getByTestId('message-user').all()
const assistantMessages = await page.getByTestId('message-assistant').all()
```

### Advanced Selectors with Data Attributes
```javascript
// Find specific document by ID
await page.locator('[data-doc-id="DOJ-OGR-00002076"]')

// Find high similarity results (>0.7)
const highScores = await page.locator('[data-similarity]').evaluateAll(
  elements => elements.filter(el => parseFloat(el.dataset.similarity) > 0.7)
)

// Find specific entity
await page.locator('[data-entity="Maxwell, Ghislaine"]')

// Find specific message
await page.locator('[data-message-id="1731972345678"]')
```

## Accessibility Testing

### ARIA Landmarks
- `role="search"` - Search form
- `role="status"` - Loading indicator
- `role="list"` - Entity badges
- `aria-label` - Descriptive labels for regions
- `aria-live="polite"` - Live updates

### Screen Reader Testing
```javascript
// Check ARIA labels
await page.getByRole('search', { name: 'Document search' })
await page.getByRole('textbox', { name: 'Search query' })
await page.getByRole('button', { name: 'Submit search' })
await page.getByRole('status') // Loading indicator

// Check semantic structure
await page.locator('header').getByRole('heading', { level: 1 })
await page.locator('section[aria-label="Search results and conversation"]')
await page.locator('article') // Message bubbles
await page.locator('time[datetime]') // Timestamps
```

## CSS Classes for Styling

### State Classes
- Empty state: Combined with `data-testid="empty-state"`
- Loading: Combined with `data-testid="loading-indicator"` + `role="status"`
- Has results: Presence of `data-testid="search-results"`

### Color-Coded Similarity
Similarity badges use these Tailwind classes based on score:
- **≥70%**: `bg-green-100 text-green-800 border-green-300`
- **≥50%**: `bg-yellow-100 text-yellow-800 border-yellow-300`
- **<50%**: `bg-blue-100 text-blue-800 border-blue-300`

## Testing Examples

### Basic Flow Test
```javascript
test('Search and display results', async ({ page }) => {
  // Navigate
  await page.goto('http://localhost:5173/chat')
  await expect(page.getByTestId('chat-page')).toBeVisible()

  // Check empty state
  await expect(page.getByTestId('empty-state')).toBeVisible()

  // Perform search
  await page.getByTestId('search-input').fill('Ghislaine Maxwell')
  await page.getByTestId('search-submit').click()

  // Wait for loading
  await expect(page.getByTestId('loading-indicator')).toBeVisible()

  // Check results
  await expect(page.getByTestId('search-results')).toBeVisible()
  await expect(page.getByTestId('search-result-card').first()).toBeVisible()

  // Verify result content
  const firstCard = page.getByTestId('search-result-card').first()
  await expect(firstCard.getByTestId('similarity-score')).toBeVisible()
  await expect(firstCard.getByTestId('doc-filename')).toBeVisible()
  await expect(firstCard.getByTestId('text-excerpt')).toBeVisible()
  await expect(firstCard.getByTestId('entity-badge').first()).toBeVisible()
})
```

### Accessibility Test
```javascript
test('Accessibility compliance', async ({ page }) => {
  await page.goto('http://localhost:5173/chat')

  // Check semantic HTML
  await expect(page.locator('header')).toBeVisible()
  await expect(page.locator('main section')).toHaveAttribute('aria-label')

  // Check form accessibility
  const searchForm = page.getByRole('search')
  await expect(searchForm).toBeVisible()
  await expect(searchForm.getByRole('textbox')).toHaveAttribute('aria-label')

  // Check ARIA attributes
  await page.getByTestId('search-input').fill('test')
  await page.getByTestId('search-submit').click()
  await expect(page.getByRole('status')).toBeVisible() // Loading indicator
})
```

## Benefits

1. **Improved Testability**
   - Easy element selection with unique test IDs
   - Stable selectors that won't break with CSS changes
   - Data attributes for programmatic filtering

2. **Better Accessibility**
   - Semantic HTML for screen readers
   - ARIA labels and roles
   - Proper document structure

3. **Maintainability**
   - Clear element purpose from test IDs
   - Consistent naming convention
   - Easy to locate elements in code

4. **Debugging**
   - Data attributes provide context in browser devtools
   - Easy to inspect message/result metadata
   - Clear visual hierarchy

## Standards Compliance

- **WCAG 2.1 Level AA**: Semantic HTML, ARIA labels, screen reader support
- **HTML5**: Proper use of semantic elements
- **React Testing Library**: Best practices for test attributes
- **Playwright**: Recommended selector patterns
