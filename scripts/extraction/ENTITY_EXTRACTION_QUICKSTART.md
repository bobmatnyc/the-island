# Entity Extraction - Quick Start Guide

**Last Updated**: 2025-11-17
**Purpose**: Technical guide for implementing automated entity extraction

---

## Prerequisites

### Required Libraries
```bash
# Install NER and NLP tools
pip install spacy spacy-transformers
pip install rapidfuzz python-Levenshtein
pip install recordlinkage
pip install wikipedia-api wptools

# Download spaCy transformer model
python -m spacy download en_core_web_trf

# Install PDF/OCR tools
pip install pymupdf pytesseract
pip install python-email-parser

# Install database connectors
pip install psycopg2-binary neo4j
```

### System Requirements
- Python 3.9+
- 16GB RAM minimum (32GB recommended for large batches)
- GPU optional (speeds up transformer model 5-10x)

---

## Quick Start: Extract Entities from Court Document

### Step 1: Basic NER Extraction

```python
import spacy
from collections import Counter

# Load transformer model (best accuracy)
nlp = spacy.load("en_core_web_trf")

def extract_entities(text, doc_id):
    """Extract PERSON and ORG entities from text"""
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG"]:
            entities.append({
                "text": ent.text,
                "type": ent.label_,
                "source_doc": doc_id,
                "confidence": 0.9,  # Default confidence
                "context": doc[max(0, ent.start-5):min(len(doc), ent.end+5)].text
            })

    return entities

# Example usage
with open("/path/to/court_document.txt", "r") as f:
    text = f.read()

entities = extract_entities(text, doc_id="giuffre_v_maxwell_001")
print(f"Found {len(entities)} entities")

# Show top entities by frequency
entity_names = [e["text"] for e in entities]
top_entities = Counter(entity_names).most_common(20)
for name, count in top_entities:
    print(f"{name}: {count} mentions")
```

**Expected Output:**
```
Found 347 entities
Jeffrey Epstein: 52 mentions
Ghislaine Maxwell: 41 mentions
Virginia Giuffre: 38 mentions
Prince Andrew: 15 mentions
...
```

---

## Step 2: Extract Entities from Email Headers

```python
import email
import re
from pathlib import Path

def extract_email_entities(email_file):
    """Extract sender/recipient entities from email"""
    with open(email_file, 'rb') as f:
        msg = email.message_from_binary_file(f)

    entities = []

    # Extract From field
    from_field = msg.get('From', '')
    from_name = extract_name_from_email(from_field)
    if from_name:
        entities.append({
            "text": from_name,
            "type": "PERSON",
            "role": "sender",
            "email": extract_email_address(from_field)
        })

    # Extract To field
    to_field = msg.get('To', '')
    for recipient in to_field.split(','):
        to_name = extract_name_from_email(recipient.strip())
        if to_name:
            entities.append({
                "text": to_name,
                "type": "PERSON",
                "role": "recipient",
                "email": extract_email_address(recipient)
            })

    # Extract CC field
    cc_field = msg.get('Cc', '')
    for recipient in cc_field.split(','):
        cc_name = extract_name_from_email(recipient.strip())
        if cc_name:
            entities.append({
                "text": cc_name,
                "type": "PERSON",
                "role": "cc",
                "email": extract_email_address(recipient)
            })

    return entities

def extract_name_from_email(email_string):
    """Extract display name from 'John Doe <john@example.com>' format"""
    match = re.match(r'([^<]+)<', email_string)
    if match:
        return match.group(1).strip().strip('"')
    return None

def extract_email_address(email_string):
    """Extract email address from string"""
    match = re.search(r'<([^>]+)>', email_string)
    if match:
        return match.group(1)
    # If no angle brackets, assume entire string is email
    return email_string.strip() if '@' in email_string else None

# Process all emails in directory
email_dir = Path("/Users/masa/Projects/Epstein/data/md/house_oversight_nov2025/emails/")
all_entities = []

for email_file in email_dir.glob("*.eml"):
    entities = extract_email_entities(email_file)
    all_entities.extend(entities)

print(f"Extracted {len(all_entities)} entity mentions from emails")

# Deduplicate
unique_entities = {}
for ent in all_entities:
    name = ent["text"]
    if name not in unique_entities:
        unique_entities[name] = ent

print(f"Unique entities: {len(unique_entities)}")
```

---

## Step 3: Deduplicate Entities with Fuzzy Matching

```python
from rapidfuzz import fuzz, process

def deduplicate_entities(entities, threshold=85):
    """
    Deduplicate entity list using fuzzy name matching

    Args:
        entities: List of entity dicts with "text" field
        threshold: Similarity threshold (0-100)

    Returns:
        Deduplicated entity list with merged variations
    """
    # Build canonical name mapping
    canonical_names = {}
    name_variations = {}

    for entity in entities:
        name = entity["text"]

        # Find best match in existing canonical names
        if canonical_names:
            match = process.extractOne(
                name,
                canonical_names.keys(),
                scorer=fuzz.token_sort_ratio
            )

            if match and match[1] >= threshold:
                # This is a variation of existing canonical name
                canonical = match[0]
                canonical_names[canonical]["count"] += 1
                if name != canonical:
                    if canonical not in name_variations:
                        name_variations[canonical] = []
                    name_variations[canonical].append(name)
            else:
                # New canonical name
                canonical_names[name] = {
                    "canonical_name": name,
                    "count": 1,
                    "type": entity.get("type", "PERSON"),
                    "sources": [entity.get("source_doc", "unknown")]
                }
        else:
            # First entity
            canonical_names[name] = {
                "canonical_name": name,
                "count": 1,
                "type": entity.get("type", "PERSON"),
                "sources": [entity.get("source_doc", "unknown")]
            }

    # Add variations to canonical names
    for canonical, data in canonical_names.items():
        if canonical in name_variations:
            data["variations"] = name_variations[canonical]

    return list(canonical_names.values())

# Example usage
entities = extract_entities(text, doc_id="test_doc")
deduplicated = deduplicate_entities(entities, threshold=85)

print(f"Before deduplication: {len(entities)} entities")
print(f"After deduplication: {len(deduplicated)} entities")

# Show entities with variations
for ent in deduplicated:
    if "variations" in ent:
        print(f"{ent['canonical_name']} (variations: {', '.join(ent['variations'])})")
```

**Expected Output:**
```
Before deduplication: 347 entities
After deduplication: 241 entities

William Clinton (variations: Bill Clinton, Clinton Bill)
Alexander Resnick (variations: Alex Resnick)
Andrew Stewart (variations: Andy Stewart)
```

---

## Step 4: Cross-Reference with Existing Entity Index

```python
import json

def load_entity_index():
    """Load existing entity index from ENTITIES_INDEX.json"""
    with open("/Users/masa/Projects/Epstein/data/md/entities/ENTITIES_INDEX.json", 'r') as f:
        data = json.load(f)

    # Extract entity list
    if "entities" in data:
        return data["entities"]
    else:
        # Fallback: assume data is direct entity list
        return data

def match_to_existing_entities(new_entities, entity_index, threshold=85):
    """
    Match new entities to existing entity index

    Returns:
        {
            "matched": [...],  # Entities found in existing index
            "new": [...]       # Entities not in existing index
        }
    """
    existing_names = [ent["normalized_name"] for ent in entity_index if isinstance(ent, dict)]

    matched = []
    new = []

    for entity in new_entities:
        name = entity["text"]

        # Try exact match first
        if name in existing_names:
            matched.append({
                "new_entity": entity,
                "matched_to": name,
                "confidence": 1.0
            })
            continue

        # Try fuzzy match
        match = process.extractOne(
            name,
            existing_names,
            scorer=fuzz.token_sort_ratio
        )

        if match and match[1] >= threshold:
            matched.append({
                "new_entity": entity,
                "matched_to": match[0],
                "confidence": match[1] / 100.0
            })
        else:
            new.append(entity)

    return {
        "matched": matched,
        "new": new,
        "stats": {
            "total_new_entities": len(new_entities),
            "matched_to_existing": len(matched),
            "truly_new": len(new),
            "match_rate": len(matched) / len(new_entities) * 100
        }
    }

# Example usage
entity_index = load_entity_index()
new_entities = extract_entities(text, doc_id="court_doc_123")

results = match_to_existing_entities(new_entities, entity_index)

print(f"Total new entities: {results['stats']['total_new_entities']}")
print(f"Matched to existing: {results['stats']['matched_to_existing']}")
print(f"Truly new entities: {results['stats']['truly_new']}")
print(f"Match rate: {results['stats']['match_rate']:.1f}%")

# Show truly new entities
print("\nNew entities not in existing index:")
for ent in results["new"][:20]:  # Top 20
    print(f"  - {ent['text']} ({ent['type']})")
```

---

## Step 5: Enrich with Wikipedia Biographical Data

```python
import wikipedia
import wptools

def enrich_entity_with_wikipedia(entity_name):
    """
    Fetch biographical data from Wikipedia

    Returns:
        Dict with biographical fields or None if not found
    """
    try:
        # Search Wikipedia
        search_results = wikipedia.search(entity_name, results=3)
        if not search_results:
            return None

        # Try to fetch page
        page = wikipedia.page(search_results[0], auto_suggest=False)

        # Get structured data from Wikidata
        wp_page = wptools.page(page.title, silent=True).get()

        return {
            "wikipedia_title": page.title,
            "wikipedia_url": page.url,
            "summary": wikipedia.summary(search_results[0], sentences=3),
            "born": wp_page.data.get("born"),
            "died": wp_page.data.get("died"),
            "occupation": wp_page.data.get("occupation"),
            "nationality": wp_page.data.get("nationality"),
            "birthplace": wp_page.data.get("birthplace")
        }

    except wikipedia.exceptions.DisambiguationError as e:
        # Multiple people with same name
        return {"error": "disambiguation", "options": e.options}
    except wikipedia.exceptions.PageError:
        # No Wikipedia page
        return None
    except Exception as e:
        return {"error": str(e)}

# Example usage
entity_name = "Ghislaine Maxwell"
bio_data = enrich_entity_with_wikipedia(entity_name)

if bio_data:
    print(f"Wikipedia: {bio_data['wikipedia_url']}")
    print(f"Born: {bio_data.get('born', 'Unknown')}")
    print(f"Occupation: {bio_data.get('occupation', 'Unknown')}")
    print(f"Summary: {bio_data['summary']}")
else:
    print(f"No Wikipedia page found for {entity_name}")
```

---

## Complete Processing Pipeline

```python
import json
from pathlib import Path
import spacy
from rapidfuzz import fuzz, process

# Load NER model
nlp = spacy.load("en_core_web_trf")

def process_document_collection(doc_directory, output_file):
    """
    Complete pipeline: Extract → Deduplicate → Match → Export

    Args:
        doc_directory: Path to directory of text documents
        output_file: Path to save extracted entities JSON
    """
    print("Step 1: Extracting entities from documents...")
    all_entities = []

    for doc_file in Path(doc_directory).glob("*.txt"):
        with open(doc_file, 'r') as f:
            text = f.read()

        entities = extract_entities(text, doc_id=doc_file.stem)
        all_entities.extend(entities)

    print(f"  Extracted {len(all_entities)} entity mentions")

    print("\nStep 2: Deduplicating entities...")
    deduplicated = deduplicate_entities(all_entities, threshold=85)
    print(f"  Deduplicated to {len(deduplicated)} unique entities")

    print("\nStep 3: Matching to existing entity index...")
    entity_index = load_entity_index()
    results = match_to_existing_entities(deduplicated, entity_index)

    print(f"  Matched {results['stats']['matched_to_existing']} to existing")
    print(f"  Found {results['stats']['truly_new']} new entities")

    print("\nStep 4: Saving results...")
    output = {
        "extraction_date": "2025-11-17",
        "source_directory": str(doc_directory),
        "total_documents_processed": len(list(Path(doc_directory).glob("*.txt"))),
        "statistics": results["stats"],
        "matched_entities": results["matched"],
        "new_entities": results["new"]
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  Saved to {output_file}")
    return output

# Run pipeline
results = process_document_collection(
    doc_directory="/Users/masa/Projects/Epstein/data/md/giuffre_maxwell/",
    output_file="/Users/masa/Projects/Epstein/data/metadata/extracted_entities_giuffre_maxwell.json"
)
```

---

## Performance Tips

### 1. Batch Processing for Large Datasets

```python
# Process in batches of 100 documents
from tqdm import tqdm

def process_large_corpus(doc_files, batch_size=100):
    """Process large corpus in batches with progress bar"""
    all_entities = []

    # Create batches
    batches = [doc_files[i:i+batch_size] for i in range(0, len(doc_files), batch_size)]

    for batch in tqdm(batches, desc="Processing batches"):
        batch_entities = []
        for doc_file in batch:
            with open(doc_file, 'r') as f:
                text = f.read()
            entities = extract_entities(text, doc_id=doc_file.stem)
            batch_entities.extend(entities)

        # Deduplicate within batch
        batch_dedup = deduplicate_entities(batch_entities)
        all_entities.extend(batch_dedup)

    # Final deduplication across all batches
    return deduplicate_entities(all_entities)
```

### 2. GPU Acceleration

```python
# Use GPU if available (5-10x speedup for transformers)
import spacy

# Check if GPU available
spacy.prefer_gpu()

nlp = spacy.load("en_core_web_trf")
print(f"Using GPU: {spacy.prefer_gpu()}")
```

### 3. Parallel Processing

```python
from multiprocessing import Pool

def process_single_document(doc_file):
    """Process single document (for parallel execution)"""
    with open(doc_file, 'r') as f:
        text = f.read()
    return extract_entities(text, doc_id=doc_file.stem)

def process_parallel(doc_files, num_workers=4):
    """Process documents in parallel"""
    with Pool(num_workers) as pool:
        results = pool.map(process_single_document, doc_files)

    # Flatten results
    all_entities = [ent for doc_entities in results for ent in doc_entities]
    return all_entities
```

---

## Troubleshooting

### Issue: Low accuracy on OCR'd documents

**Solution**: Clean OCR text first
```python
import re

def clean_ocr_text(text):
    """Remove common OCR artifacts"""
    # Remove excessive whitespace in names
    text = re.sub(r'(\w)\s+(\w)', r'\1\2', text)

    # Fix common OCR errors
    text = text.replace('G h i s l a i n e', 'Ghislaine')
    text = text.replace('J e f f r e y', 'Jeffrey')

    # Remove page numbers, headers
    text = re.sub(r'Page \d+', '', text)

    return text
```

### Issue: Too many false positives

**Solution**: Filter by entity confidence and frequency
```python
def filter_entities(entities, min_confidence=0.8, min_frequency=2):
    """Filter low-confidence and rare entities"""
    from collections import Counter

    # Filter by confidence
    high_conf = [e for e in entities if e.get("confidence", 0) >= min_confidence]

    # Count frequencies
    name_counts = Counter([e["text"] for e in high_conf])

    # Filter by frequency
    filtered = [e for e in high_conf if name_counts[e["text"]] >= min_frequency]

    return filtered
```

---

## Next Steps

1. **Test on sample documents**: Run extraction on 10-20 documents
2. **Evaluate accuracy**: Manually review top 50 entities
3. **Tune thresholds**: Adjust confidence and frequency filters
4. **Scale up**: Process full corpus in batches
5. **Integrate with database**: Load entities into PostgreSQL

**Full Research Report**: `/data/metadata/ENTITY_DATA_EXPANSION_RESEARCH_REPORT.md`

**Questions?** See project README or contact repository maintainers.
