# AI Assistant Conversation Flow Diagram

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- How the Enhanced Chatbot Works

---

## How the Enhanced Chatbot Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ASKS A QUESTION                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 1: DETECT INTENT & ENTITIES                    │
│                                                                  │
│  Query: "Tell me about Ghislaine Maxwell"                       │
│                                                                  │
│  Intent Detection:                                               │
│  ✓ Check for capability words → NO                              │
│  ✓ Check for entity words ("tell me about") → YES               │
│  → Intent = "entity_info"                                        │
│                                                                  │
│  Entity Detection:                                               │
│  ✓ Scan all 1,637 entities                                      │
│  ✓ Match "Ghislaine Maxwell" → FOUND                            │
│  → Entity: {name, docs: 245, connections: 67, flights: 42}      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 2: BUILD SITE CONTEXT & CAPABILITIES             │
│                                                                  │
│  Site Stats:                                                     │
│  - Total Entities: 1,637                                         │
│  - Total Flights: 1,167                                          │
│  - Total Documents: 305                                          │
│  - Network Connections: 2,221                                    │
│                                                                  │
│  Features Available:                                             │
│  - Search entities by name                                       │
│  - Filter flight logs                                            │
│  - Browse documents                                              │
│  - Explore network                                               │
│  - View timeline                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            STEP 3: GENERATE NAVIGATION & SUGGESTIONS            │
│                                                                  │
│  Navigation Quick Actions:                                       │
│  1. [View Ghislaine Maxwell's profile] → /entities/...          │
│  2. [See flight records (42 flights)] → /flights?passenger=...  │
│                                                                  │
│  Follow-up Suggestions:                                          │
│  1. "Who is connected to Ghislaine Maxwell?"                    │
│  2. "Show me documents about Ghislaine Maxwell"                 │
│  3. "When did Ghislaine Maxwell travel?"                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 4: BUILD SYSTEM PROMPT                       │
│                                                                  │
│  System Prompt:                                                  │
│  "You are the Epstein Archive AI Assistant.                     │
│                                                                  │
│   SITE CAPABILITIES:                                             │
│   - 1,637 entities (12 billionaires, 743 in black book)         │
│   - 1,167 flight records                                         │
│   - 305 documents                                                │
│   - 2,221 connections                                            │
│                                                                  │
│   DETECTED QUERY INTENT: entity_info                             │
│   ENTITIES MENTIONED: Ghislaine Maxwell                          │
│                                                                  │
│   GUIDELINES:                                                    │
│   - Provide actionable responses                                │
│   - Use actual statistics                                        │
│   - Suggest navigation steps"                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 5: CALL LLM API                          │
│                                                                  │
│  Messages:                                                       │
│  1. System: [Enhanced prompt with site context]                 │
│  2. User: "Tell me about Ghislaine Maxwell"                     │
│  3. [Conversation history if provided]                           │
│                                                                  │
│  OpenRouter API → GPT-4o                                         │
│  Timeout: 30 seconds                                             │
│  Temperature: 0.7                                                │
│  Max Tokens: 800                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  API Success?     │
                    └─────────┬─────────┘
                     YES ▼    │ NO ▼
              ┌──────────┐   ┌──────────┐
              │ LLM Mode │   │ Fallback │
              └──────────┘   └──────────┘
                     │              │
                     ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 6: BUILD RESPONSE                        │
│                                                                  │
│  LLM Mode (1-3 seconds):                                         │
│  Response: "Ghislaine Maxwell is a central figure in the        │
│  archive with extensive documentation. She appears in 245       │
│  documents, has 67 network connections, and was a passenger     │
│  on 42 documented flights. [AI-generated insights...]"          │
│  Model: "openai/gpt-4o"                                          │
│                                                                  │
│  Fallback Mode (<50ms):                                          │
│  Response: "I found information about Ghislaine Maxwell.        │
│  They appear in 245 documents with 67 connections. Use the      │
│  navigation suggestions below to explore further."              │
│  Model: "fallback"                                               │
│  Context.error: "AI service temporarily unavailable"            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE STRUCTURE                      │
│                                                                  │
│  {                                                               │
│    "response": "Ghislaine Maxwell is a central figure...",      │
│    "suggestions": [                                              │
│      "Who is connected to Ghislaine Maxwell?",                  │
│      "Show me documents about Ghislaine Maxwell",               │
│      "When did Ghislaine Maxwell travel?"                       │
│    ],                                                            │
│    "navigation": {                                               │
│      "quick_actions": [                                          │
│        {                                                         │
│          "text": "View Ghislaine Maxwell's full profile",       │
│          "action": "navigate",                                   │
│          "target": "/entities/Ghislaine Maxwell"                │
│        },                                                        │
│        {                                                         │
│          "text": "See flight records (42 flights)",             │
│          "action": "filter",                                     │
│          "target": "/flights",                                   │
│          "params": {"passenger": "Ghislaine Maxwell"}           │
│        }                                                         │
│      ]                                                           │
│    },                                                            │
│    "context": {                                                  │
│      "detected_entities": [{...}],                              │
│      "intent": "entity_info",                                    │
│      "site_stats": {...}                                         │
│    },                                                            │
│    "model": "openai/gpt-4o"                                      │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER SEES:                               │
│                                                                  │
│  💬 "Ghislaine Maxwell is a central figure in the archive..."  │
│                                                                  │
│  🔘 Quick Actions:                                               │
│  ┌─────────────────────────────────────────┐                   │
│  │ View Ghislaine Maxwell's full profile   │                   │
│  └─────────────────────────────────────────┘                   │
│  ┌─────────────────────────────────────────┐                   │
│  │ See flight records (42 flights)         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                  │
│  💡 You might also ask:                                          │
│  • Who is connected to Ghislaine Maxwell?                       │
│  • Show me documents about Ghislaine Maxwell                    │
│  • When did Ghislaine Maxwell travel?                           │
└─────────────────────────────────────────────────────────────────┘
```

## Intent Detection Decision Tree

```
USER QUERY
    │
    ├─ Contains "what can", "help", "features"?
    │   └─ YES → Intent: capabilities
    │        └─ Navigation: All 5 main pages
    │        └─ Suggestions: General feature demos
    │
    ├─ Contains "who is", "tell me about"?
    │   └─ YES → Intent: entity_info
    │        └─ Detect mentioned entities
    │        └─ Navigation: Entity profile + flights
    │        └─ Suggestions: Connections, documents, timeline
    │
    ├─ Contains "flight", "travel", "passenger"?
    │   └─ YES → Intent: flights
    │        └─ Navigation: Flights page
    │        └─ Suggestions: Passenger filters, date ranges
    │
    ├─ Contains "document", "file", "deposition"?
    │   └─ YES → Intent: documents
    │        └─ Navigation: Documents page
    │        └─ Suggestions: Type filters, entity search
    │
    ├─ Contains "connect", "network", "related"?
    │   └─ YES → Intent: connections
    │        └─ Navigation: Network page
    │        └─ Suggestions: Entity relationships
    │
    ├─ Contains "when", "date", "timeline"?
    │   └─ YES → Intent: timeline
    │        └─ Navigation: Timeline page
    │        └─ Suggestions: Event exploration
    │
    └─ NO MATCHES
        └─ Intent: general
             └─ Navigation: Contextual based on query
             └─ Suggestions: Common features
```

## Entity Detection Flow

```
QUERY: "How are Bill Clinton and Prince Andrew connected?"

STEP 1: Convert to lowercase
"how are bill clinton and prince andrew connected?"

STEP 2: Scan all 1,637 entities
┌─────────────────────────────┐
│ For each entity in archive: │
│                              │
│ "Jeffrey Epstein" → NO MATCH │
│ "Ghislaine Maxwell" → NO     │
│ "Bill Clinton" → MATCH! ✓    │
│ "William Clinton" → SKIP     │ (same person)
│ "Prince Andrew" → MATCH! ✓   │
│ ...                          │
└─────────────────────────────┘

STEP 3: Return detected entities
[
  {
    "name": "Bill Clinton",
    "documents": 134,
    "connections": 45,
    "flights": 26,
    "is_billionaire": false
  },
  {
    "name": "Prince Andrew",
    "documents": 89,
    "connections": 34,
    "flights": 17,
    "is_billionaire": false
  }
]

STEP 4: Generate suggestions
- "How are Bill Clinton and Prince Andrew connected?" (based on 2+ entities)
- "Tell me about Bill Clinton"
- "Tell me about Prince Andrew"
```

## Navigation Generation Logic

```
Based on Intent + Detected Entities

IF intent = "entity_info" AND entities detected:
    actions = [
        {
            text: "View {entity}'s full profile",
            action: "navigate",
            target: "/entities/{entity}"
        }
    ]

    IF entity.flights > 0:
        actions.append({
            text: "See {entity}'s flight records ({count} flights)",
            action: "filter",
            target: "/flights",
            params: {passenger: entity.name}
        })

IF intent = "capabilities":
    actions = [
        {text: "Explore Entities", action: "navigate", target: "/entities"},
        {text: "View Flight Logs", action: "navigate", target: "/flights"},
        {text: "Browse Documents", action: "navigate", target: "/documents"},
        {text: "Explore Network", action: "navigate", target: "/network"}
    ]

IF intent = "flights":
    actions = [
        {text: "Browse all flight records", action: "navigate", target: "/flights"}
    ]

    IF entities detected:
        actions.append({
            text: "Filter flights by {entity}",
            action: "filter",
            target: "/flights",
            params: {passenger: entity.name}
        })

... (similar logic for other intents)

LIMIT: Max 4 quick actions returned
```

## Performance Breakdown

```
REQUEST: "Tell me about Jeffrey Epstein"
    │
    ├─ Entity Detection ............... 8ms
    │   └─ Scan 1,637 entities in memory
    │
    ├─ Intent Detection ............... 3ms
    │   └─ Regex pattern matching
    │
    ├─ Navigation Generation .......... 4ms
    │   └─ Rule-based action builder
    │
    ├─ Site Stats Lookup .............. 2ms
    │   └─ Cached in memory
    │
    ├─ System Prompt Build ............ 1ms
    │   └─ String concatenation
    │
    └─ LLM API Call ................... 1,200ms
        └─ OpenRouter → GPT-4o (network + inference)

TOTAL: ~1,218ms (1.2 seconds)

FALLBACK MODE (if LLM fails):
    │
    ├─ Entity Detection ............... 8ms
    ├─ Intent Detection ............... 3ms
    ├─ Navigation Generation .......... 4ms
    ├─ Site Stats Lookup .............. 2ms
    └─ Fallback Response .............. 1ms

TOTAL: ~18ms (50ms worst case)
```

## Data Flow Summary

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│  Enhanced    │────▶│ OpenRouter│────▶│  User    │
│  Query   │     │  Chat API    │     │  GPT-4o   │     │ Response │
└──────────┘     └──────────────┘     └──────────┘     └──────────┘
                       │
                       ├─ Load: entity_stats (1,637 entities)
                       ├─ Load: network_data (387 nodes, 2,221 edges)
                       ├─ Load: classifications (305 documents)
                       ├─ Load: flight_data (1,167 flights)
                       │
                       ├─ Detect: Intent
                       ├─ Detect: Entities
                       ├─ Generate: Navigation
                       ├─ Generate: Suggestions
                       │
                       └─ Build: Enriched System Prompt
```

---

**This diagram shows the complete conversation flow from user question to enriched response with navigation and suggestions!**
