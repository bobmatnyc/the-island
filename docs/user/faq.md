# Frequently Asked Questions (FAQ)

**Quick Summary**: **Common questions about the Epstein Document Archive**...

**Category**: User
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- House Oversight Committee release (67,144 PDFs)
- Court documents (Giuffre v. Maxwell, etc.)
- Flight logs and contact books
- Public records
- Last major update: House Oversight Nov 2025 release

---

**Common questions about the Epstein Document Archive**

---

## General Questions

### What is this project?

A comprehensive, searchable archive of publicly available Jeffrey Epstein-related documents with entity extraction, relationship mapping, and semantic search capabilities.

### Where does the data come from?

30+ public sources including:
- House Oversight Committee release (67,144 PDFs)
- Court documents (Giuffre v. Maxwell, etc.)
- FBI Vault
- Flight logs and contact books
- Public records

See [../content/data-sources.md](../content/data-sources.md) for complete list.

### Is all the data from public sources?

Yes. All documents are from publicly available sources with proper attribution and provenance tracking.

### How current is the data?

- Last major update: House Oversight Nov 2025 release
- OCR processing: 45% complete (ongoing)
- Entity enrichment: Ongoing
- Updated regularly as new sources emerge

---

## Search Questions

### How do I search for a person?

**Web**: Go to Entities tab, enter name in search box

**Command line**:
```bash
python3 scripts/search/entity_search.py --entity "NAME"
```

### Why can't I find a specific person?

Possible reasons:
1. Name spelling variation (try alternative spellings)
2. Not in indexed documents
3. Document OCR pending (45% complete)
4. Name redacted in source documents

### How do I see connections between people?

**Web**: Click entity → "Connections" tab

**Command line**:
```bash
python3 scripts/search/entity_search.py --connections "NAME"
```

### Can I search document content?

Full-text search available for OCR'd documents (45% complete). More coming as OCR processing finishes.

---

## Data Questions

### How many documents are in the archive?

- Total: 67,144+ PDFs (House Oversight)
- OCR'd: 15,100 (45%)
- Expected emails: ~2,330
- Entity documents: 6 (flight logs, contact books)

### How many entities are indexed?

- Total entities: 1,773
- With network connections: 387
- Documented relationships: 2,221

### What document types are included?

11 categories:
- Email
- Court filing
- Financial document
- Flight log
- Contact book
- Investigative report
- Legal agreement
- Personal note
- Media article
- Administrative document
- Unknown

### How accurate is the data?

**High quality**:
- Flight logs (manually verified)
- Contact books (clean OCR)
- Court documents (official sources)

**Medium quality**:
- Handwritten notes (OCR challenges)
- Lower quality scans

**In progress**:
- Email extraction
- Full classification
- Entity enrichment

---

## Technical Questions

### Can I download the data?

Yes. All processed data available in `data/` directory:
- Entity index: `data/md/entities/ENTITIES_INDEX.json`
- Network graph: `data/metadata/entity_network.json`
- Flight logs: `data/md/entities/flight_logs_by_flight.json`

### Is there an API?

Yes. See [../developer/api/](../developer/api/) for documentation.

Web interface runs at: `http://localhost:8081/`

### Can I contribute?

Yes! See [../../CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

### What technologies are used?

- **Backend**: Python, FastAPI
- **Frontend**: React, Vite, TypeScript
- **OCR**: Tesseract, PyMuPDF
- **NLP**: spaCy, sentence-transformers
- **Semantic Search**: sentence-transformers (all-MiniLM-L6-v2)
- **Data**: JSON, ChromaDB
- **Search**: Python scripts, semantic indexing, RAG

### What is the sentence-transformers model?

The system uses the `all-MiniLM-L6-v2` model for semantic search:

- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Size**: ~90MB (one-time download)
- **Purpose**: Generate embeddings for semantic search
- **Cache**: ~/.cache/huggingface/hub/
- **First-run**: Requires internet connection

See [getting-started.md#model-requirements](getting-started.md#model-requirements) for details.

### Do I need internet to use this?

**First-time setup**: Yes (to download 90MB model)

**After setup**: No (model is cached locally)

**For offline installation**: Transfer model cache from connected machine (see FAQ troubleshooting)

---

## Privacy & Ethics Questions

### Is this legal?

Yes. All documents are from public sources. We maintain proper attribution and provenance.

### What about privacy?

- Focus on public figures and public interest
- Respect privacy of non-public individuals
- Follow ethical research guidelines

See [../research/ethics.md](../research/ethics.md)

### Can I use this data for research?

Yes. Please cite the project and maintain ethical standards.

### Who maintains this?

Open source project. See [../../CONTRIBUTING.md](../../CONTRIBUTING.md) to contribute.

---

## Troubleshooting

### Server won't start / "Model download error"

**First-time setup requires downloading a 90MB model file.**

**Solution**:
```bash
# Check internet connection
ping huggingface.co

# Manually download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Increase timeout if needed
export HF_HUB_DOWNLOAD_TIMEOUT=300
python server/app.py
```

See [getting-started.md#model-requirements](getting-started.md#model-requirements) for detailed troubleshooting.

### "Model not found" error

The sentence-transformers model wasn't cached properly.

**Solution**:
```bash
# Verify cache location
ls -lh ~/.cache/huggingface/hub/ | grep all-MiniLM-L6-v2

# Re-download if missing
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Network timeout during first run

Default timeout may be too short for slower connections.

**Solution**:
```bash
# Increase timeout to 5 minutes
export HF_HUB_DOWNLOAD_TIMEOUT=300

# Configure proxy if needed
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# Run server
python server/app.py
```

### Offline installation / No internet connection

**Solution - Transfer model from connected machine**:
```bash
# On machine WITH internet
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
tar -czf model-cache.tar.gz ~/.cache/huggingface/hub/

# Transfer file to offline machine

# On machine WITHOUT internet
tar -xzf model-cache.tar.gz -C ~/
```

### Search returns no results

Try:
1. Alternative name spellings
2. Partial name match
3. Check entity index directly
4. Wait for OCR completion (if recent docs)

### Connection count seems low

Possible reasons:
1. OCR incomplete (45% done)
2. Only flight co-occurrence counted currently
3. Document co-mentions coming in next update

### Network graph won't load

Try:
1. Refresh page
2. Reduce connection threshold filter
3. Clear browser cache
4. Check browser console for errors

### Document shows as "Unknown" type

Classification in progress. Only 6 documents fully classified. 67,144 documents pending after OCR completion.

---

## More Help

- **Troubleshooting**: [../operations/troubleshooting.md](../operations/troubleshooting.md)
- **User Guide**: [getting-started.md](getting-started.md)
- **GitHub Issues**: [Report a problem](https://github.com/yourusername/epstein-document-archive/issues)

---

**Still have questions?** [Open an issue](https://github.com/yourusername/epstein-document-archive/issues)
