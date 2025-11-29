# Getting Started - User Guide

**Quick Summary**: **Quick start guide for first-time users of the Epstein Document Archive**...

**Category**: User
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **67,144+ documents** from 30+ public sources
- **1,773 unique entities** (people, organizations)
- **Entity relationship network** with 2,221 documented connections
- **Semantic search** to find documents by entity mentions
- **Document classification** into 11 categories

---

**Quick start guide for first-time users of the Epstein Document Archive**

**Last Updated**: November 17, 2025

---

## Welcome

This guide will help you start using the Epstein Document Archive to search and explore documents, entities, and relationships.

---

## What is This System?

The Epstein Document Archive is a comprehensive, searchable database of publicly available Jeffrey Epstein-related documents with:

- **67,144+ documents** from 30+ public sources
- **1,773 unique entities** (people, organizations)
- **Entity relationship network** with 2,221 documented connections
- **Semantic search** to find documents by entity mentions
- **Document classification** into 11 categories
- **Complete source provenance** for every document

---

## 5-Minute Quick Start

### Prerequisites

Before starting, ensure you have:
- Python 3.11+ installed
- Node.js 18+ installed (for frontend)
- Active internet connection (for first-time model download)

**First-Run Model Download**: The system uses the `all-MiniLM-L6-v2` sentence-transformers model for semantic search. On first run, this model (~90MB) will be automatically downloaded and cached. See [Model Requirements](#model-requirements) below for details.

### 1. Access the Web Interface

Open your browser and visit:
```
http://localhost:8081/
```

You'll see the main interface with four sections:
- **Entities**: Browse and search entities
- **Documents**: Search and view documents
- **Flights**: Explore flight logs
- **Network**: Visualize entity relationships

### 2. Search for an Entity

**Via Web Interface**:
1. Click "Entities" in navigation
2. Type a name in the search box (e.g., "Clinton")
3. Click on entity to see details and connections

**Via Command Line**:
```bash
python3 scripts/search/entity_search.py --entity "Clinton"
```

### 3. View Entity Connections

**Via Web Interface**:
1. Open an entity's detail page
2. Click "Connections" tab
3. See all documented relationships

**Via Command Line**:
```bash
python3 scripts/search/entity_search.py --connections "Ghislaine Maxwell"
```

### 4. Explore Flight Logs

**Via Web Interface**:
1. Click "Flights" in navigation
2. Use date range filters
3. Click on flights to see passenger lists

**Via Data Files**:
```bash
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]))'
```

### 5. Visualize the Network

**Via Web Interface**:
1. Click "Network" in navigation
2. Use filters to show/hide entities
3. Click nodes to see details
4. Hover over edges to see relationships

---

## Understanding the Interface

### Entities Page

**Features**:
- Search by name
- Filter by type (person, organization)
- Sort by connections
- View biographical information
- See document mentions

**Key Fields**:
- **Name**: Entity name
- **Type**: Person, Organization, Location
- **Connections**: Number of documented relationships
- **Documents**: Documents mentioning this entity
- **Bio**: Biographical information (when available)

### Documents Page

**Features**:
- Full-text search
- Filter by type (email, court filing, etc.)
- Filter by date range
- Filter by source
- View document content

**Document Types**:
- Email
- Court Filing
- Financial Document
- Flight Log
- Contact Book
- Investigative Report
- Legal Agreement
- Personal Note
- Media Article
- Administrative Document

### Flights Page

**Features**:
- Browse flights chronologically
- Filter by date range
- Filter by passenger
- See all passengers per flight
- View flight routes (when available)

**Flight Data**:
- **Date**: Flight date
- **Passengers**: List of passengers
- **Route**: Origin → Destination (when available)
- **Tail Number**: Aircraft identifier

### Network Page

**Features**:
- Interactive force-directed graph
- Zoom and pan
- Click nodes for details
- Filter by connection count
- Highlight specific entities

**Graph Elements**:
- **Nodes**: Entities (sized by connections)
- **Edges**: Relationships (weighted by strength)
- **Colors**: Entity types
- **Labels**: Entity names

---

## Model Requirements

### Sentence-Transformers Model

The system uses the **`all-MiniLM-L6-v2`** model from the sentence-transformers library for semantic search and document embedding. This is a lightweight, efficient model for generating 384-dimensional embeddings.

**Model Specifications**:
- **Model Name**: `sentence-transformers/all-MiniLM-L6-v2`
- **Download Size**: ~90MB
- **Embedding Dimensions**: 384
- **Purpose**: Semantic search, document similarity, RAG (Retrieval-Augmented Generation)

### First-Run Download

**Automatic Download**:
The model is downloaded automatically on first use when you:
- Start the backend server (`python server/app.py`)
- Run RAG scripts (`python scripts/rag/query_rag.py`)
- Use semantic search features

**What to Expect**:
```bash
$ python server/app.py

Loading sentence-transformers model...
Model: all-MiniLM-L6-v2 (384 dimensions)
Downloading model files... (this may take 1-2 minutes)
✅ Model loaded successfully
```

**Network Requirements**:
- Active internet connection for first download
- ~90MB bandwidth
- Firewall/proxy must allow access to `huggingface.co`

### Model Caching

**Cache Location**:
- **Default**: `~/.cache/huggingface/hub/`
- **Linux/Mac**: `/home/username/.cache/huggingface/hub/`
- **Windows**: `C:\Users\username\.cache\huggingface\hub\`

**Cache Size**: ~90MB once downloaded

**Verify Cached Model**:
```bash
# Check if model is cached
ls -lh ~/.cache/huggingface/hub/ | grep all-MiniLM-L6-v2

# Expected output shows model directory
# models--sentence-transformers--all-MiniLM-L6-v2
```

### Offline Installation

For environments without internet access, pre-download the model:

**Step 1: Download on a connected machine**:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Step 2: Copy cache directory**:
```bash
# On source machine (with internet)
tar -czf model-cache.tar.gz ~/.cache/huggingface/hub/

# Transfer model-cache.tar.gz to target machine

# On target machine (without internet)
tar -xzf model-cache.tar.gz -C ~/
```

**Step 3: Verify installation**:
```bash
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print('Model loaded successfully!')"
```

### Troubleshooting Model Download

**Network Timeout Errors**:
```bash
# Increase download timeout (default: 60 seconds)
export HF_HUB_DOWNLOAD_TIMEOUT=300

# Run server again
python server/app.py
```

**Proxy/Firewall Issues**:
```bash
# Configure HTTP proxy
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# Run server again
python server/app.py
```

**SSL Certificate Errors**:
```bash
# Disable SSL verification (use with caution)
export CURL_CA_BUNDLE=""
python server/app.py
```

**Disk Space Issues**:
```bash
# Check available space
df -h ~/.cache/

# Clean old model cache if needed
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--*
```

**Manual Model Verification**:
```bash
# Test model loading independently
python -c "
from sentence_transformers import SentenceTransformer
import sys

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f'✅ Model loaded successfully')
    print(f'Model name: {model._model_card_vars.get(\"model_name\", \"unknown\")}')
    print(f'Embedding dimension: {model.get_sentence_embedding_dimension()}')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
```

**Custom Cache Location**:
```bash
# Set custom cache directory
export HF_HOME=/custom/path/to/cache
export TRANSFORMERS_CACHE=/custom/path/to/cache

# Run server
python server/app.py
```

### Performance Notes

- **First Load**: 1-2 seconds (reading from cache)
- **Subsequent Loads**: <500ms (model stays in memory)
- **Memory Usage**: ~150MB RAM when loaded
- **Model Reuse**: All scripts share the same cached model

---

## Common Search Tasks

### Find All Documents Mentioning an Entity

**Web Interface**:
1. Go to Entities page
2. Search for entity name
3. Click entity
4. View "Documents" tab

**Command Line**:
```bash
python3 scripts/search/entity_search.py --entity "Prince Andrew"
```

### Find Connections Between Entities

**Web Interface**:
1. Open first entity's page
2. Look in "Connections" list for second entity
3. Click connection to see shared documents

**Command Line**:
```bash
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein" "Maxwell"
```

### Find All Emails

**Web Interface**:
1. Go to Documents page
2. Filter by type: "Email"
3. Browse results

**Command Line**:
```bash
python3 scripts/search/entity_search.py --type "email"
```

### Find Flights with Specific Passenger

**Web Interface**:
1. Go to Flights page
2. Enter passenger name in filter
3. See all flights

**Data Query**:
```bash
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]))'
```

### Explore Entity Network

**Web Interface**:
1. Go to Network page
2. Enter entity name in search
3. Graph highlights entity and connections
4. Click nodes to explore further

---

## Understanding Entity Data

### Entity Types

**Person**:
- Individuals mentioned in documents
- Includes biographical data when available
- Shows network connections

**Organization**:
- Companies, foundations, institutions
- Includes description when available
- Shows affiliated individuals

**Location**:
- Places mentioned in flight logs or documents
- Includes address/coordinates when available

### Entity Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Primary name | "Ghislaine Maxwell" |
| **Aliases** | Alternative names | ["Maxwell", "G. Maxwell"] |
| **Type** | Entity classification | "Person" |
| **Bio** | Biographical info | "British socialite..." |
| **Connections** | Number of relationships | 190 |
| **Documents** | Mentioning documents | 12 |
| **First Seen** | First document date | "1999-03-15" |
| **Last Seen** | Last document date | "2005-11-20" |

---

## Understanding Network Data

### Connection Types

**Flight Co-occurrence**:
- Entities who flew together
- Strength = number of shared flights
- Source: Flight logs

**Document Co-mention**:
- Entities mentioned in same documents
- Strength = number of shared documents
- Source: All document types

**Direct Relationship**:
- Explicitly stated relationships
- Type: employer, family, associate, etc.
- Source: Biographical data

### Network Metrics

**Connection Count**:
- Number of documented relationships
- Higher = more central in network

**Betweenness Centrality**:
- How often entity connects other entities
- Higher = more "bridging" role

**Clustering Coefficient**:
- How connected an entity's connections are
- Higher = tighter local network

---

## Tips and Best Practices

### Effective Searching

1. **Start broad, then narrow**
   - Begin with entity name only
   - Add filters as needed

2. **Use multiple search methods**
   - Try both web interface and command line
   - Different views reveal different insights

3. **Check aliases**
   - Entities may have multiple names
   - "Clinton" vs "Bill Clinton" vs "William Jefferson Clinton"

4. **Explore connections**
   - Don't just search target entity
   - Look at their connections for context

5. **Verify sources**
   - Always check document provenance
   - Original source links provided

### Understanding Results

1. **Connection strength matters**
   - Single co-occurrence vs dozens
   - Weight connections appropriately

2. **Date context**
   - When did relationships exist?
   - Flight logs span 1997-2006 primarily

3. **Document types**
   - Different sources = different perspectives
   - Court documents vs personal notes

4. **Missing data**
   - Not all documents OCR'd yet (45% complete)
   - More data coming as OCR finishes

---

## Data Limitations

### Current Limitations

1. **OCR in Progress**
   - Only 45% of documents processed
   - Full text search incomplete for 55%

2. **Classification Incomplete**
   - Only entity documents fully classified
   - 67,144 documents pending classification

3. **Biographical Data Partial**
   - ~30% of entities have bios
   - Enrichment ongoing

4. **Redactions Present**
   - Some documents have redactions
   - Information may be incomplete

### Data Quality

**High Quality**:
- Flight logs (manually verified)
- Contact books (clean OCR)
- Court filings (official documents)

**Medium Quality**:
- Personal notes (handwriting issues)
- Some older PDFs (low scan quality)

**In Progress**:
- Email extraction (pending OCR)
- Full document classification

---

## Next Steps

### Learn More

1. **Search Guide**: [searching.md](searching.md)
   - Advanced search techniques
   - Query syntax
   - Filters and operators

2. **Entity Guide**: [entities.md](entities.md)
   - Entity database structure
   - Entity enrichment
   - Biographical sources

3. **Flight Guide**: [flights.md](flights.md)
   - Flight log analysis
   - Passenger identification
   - Route mapping

4. **Network Guide**: [network-analysis.md](network-analysis.md)
   - Network visualization
   - Relationship types
   - Graph analysis

### Get Help

- **FAQ**: [faq.md](faq.md)
- **Troubleshooting**: [../operations/troubleshooting.md](../operations/troubleshooting.md)
- **GitHub Issues**: Report problems or request features

---

## Quick Reference

### Essential Commands

```bash
# Search for entity
python3 scripts/search/entity_search.py --entity "NAME"

# View entity connections
python3 scripts/search/entity_search.py --connections "NAME"

# Multi-entity search
python3 scripts/search/entity_search.py --multiple "NAME1" "NAME2"

# Search by document type
python3 scripts/search/entity_search.py --type "email"

# View network statistics
cat data/metadata/entity_network_stats.txt

# Browse entity index
cat data/md/entities/ENTITIES_INDEX.json | jq '.'
```

### Essential Files

- **Entity Index**: `data/md/entities/ENTITIES_INDEX.json`
- **Entity Network**: `data/metadata/entity_network.json`
- **Flight Logs**: `data/md/entities/flight_logs_by_flight.json`
- **Document Classifications**: `data/metadata/document_classifications.json`
- **Network Statistics**: `data/metadata/entity_network_stats.txt`

---

## Feedback

We welcome feedback on this guide and the system:

- **Documentation unclear?** [Open an issue](https://github.com/yourusername/epstein-document-archive/issues)
- **Feature request?** [Open an issue](https://github.com/yourusername/epstein-document-archive/issues)
- **Bug found?** [Report it](https://github.com/yourusername/epstein-document-archive/issues)

---

**Happy searching!**

**Next**: [Searching Guide](searching.md) for advanced search techniques
