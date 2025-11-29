# Chat Enhancement Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Entity badge shows "Prince Andrew"
- Entity documents section appears
- Connections section shows related entities
- Smart suggestions appear

---

## For Developers

### New API Methods

```typescript
// Basic semantic search
const results = await api.ragSearch("query text", 10);

// Entity-specific documents
const entityDocs = await api.getEntityDocuments("Prince Andrew", 20);

// Knowledge graph connections
const connections = await api.getEntityConnections("Jeffrey Epstein", 10);

// Find similar documents
const similar = await api.getSimilarDocuments("doc_id_123", 5);

// Multi-entity search
const multiResults = await api.multiEntitySearch(["Clinton", "Epstein"], 10);

// Load knowledge index
const knowledge = await api.getChatbotKnowledge();
```

### Response Types

```typescript
// Search results with similarity scores
interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

// Entity documents
interface EntitySearchResponse {
  entity: string;
  documents: EntityDocumentResult[];
  total_documents: number;
  total_mentions: number;
}

// Knowledge graph connections
interface ConnectionsResponse {
  entity: string;
  connections: EntityConnection[];
  total_connections: number;
}
```

### Key Functions in ChatSidebar

```typescript
// Detect entities in user query
const entities = detectEntities(query);  // Returns: string[]

// Generate smart suggestions
const suggestions = generateSuggestions(entities, connections);

// Handle entity search
await handleSearch(e);  // Detects entities, fetches all data in parallel

// Click handlers
handleEntityClick(entityName);    // Auto-fills input
handleSuggestionClick(suggestion); // Auto-fills input
handleFindSimilar(docId);         // Fetches similar docs
```

### Component Usage

```tsx
import { ChatSidebar } from '@/components/chat/ChatSidebar';

// In your layout/page
<ChatSidebar />

// Floating button appears in bottom-right
// Click to open full sidebar
// Features: history panel, entity detection, knowledge graph
```

---

## For Testing

### Manual Test Scenarios

**Test Entity Detection:**
```
Input: "Prince Andrew"
Expected:
  - Entity badge shows "Prince Andrew"
  - Entity documents section appears
  - Connections section shows related entities
  - Smart suggestions appear
```

**Test General Search:**
```
Input: "flight logs"
Expected:
  - Semantic search results
  - Similarity scores (color-coded)
  - Document excerpts
  - Entity mentions as badges
```

**Test Find Similar:**
```
1. Run any search
2. Click "Find Similar Documents" on a result
Expected:
  - New message with similar docs
  - Similarity percentages shown
  - Source doc ID referenced
```

**Test Knowledge Graph:**
```
Input: "Jeffrey Epstein"
Expected:
  - Connections card appears
  - Shows top connections (e.g., Maxwell, Clinton)
  - Shows relationship weights (e.g., "23 flights")
  - Connections are clickable
```

### Test Queries

**Entity Queries:**
- "Ghislaine Maxwell"
- "Prince Andrew connections"
- "Tell me about Bill Clinton"

**Semantic Queries:**
- "private island travel"
- "victims testimonies"
- "financial transactions"

**Multi-Entity:**
- "Clinton and Epstein"
- "Maxwell and Prince Andrew"

---

## For Users

### How to Use

**Start a Query:**
1. Click floating chat button (bottom-right)
2. Type your question naturally
3. Press Enter or click Send

**Explore Entities:**
- Click any entity badge to search for that person
- View connections in the Knowledge Graph card
- Click connections to explore relationships

**Follow Suggestions:**
- After each answer, see "You might also ask"
- Click suggestion to auto-fill input
- Edit if needed, then send

**Find Similar Content:**
- Click "Find Similar Documents" on any result
- Discover related information automatically
- Great for research and exploration

**Manage Sessions:**
- Click history icon (top-left) to see past chats
- Click a session to reload it
- Click trash icon to delete
- Click "+" to start new chat

### Example Interactions

**Question:** "Tell me about Prince Andrew"

**Response Shows:**
- 📄 Document count (156 documents, 342 mentions)
- 🔗 Connections (Epstein, Maxwell, Giuffre)
- 🔍 Search results (89 relevant documents)
- ✨ Suggestions (related queries)

**You Can:**
- Click "Jeffrey Epstein" badge → searches Epstein
- Click "Find Similar" → finds related documents
- Click suggestion → asks follow-up question
- Explore connections → discover relationships

---

## API Endpoints

### Vector Search
```
GET /api/rag/search?query={text}&limit={n}&entity_filter={name}
```

### Entity Documents
```
GET /api/rag/entity/{entity_name}?limit={n}
```

### Similar Documents
```
GET /api/rag/similar/{doc_id}?limit={n}
```

### Knowledge Graph
```
GET /api/rag/connections/{entity_name}?limit={n}
```

### Multi-Entity
```
GET /api/rag/multi-entity?entities={name1,name2}&limit={n}
```

### Knowledge Index
```
GET /api/chatbot/knowledge
```

---

## Troubleshooting

### Chat Not Loading
- Check backend is running: `http://localhost:8000/health`
- Check browser console for errors
- Verify knowledge index exists: `/data/metadata/chatbot_knowledge_index.json`

### Entity Detection Not Working
- Knowledge index must load successfully
- Check console for "Failed to load knowledge index"
- Verify `/api/chatbot/knowledge` endpoint works

### Search Returns No Results
- Check vector store is initialized
- Verify ChromaDB collection exists
- Check backend logs for errors

### Connections Not Showing
- Entity must exist in knowledge graph
- Check entity name spelling (case-sensitive)
- Verify `/api/rag/connections/{name}` returns data

---

## Performance Tips

**For Developers:**
- Knowledge index cached on mount (one-time load)
- Entity detection is in-memory (fast)
- Use Promise.all for parallel API calls
- Limit result counts (default: 10)

**For Users:**
- Specific entity queries are faster
- Use suggestions for optimized queries
- Session history loads from localStorage (instant)

---

## Feature Highlights

✨ **Smart Entity Detection**
- Automatic entity recognition in queries
- Multi-entity support
- Case-insensitive matching

🔗 **Knowledge Graph Integration**
- Shows entity connections from flight logs
- Relationship weights and types
- Interactive exploration

🎯 **Semantic Search**
- Vector embeddings for relevance
- Similarity scores (color-coded)
- Sub-100ms response times

💡 **Smart Suggestions**
- Context-aware follow-up questions
- Based on entities and connections
- Enables exploratory discovery

📊 **Rich Results**
- Document excerpts
- Entity mentions
- Source metadata
- Find similar documents

💾 **Session Management**
- Auto-save conversations
- History panel
- Resume past chats
- Up to 50 saved sessions

---

**Quick Start:**
1. Click chat button (bottom-right)
2. Ask a question (try: "Prince Andrew")
3. Explore entities and connections
4. Click suggestions to learn more

**Need Help?**
See full documentation in `CHAT_ENHANCEMENT_COMPLETE.md`
