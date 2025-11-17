# Chatbot Knowledge Index

## Overview

The chatbot knowledge index (`chatbot_knowledge_index.json`) is a comprehensive JSON file that provides the chatbot with quick access to all project information without needing to read multiple files.

## Purpose

**Enable chatbot to answer questions about:**
- Project files and scripts
- Data statistics (entities, documents, network)
- Ongoing work (downloads, classifications, processing)
- Source files and locations
- Email counts and participants
- Entity network statistics

## Structure

```json
{
  "generated_at": "2025-11-17T00:16:30",
  "project_root": "/Users/masa/Projects/epstein",

  "files": {
    "scripts": [...],           // All Python scripts with descriptions
    "data_files": {
      "metadata": [...],        // JSON metadata files
      "entities": [...],        // Entity extraction files
      "canonical_emails": [...], // Deduplicated emails
      "source_pdfs": {...}      // PDF counts by source
    }
  },

  "data_summary": {
    "entities": {
      "total": 1773,
      "billionaires": 33,
      "in_black_book": 1501,
      "in_flight_logs": 273,
      "top_frequent_flyers": [...]
    },
    "documents": {
      "total_files": 67963,
      "unique_documents": 38177,
      "duplicates": 29786,
      "deduplication_rate": "43.8%",
      "sources": {...}
    },
    "emails": {
      "canonical_count": 5,
      "date_range": {...},
      "unique_participants": 21,
      "participant_list": [...]
    },
    "network": {
      "total_nodes": 387,
      "total_edges": 2221,
      "top_connections": [...]
    }
  },

  "ongoing_work": {
    "recent_downloads": [...],
    "pending_classifications": 38174,
    "background_processes": [...]
  },

  "quick_stats": {
    "total_pdfs": 67963,
    "total_emails": 5,
    "unique_documents": 38177,
    "deduplication_rate": "43.8%",
    "unique_entities": 1773,
    "network_nodes": 387,
    "network_edges": 2221
  },

  "search_capabilities": {
    "entity_search": {...},
    "classification_types": [...]
  },

  "key_reports": {
    "entity_network_stats": "...",
    "classification_report": "...",
    "entity_statistics": "..."
  }
}
```

## Usage

### Building the Index

```bash
# Initial build
python3 scripts/metadata/build_chatbot_knowledge_index.py

# Refresh after updates
python3 scripts/metadata/refresh_chatbot_index.py
```

### API Endpoint

```bash
# Query the knowledge index via API
curl -u username:password http://localhost:8000/api/chatbot/knowledge
```

### When to Refresh

Refresh the knowledge index after:
- ✅ New documents downloaded
- ✅ Classifications completed
- ✅ Entity extraction updates
- ✅ Network analysis rebuilt
- ✅ Email canonicalization runs
- ✅ New scripts added

## Chatbot Integration

The chatbot can use this index to answer questions like:

**"How many documents do we have?"**
→ Check `quick_stats.unique_documents`

**"What's the deduplication rate?"**
→ Check `quick_stats.deduplication_rate`

**"How many entities are in the network?"**
→ Check `data_summary.entities.total`

**"What scripts handle classification?"**
→ Check `files.scripts` where `category == "classification"`

**"Are there any downloads in progress?"**
→ Check `ongoing_work.recent_downloads`

**"How many emails have been extracted?"**
→ Check `data_summary.emails.canonical_count`

**"Who are the top connected entities?"**
→ Check `data_summary.network.top_connections`

## File Locations

- **Index File**: `data/metadata/chatbot_knowledge_index.json`
- **Build Script**: `scripts/metadata/build_chatbot_knowledge_index.py`
- **Refresh Script**: `scripts/metadata/refresh_chatbot_index.py`
- **API Endpoint**: `/api/chatbot/knowledge`

## Technical Details

### Performance
- **File Size**: ~25KB
- **Load Time**: <10ms
- **Caching**: Loaded into memory on API call

### Design Decisions

**Single File vs Multiple Reads**
- ✅ **Chosen**: Single consolidated JSON file
- **Rationale**: Faster chatbot responses (1 read vs. 10+ reads)
- **Trade-off**: Must refresh after updates (manual trigger)

**Freshness vs Performance**
- **Approach**: Manual refresh via script
- **Rationale**: Data doesn't change frequently (hours/days between updates)
- **Alternative Considered**: Auto-refresh on API call (rejected: too slow)

**Completeness vs Size**
- **Approach**: Include summaries, not full data
- **Example**: Top 10 connections, not all 2,221 edges
- **Rationale**: Chatbot needs overview, not exhaustive details

## Future Enhancements

1. **Auto-refresh Integration**: Trigger refresh at end of ingestion pipeline
2. **Incremental Updates**: Update specific sections without full rebuild
3. **Caching Layer**: In-memory cache with TTL in API server
4. **Change Detection**: Only rebuild if source files modified
5. **Compression**: Gzip for large indexes (>100KB)

## Maintenance

**Monthly**: Verify index accuracy against source files
**After Major Updates**: Rebuild from scratch
**Production**: Add to CI/CD pipeline for auto-refresh

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
**Status**: Production Ready
