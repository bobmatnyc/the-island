# Content Documentation

**Understanding the data in the Epstein Document Archive**

---

## Overview

This section explains where our data comes from, how it's processed, and how quality is maintained.

---

## Content Guides

| Guide | Description |
|-------|-------------|
| [data-sources.md](data-sources.md) | Complete inventory of all 30+ document sources |
| [entity-extraction.md](entity-extraction.md) | How entities are identified and extracted |
| [classification.md](classification.md) | Document classification system (11 types) |
| [entity-enrichment.md](entity-enrichment.md) | Biographical data collection methodology |
| [data-quality.md](data-quality.md) | Quality assurance processes |

---

## Quick Reference

### Data Sources

- **67,144 PDFs** from House Oversight Committee (Nov 2025)
- **30+ public sources** including court documents, FBI Vault
- **Complete provenance** tracking for every document

See [data-sources.md](data-sources.md) for complete list.

### Entity Extraction

- **1,773 unique entities** extracted from documents
- **3 types**: Person, Organization, Location
- **Automated extraction** with manual verification

See [entity-extraction.md](entity-extraction.md) for methodology.

### Document Classification

- **11 categories**: email, court_filing, financial, flight_log, contact_book, investigative, legal_agreement, personal, media, administrative, unknown
- **Keyword-based** classification with confidence scoring
- **67,144 documents** to classify (6 done, rest pending OCR)

See [classification.md](classification.md) for details.

### Entity Enrichment

- **Biographical data** from public sources
- **AI-assisted** research and extraction
- **Manual verification** of all enrichments

See [entity-enrichment.md](entity-enrichment.md) for process.

---

## Data Pipeline

```
Source Documents
    ↓
OCR Processing (Tesseract)
    ↓
Text Extraction
    ↓
Entity Recognition
    ↓
Document Classification
    ↓
Entity Enrichment
    ↓
Network Analysis
    ↓
Semantic Indexing
```

---

## Data Quality

### High Quality Sources

- Flight logs (manually verified)
- Contact books (clean OCR)
- Court documents (official sources)

### Medium Quality Sources

- Handwritten notes (OCR challenges)
- Lower quality scans

### In Progress

- Email extraction (OCR 45% complete)
- Full document classification
- Entity enrichment (30% complete)

See [data-quality.md](data-quality.md) for QA process.

---

## Related Documentation

- [../research/methodology.md](../research/methodology.md) - Research approach
- [../research/ethics.md](../research/ethics.md) - Ethical guidelines
- [../developer/database.md](../developer/database.md) - Database schema
