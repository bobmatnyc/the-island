# Hybrid Vector RAG + Knowledge Graph Architecture

**Quick Summary**: This architecture combines the strengths of both systems:...

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Vector RAG**: Semantic search over unstructured documents
- **Knowledge Graph**: Structured entity relationships and graph traversal
- "What documents mention flight logs?"
- "Find emails about financial transactions"
- "Search for documents from 2005"

---

## Overview

This architecture combines the strengths of both systems:
- **Vector RAG**: Semantic search over unstructured documents
- **Knowledge Graph**: Structured entity relationships and graph traversal

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Query                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │  Query Router   │ (Determines query type)
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │  Vector   │     │   Graph   │     │  Hybrid   │
    │    RAG    │     │  Traversal│     │  Search   │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │ ChromaDB  │     │  Neo4j    │     │   Both    │
    │ Vectors   │     │  Graph    │     │ Combined  │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Context Fusion │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Qwen LLM      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    Response     │
                    └─────────────────┘
```

## Component Breakdown

### 1. Query Router
Analyzes user query to determine optimal search strategy:

**Vector RAG queries**:
- "What documents mention flight logs?"
- "Find emails about financial transactions"
- "Search for documents from 2005"

**Graph queries**:
- "Who is connected to Ghislaine Maxwell?"
- "Show me the shortest path between X and Y"
- "Find all billionaires with >10 connections"

**Hybrid queries**:
- "What did Prince Andrew say in documents?" (Graph: find entity, Vector: search mentions)
- "Show connections mentioned in flight logs" (Vector: find logs, Graph: extract relationships)

### 2. Vector RAG (ChromaDB)

**Schema**:
```python
{
    "collection": "documents",
    "embeddings": nomic-embed-text,
    "metadata": {
        "document_id": str,
        "chunk_id": int,
        "source": str,
        "entity_mentions": [str],  # Links to KG
        "date": str,
        "document_type": str,
        "page_number": int
    }
}
```

**Entity embeddings**:
```python
{
    "collection": "entities",
    "embeddings": nomic-embed-text,
    "metadata": {
        "entity_id": str,
        "name": str,
        "aliases": [str],
        "category": str,  # person, organization, location
        "neo4j_node_id": str  # Links to KG
    }
}
```

### 3. Knowledge Graph (Neo4j or NetworkX)

**Schema**:
```cypher
// Nodes
(:Person {name, entity_id, is_billionaire, metadata})
(:Organization {name, entity_id, type})
(:Document {path, source, date, type})
(:Location {name, coordinates})

// Relationships
(:Person)-[:FLEW_WITH {flight_count, dates: []}]->(:Person)
(:Person)-[:MENTIONED_IN {context, page}]->(:Document)
(:Person)-[:ASSOCIATED_WITH]->(:Organization)
(:Person)-[:VISITED]->(:Location)
(:Document)-[:MENTIONS]->(:Person)
```

**Benefits**:
- Graph traversal queries (shortest path, centrality)
- Relationship-based filtering
- Multi-hop reasoning
- Temporal analysis

### 4. Hybrid Search Pipeline

```python
def hybrid_search(query: str, strategy: str = "auto"):
    # 1. Detect query intent
    intent = classify_query(query)
    
    # 2. Execute appropriate searches
    if intent == "semantic":
        vector_results = chromadb.similarity_search(query, k=10)
        return vector_results
    
    elif intent == "graph":
        graph_results = neo4j.cypher_query(query)
        return graph_results
    
    elif intent == "hybrid":
        # Execute both
        vector_results = chromadb.similarity_search(query, k=5)
        
        # Extract entities from vector results
        entities = extract_entities(vector_results)
        
        # Graph expansion
        graph_context = neo4j.expand_from_entities(entities, hops=2)
        
        # Combine contexts
        combined_context = merge_contexts(vector_results, graph_context)
        
        return combined_context
    
    # 3. Provide to LLM
    response = qwen_llm(query, context=combined_context)
    return response
```

## Use Cases

### Use Case 1: Entity-Centric Search
**Query**: "What do we know about Bill Clinton?"

**Execution**:
1. **Graph**: Find Bill Clinton node + 1-hop neighbors
2. **Vector**: Search all document chunks mentioning "Bill Clinton"
3. **Fusion**: Combine relationship graph with document excerpts
4. **LLM**: Synthesize comprehensive answer

### Use Case 2: Relationship Discovery
**Query**: "How are Trump and Epstein connected?"

**Execution**:
1. **Graph**: Find shortest path(s) between Trump and Epstein nodes
2. **Graph**: Identify intermediate entities and relationships
3. **Vector**: Retrieve documents mentioning both entities
4. **LLM**: Explain connections with supporting evidence

### Use Case 3: Temporal Analysis
**Query**: "What happened in 2005?"

**Execution**:
1. **Vector**: Search documents with date metadata = 2005
2. **Graph**: Filter nodes/edges by date property
3. **Fusion**: Timeline of events + entity interactions
4. **LLM**: Narrative summary

### Use Case 4: Network Analysis
**Query**: "Who are the most connected people?"

**Execution**:
1. **Graph**: Calculate degree centrality, betweenness centrality
2. **Graph**: Identify hub nodes
3. **Vector**: Retrieve documents for top-N central entities
4. **LLM**: Explain why these entities are central

## Implementation Stack

```yaml
Vector Store:
  - ChromaDB (local, embedded)
  - Embeddings: nomic-embed-text via Ollama
  - Collections: documents, entities

Knowledge Graph:
  Option A (Lightweight):
    - NetworkX (Python, in-memory)
    - Export/Import from JSON
    - Good for current 387 nodes
  
  Option B (Production):
    - Neo4j (graph database)
    - Cypher query language
    - Better for scale (67K+ documents)

LLM:
  - Qwen 2.5 Coder 7B (existing)
  - Context window: 32K tokens

Query Router:
  - Simple keyword detection initially
  - Upgrade to classifier later
```

## Advantages of Hybrid Approach

| Feature | Vector RAG | Knowledge Graph | Hybrid |
|---------|-----------|-----------------|---------|
| Semantic search | ✅ | ❌ | ✅ |
| Exact relationships | ❌ | ✅ | ✅ |
| Multi-hop reasoning | ❌ | ✅ | ✅ |
| Document context | ✅ | ❌ | ✅ |
| Graph traversal | ❌ | ✅ | ✅ |
| Temporal queries | ⚠️ | ✅ | ✅ |
| Unstructured text | ✅ | ❌ | ✅ |
| Structured relations | ❌ | ✅ | ✅ |

## Next Steps

1. **Phase 1**: Implement NetworkX-based KG from existing entity network
2. **Phase 2**: Set up ChromaDB and embed existing documents
3. **Phase 3**: Build query router and hybrid search
4. **Phase 4**: Integrate with chatbot
5. **Phase 5**: (Optional) Migrate to Neo4j if scale requires
