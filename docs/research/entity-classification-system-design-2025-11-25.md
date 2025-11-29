# Entity Classification System Design

**Research Report**
**Date:** 2025-11-25
**Objective:** Design an AI-powered entity classification system based on relationship analysis
**Status:** Research Complete - Ready for Implementation

---

## Executive Summary

This research report proposes a comprehensive entity classification system for the Epstein Archive that categorizes 1,637 entities based on their relationships and roles within the network. The system leverages Grok-4.1-fast LLM to analyze biography text, network connections, and document sources to assign relationship-based categories with confidence scoring.

**Key Findings:**
- **Current Coverage:** 269 entities (16.4%) have biographies suitable for classification
- **Network Data:** 1,482 relationship edges, 284 nodes in network graph
- **Data Sources:** Black Book (contact listings), Flight Logs, Document mentions
- **Implementation Readiness:** Existing Grok API infrastructure can be extended for classification

**Recommended Approach:** Multi-label classification with hierarchical taxonomy, confidence scoring, and manual review workflow for high-profile entities.

---

## 1. Current Data Analysis

### 1.1 Entity Data Structure

**Database Schema (`entities.db`):**
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,                -- Normalized entity ID (e.g., "jeffrey_epstein")
    display_name TEXT NOT NULL,         -- Full display name
    normalized_name TEXT,               -- Normalized version for matching
    entity_type TEXT,                   -- person, organization, location, etc.
    aliases TEXT,                       -- JSON array of alternative names
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    guid TEXT                           -- Global unique identifier
);
```

**Entity Statistics (`entity_statistics.json`):**
- **Total entities:** 1,637
- **All persons:** 100% (no organizations/locations currently)
- **Entities with GUIDs:** 1,318 (80.5%)

**Available Metadata per Entity:**
```json
{
  "id": "string",
  "name": "string",
  "name_variations": ["array"],
  "in_black_book": boolean,
  "is_billionaire": boolean,
  "categories": ["array"],          // Currently empty - TARGET for classification
  "sources": ["array"],             // black_book, flight_logs, documents
  "total_documents": number,
  "document_types": ["array"],
  "documents": ["array"],
  "flight_count": number,
  "connection_count": number,
  "top_connections": ["array"],     // Names of most frequent co-travelers
  "has_connections": boolean,
  "appears_in_multiple_sources": boolean,
  "guid": "string"
}
```

### 1.2 Biography Coverage

**Biography Statistics (`entity_biographies.json`):**
- **Total biographies:** 269 entities (16.4% coverage)
- **Generation method:** Grok-4.1-fast LLM via OpenRouter API
- **Average quality score:** 0.95 (high quality)
- **Average word count:** 200-250 words
- **Recent batches:** Batch 2 (50 entities), Batch 3a/3b (100+ entities)

**Biography Content Structure:**
```json
{
  "entity_id": {
    "name": "Display Name",
    "summary": "150-300 word biography text focusing on relationship to Epstein",
    "generated_by": "grok-4.1-fast",
    "quality_score": 0.95,
    "word_count": 265,
    "generated_at": "2025-11-25T13:44:07.340893+00:00"
  }
}
```

**Biography Focus Areas (from existing prompts):**
1. Apparent role or relationship to Jeffrey Epstein
2. Timeframe of involvement (from flight dates when available)
3. Network position (connections, frequency of contact)
4. Observable patterns from data
5. Public information for known figures

### 1.3 Network Graph Analysis

**Network Structure (`entity_network.json`):**
- **Total nodes:** 284 (high-connectivity subset)
- **Total edges:** 1,482 relationships
- **Max connections:** 262 (Jeffrey Epstein - central node)
- **Edge types:** Currently all default to "FLEW_TOGETHER"

**Key Entities by Connection Count:**
1. Jeffrey Epstein: 262 connections
2. Ghislaine Maxwell: 188 connections
3. Eva Dubin: 44 connections
4. Celina Dubin: 42 connections
5. Glenn Dubin: 29 connections

**Network Metadata Available:**
- `in_black_book`: Contact listing presence
- `is_billionaire`: Wealth indicator
- `flight_count`: Number of flights on Epstein's aircraft
- `connection_count`: Total documented relationships
- `top_connections`: List of most frequent co-passengers

### 1.4 Relationship Patterns from Biography Analysis

**Sample Biography Excerpt Analysis:**

**Patricia Cayne (6 flights, 4 connections):**
> "Patricia Cayne appears in Jeffrey Epstein's flight logs as a passenger on six documented flights, marking her as a recurring traveler on aircraft associated with Epstein... Her network statistics indicate four direct connections within the broader Epstein orbit..."

**Melinda Luntz (Black Book + 6 flights, 4 connections):**
> "Melinda Luntz is documented as a contact in Jeffrey Epstein's personal address book, commonly referred to as the 'Black Book,' which lists individuals associated with his social and professional network. Flight logs from Epstein's private aircraft further record her participation in six flights..."

**Observable Patterns:**
1. **Flight Frequency:** Ranges from 1-100+ flights
2. **Black Book Presence:** Indicates direct contact information exchange
3. **Connection Density:** 1-262 documented relationships
4. **Source Diversity:** Single source vs. multiple sources indicates depth of involvement
5. **Co-Passenger Patterns:** Repeated co-travelers suggest relationship clusters

---

## 2. Classification Taxonomy Design

### 2.1 Proposed Category Structure

**Hierarchical Multi-Label Classification:**

#### **Tier 1: Primary Role Categories**

1. **CORE_NETWORK**
   - **Definition:** Central figures with extensive documented connections (50+ connections OR Black Book + 20+ flights)
   - **Examples:** Jeffrey Epstein, Ghislaine Maxwell, Glenn Dubin, Eva Dubin
   - **Characteristics:** Multiple source types, high flight frequency, central network position
   - **Sub-categories:**
     - `core_network.primary`: The principal figure (Jeffrey Epstein)
     - `core_network.facilitator`: Key enablers and organizers (e.g., Ghislaine Maxwell)
     - `core_network.associate`: Close long-term associates

2. **BUSINESS_FINANCIAL**
   - **Definition:** Business associates, financial advisors, investors, corporate connections
   - **Characteristics:** Professional relationships, financial transactions, business dealings
   - **Sub-categories:**
     - `business.financial_advisor`: Money managers, accountants, financial planners
     - `business.investor`: Investment partners, venture capitalists
     - `business.corporate_executive`: CEOs, board members, corporate associates
     - `business.legal_financial`: Lawyers, accountants in financial capacity

3. **POLITICAL_GOVERNMENT**
   - **Definition:** Politicians, government officials, diplomats, policy advisors
   - **Characteristics:** Government positions, political influence, policy connections
   - **Sub-categories:**
     - `political.elected_official`: Elected politicians, legislators
     - `political.diplomat`: Ambassadors, diplomatic corps
     - `political.advisor`: Political consultants, policy advisors
     - `political.government_employee`: Civil servants, agency officials

4. **CELEBRITY_ENTERTAINMENT**
   - **Definition:** Actors, models, musicians, media personalities, entertainment industry
   - **Characteristics:** Public recognition, entertainment career, media presence
   - **Sub-categories:**
     - `celebrity.actor`: Film and television actors
     - `celebrity.model`: Professional models
     - `celebrity.musician`: Musicians, performers
     - `celebrity.media`: Journalists, TV personalities, producers

5. **ACADEMIC_SCIENTIFIC**
   - **Definition:** Scientists, academics, researchers, educational institution connections
   - **Characteristics:** Academic credentials, research positions, institutional affiliations
   - **Sub-categories:**
     - `academic.scientist`: Research scientists, laboratory directors
     - `academic.professor`: University professors, lecturers
     - `academic.institution_leader`: University presidents, deans, trustees

6. **PHILANTHROPIC_NONPROFIT**
   - **Definition:** Charity workers, foundation executives, nonprofit leadership
   - **Characteristics:** Nonprofit roles, charitable activities, foundation connections
   - **Sub-categories:**
     - `philanthropic.foundation_executive`: Foundation directors, trustees
     - `philanthropic.charity_worker`: Nonprofit employees, volunteers
     - `philanthropic.donor`: Major donors, philanthropists

7. **SOCIAL_ELITE**
   - **Definition:** High society, socialites, private club members, wealth-based connections
   - **Characteristics:** Social standing, private memberships, society events
   - **Sub-categories:**
     - `social.socialite`: Professional socialites, society figures
     - `social.aristocracy`: Titled nobility, royal connections
     - `social.club_member`: Exclusive club members, social organizations

8. **STAFF_EMPLOYEES**
   - **Definition:** Pilots, assistants, household staff, property managers, security
   - **Characteristics:** Employment relationship, service roles, operational support
   - **Sub-categories:**
     - `staff.pilot`: Aircraft pilots, aviation crew
     - `staff.assistant`: Personal assistants, secretaries
     - `staff.household`: Housekeepers, cooks, property staff
     - `staff.security`: Security personnel, bodyguards
     - `staff.property_manager`: Real estate managers, property administrators

9. **LEGAL_INVESTIGATIVE**
   - **Definition:** Lawyers, prosecutors, investigators, law enforcement, legal counsel
   - **Characteristics:** Legal proceedings, investigations, law enforcement roles
   - **Sub-categories:**
     - `legal.defense_attorney`: Epstein's legal defense team
     - `legal.prosecutor`: Government prosecutors, district attorneys
     - `legal.investigator`: Private investigators, journalists investigating case
     - `legal.law_enforcement`: Police, FBI, federal agents

10. **VICTIMS_SURVIVORS**
    - **Definition:** Documented victims and survivors of Epstein's crimes
    - **Characteristics:** Legal testimony, victim statements, court-identified victims
    - **Privacy Note:** Requires highest privacy protection and sensitivity
    - **Sub-categories:**
      - `victim.testified`: Publicly testified victims
      - `victim.legal_filing`: Identified in legal documents
      - `victim.anonymous`: Anonymized victim references

11. **UNKNOWN_PERIPHERAL**
    - **Definition:** Limited documented information, unclear relationship, single-source mentions
    - **Characteristics:** Low connection count (<5), single data source, no biography
    - **Sub-categories:**
      - `unknown.flight_only`: Only appears in flight logs
      - `unknown.black_book_only`: Only appears in Black Book
      - `unknown.document_mention`: Only mentioned in documents

#### **Tier 2: Relationship Strength Modifiers**

Apply as additional tags to indicate relationship intensity:

- `relationship.direct`: Direct documented relationship (Black Book listing)
- `relationship.frequent`: High frequency interaction (20+ flights or 30+ connections)
- `relationship.occasional`: Moderate interaction (5-19 flights or 10-29 connections)
- `relationship.minimal`: Limited interaction (<5 flights, <10 connections)
- `relationship.unverified`: Single source, no corroboration

#### **Tier 3: Temporal Categories**

Apply when sufficient date information available:

- `temporal.early_period`: Pre-2000 connections
- `temporal.middle_period`: 2000-2008 connections
- `temporal.late_period`: 2008-2019 connections
- `temporal.post_arrest`: Post-2019 connections (legal/investigative only)

### 2.2 Multi-Label Classification Rules

**Primary Category Assignment:**
- Each entity MUST have exactly **1 primary role category** (Tier 1)
- Choose the most prominent role based on documented evidence
- If equally balanced, prefer category with highest evidence quality

**Secondary Categories:**
- Entities MAY have **0-3 secondary role categories**
- Assign when entity clearly fulfills multiple distinct roles
- Example: A scientist who was also a foundation trustee → Primary: `ACADEMIC_SCIENTIFIC`, Secondary: `PHILANTHROPIC_NONPROFIT`

**Relationship Modifiers:**
- Each entity MUST have exactly **1 relationship strength modifier** (Tier 2)
- Automatically derived from connection count and source diversity

**Temporal Categories:**
- Assign when flight dates or document dates provide timeline evidence
- May have multiple temporal periods if association spanned years

### 2.3 Confidence Scoring System

**Confidence Score (0.0 - 1.0):**

```
Base Confidence = 0.0

+0.40  Has biography with clear role description
+0.20  Black Book listing (indicates direct relationship)
+0.15  20+ flights (indicates sustained interaction)
+0.10  Appears in multiple document types
+0.05  High connection count (30+)
+0.05  Public figure with corroborating external sources
+0.05  Specific dates/timeline available

-0.20  Single source only
-0.15  No biography available
-0.10  Contradictory information across sources
-0.10  Generic/ambiguous name (e.g., "Mike", "John")
```

**Confidence Thresholds:**
- **High Confidence (0.80-1.00):** Publish without review
- **Medium Confidence (0.60-0.79):** Flag for manual review
- **Low Confidence (0.40-0.59):** Require manual classification
- **Very Low (<0.40):** Default to UNKNOWN_PERIPHERAL

---

## 3. Grok LLM Classification Approach

### 3.1 Data Input Strategy

**What to Pass to Grok:**

```python
{
  "entity_id": "string",
  "entity_name": "string",
  "biography_text": "string (150-300 words)",  # If available
  "flight_count": number,
  "connection_count": number,
  "top_connections": [                          # Names + their categories if classified
    {"name": "Jeffrey Epstein", "category": "CORE_NETWORK"},
    {"name": "Ghislaine Maxwell", "category": "CORE_NETWORK.facilitator"}
  ],
  "in_black_book": boolean,
  "sources": ["black_book", "flight_logs", "documents"],
  "document_types": ["deposition", "court_filing", "email"],
  "is_billionaire": boolean,
  "is_public_figure": boolean,  # Derived from external validation
  "available_context": {
    "has_dates": boolean,
    "earliest_date": "YYYY-MM-DD",
    "latest_date": "YYYY-MM-DD"
  }
}
```

### 3.2 Prompt Engineering

**System Prompt:**

```
You are an expert investigative analyst specializing in network relationship classification for the Epstein Archive project. Your task is to categorize entities based on their documented role and relationship to Jeffrey Epstein's network.

Classification Rules:
1. Assign classifications based ONLY on provided evidence (biography, sources, connection data)
2. Primary category: Select the most prominent role from the taxonomy
3. Secondary categories: Include up to 3 additional roles if clearly supported by evidence
4. Confidence score: Rate your certainty (0.0-1.0) based on evidence quality and specificity
5. Reasoning: Provide a brief explanation citing specific evidence

Sensitivity Guidelines:
- VICTIMS_SURVIVORS category requires explicit legal documentation or victim testimony
- Never speculate about criminal involvement without court records
- Respect privacy for individuals with minimal documented involvement
- Distinguish between documented facts and inferred patterns

Output strict JSON format with no additional commentary.
```

**User Prompt Template:**

```
Entity: {entity_name}

Biography:
{biography_text}

Network Statistics:
- Flight count: {flight_count}
- Connection count: {connection_count}
- Top connections: {top_connections_with_categories}
- In Black Book: {in_black_book}
- Data sources: {sources}
- Document types: {document_types}

Classification Taxonomy:
[Include full taxonomy from Section 2.1]

Task:
Classify this entity into the appropriate category(ies). Return JSON:

{
  "primary_category": "CATEGORY_NAME",
  "primary_subcategory": "subcategory.name",
  "secondary_categories": ["CATEGORY_NAME_2", "CATEGORY_NAME_3"],
  "relationship_modifier": "relationship.strength",
  "temporal_categories": ["temporal.period"],
  "confidence_score": 0.85,
  "reasoning": "Brief explanation citing evidence from biography and network data",
  "evidence_highlights": [
    "Key quote or fact from biography",
    "Network pattern (e.g., '20+ flights with Maxwell')"
  ],
  "needs_manual_review": false,
  "review_reason": null
}

Important:
- Use ONLY information from provided context
- Do not infer relationships beyond documented evidence
- If insufficient information, use UNKNOWN_PERIPHERAL with low confidence
- Flag for manual review if evidence is ambiguous or sensitive
```

### 3.3 Handling Entities Without Biographies

**For entities lacking biographies (1,368 entities):**

**Modified Prompt Strategy:**

```
Entity: {entity_name}

[NO BIOGRAPHY AVAILABLE]

Network Statistics:
- Flight count: {flight_count}
- Connection count: {connection_count}
- Top connections: {top_connections_with_categories}
- In Black Book: {in_black_book}
- Data sources: {sources}

Classification Strategy:
1. If flight_count < 5 AND connection_count < 10 AND single source → UNKNOWN_PERIPHERAL
2. If in_black_book AND frequent co-traveler with STAFF entities → likely STAFF
3. If high connection_count (30+) AND billionaire → likely BUSINESS_FINANCIAL or SOCIAL_ELITE
4. If frequent co-traveler with specific category cluster → infer category from cluster

Use relationship patterns and network position to infer likely category, but:
- Confidence score MUST be ≤ 0.60 (without biography)
- ALWAYS flag needs_manual_review: true
- Provide reasoning explaining inference method
```

### 3.4 Batch Processing Strategy

**Batch Size:** 50-100 entities per batch

**Processing Order (Priority Queue):**

1. **High-Priority Tier 1:** Entities with biographies + 20+ connections (269 entities)
   - Most complete data, highest classification accuracy
   - Process first to establish baseline categories

2. **Medium-Priority Tier 2:** Entities without biographies but 10+ connections (estimated 400 entities)
   - Use network patterns and connection inference
   - Higher manual review rate expected

3. **Low-Priority Tier 3:** Entities with <10 connections (estimated 968 entities)
   - Likely UNKNOWN_PERIPHERAL
   - Batch classify with minimal LLM calls (use rule-based system)

**Rate Limiting:**
- Grok-4.1-fast free tier: No explicit rate limit (until Dec 3, 2025)
- Conservative approach: 1 request per second (3,600/hour)
- Estimated time: 1,637 entities ÷ 3,600/hour ≈ **27 minutes** (Tier 1 only)
- Full dataset: ~45 minutes with batching optimization

**Checkpoint Strategy:**
- Save results every 10 entities (matches existing bio generation pattern)
- Checkpoint file: `data/metadata/entity_classifications_checkpoint.json`
- Resume capability: Skip already-classified entities on restart

---

## 4. Data Schema Design

### 4.1 Storage Location Recommendation

**Primary Option: New JSON File**

**File:** `data/metadata/entity_classifications.json`

**Rationale:**
- Follows existing pattern (`entity_biographies.json`, `entity_statistics.json`)
- Easy version control and backup
- No database schema migration required
- Simple merge into existing API responses

**Structure:**

```json
{
  "metadata": {
    "generated": "2025-11-25T18:00:00+00:00",
    "generator": "grok-4.1-fast",
    "version": "1.0",
    "total_classified": 1637,
    "classification_date": "2025-11-25",
    "taxonomy_version": "1.0",
    "statistics": {
      "by_primary_category": {
        "CORE_NETWORK": 15,
        "BUSINESS_FINANCIAL": 120,
        "POLITICAL_GOVERNMENT": 45,
        "CELEBRITY_ENTERTAINMENT": 80,
        "ACADEMIC_SCIENTIFIC": 35,
        "PHILANTHROPIC_NONPROFIT": 25,
        "SOCIAL_ELITE": 90,
        "STAFF_EMPLOYEES": 60,
        "LEGAL_INVESTIGATIVE": 30,
        "VICTIMS_SURVIVORS": 12,
        "UNKNOWN_PERIPHERAL": 1125
      },
      "average_confidence": 0.72,
      "manual_review_flagged": 245,
      "needs_biography_enrichment": 1368
    }
  },
  "classifications": {
    "entity_id": {
      "entity_id": "glenn_dubin",
      "entity_name": "Glenn Dubin",
      "primary_category": "BUSINESS_FINANCIAL",
      "primary_subcategory": "business.investor",
      "secondary_categories": ["SOCIAL_ELITE", "PHILANTHROPIC_NONPROFIT"],
      "relationship_modifier": "relationship.frequent",
      "temporal_categories": ["temporal.middle_period", "temporal.late_period"],
      "confidence_score": 0.92,
      "classification_reasoning": "Hedge fund manager and investor with documented financial ties to Epstein. Black Book listing and 29 documented connections indicate sustained relationship. Also prominent in social elite circles and philanthropy.",
      "evidence_highlights": [
        "Hedge fund manager with direct financial relationship",
        "Black Book listing indicates direct contact",
        "29 network connections place him in frequent interaction tier"
      ],
      "classified_by": "grok-4.1-fast",
      "classification_date": "2025-11-25T18:05:23+00:00",
      "needs_manual_review": false,
      "review_reason": null,
      "manually_reviewed": false,
      "manual_override": null,
      "last_updated": "2025-11-25T18:05:23+00:00"
    }
  }
}
```

### 4.2 Alternative: Database Table Extension

**If database storage preferred:**

```sql
CREATE TABLE entity_classifications (
    entity_id TEXT PRIMARY KEY,
    primary_category TEXT NOT NULL,
    primary_subcategory TEXT,
    secondary_categories TEXT,          -- JSON array
    relationship_modifier TEXT,
    temporal_categories TEXT,            -- JSON array
    confidence_score REAL NOT NULL,
    classification_reasoning TEXT,
    evidence_highlights TEXT,            -- JSON array
    classified_by TEXT,
    classification_date TIMESTAMP,
    needs_manual_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,
    manually_reviewed BOOLEAN DEFAULT FALSE,
    manual_override TEXT,                -- JSON object with override details
    last_updated TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

CREATE INDEX idx_classifications_primary_category ON entity_classifications(primary_category);
CREATE INDEX idx_classifications_confidence ON entity_classifications(confidence_score);
CREATE INDEX idx_classifications_needs_review ON entity_classifications(needs_manual_review);
```

**Pros:**
- Normalized data structure
- Efficient querying and filtering
- Enforced referential integrity

**Cons:**
- Requires database migration
- More complex backup/restore
- Less portable than JSON

**Recommendation:** Start with JSON file, migrate to database if performance issues arise with 1,600+ classifications.

### 4.3 Metadata Fields Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | Normalized entity ID (FK to entities table) |
| `entity_name` | string | Yes | Display name for human readability |
| `primary_category` | string | Yes | Primary role category (Tier 1) |
| `primary_subcategory` | string | No | Specific subcategory within primary |
| `secondary_categories` | array | No | Additional role categories (max 3) |
| `relationship_modifier` | string | Yes | Relationship strength (Tier 2) |
| `temporal_categories` | array | No | Time periods when applicable |
| `confidence_score` | float | Yes | 0.0-1.0, algorithm or LLM certainty |
| `classification_reasoning` | string | Yes | Brief explanation of classification |
| `evidence_highlights` | array | No | Key facts supporting classification |
| `classified_by` | string | Yes | "grok-4.1-fast", "rule-based", or "manual" |
| `classification_date` | timestamp | Yes | When classification was performed |
| `needs_manual_review` | boolean | Yes | Flag for human review queue |
| `review_reason` | string | No | Why manual review needed |
| `manually_reviewed` | boolean | Yes | Has human reviewed this? |
| `manual_override` | object | No | Human corrections if any |
| `last_updated` | timestamp | Yes | Most recent modification timestamp |

### 4.4 Re-Classification Strategy

**When to Re-Classify:**

1. **New biography generated:** Entity transitions from no-bio to bio-available
   - Automatic trigger: When `entity_biographies.json` updated
   - Re-run classification with higher confidence threshold

2. **New network connections discovered:** Connection count increases significantly
   - Trigger: Connection count changes by >20%
   - Re-evaluate relationship_modifier

3. **Manual correction:** Human reviewer overrides classification
   - Store original in `manual_override.original_classification`
   - Update classification with human input
   - Set `manually_reviewed: true`

4. **Taxonomy update:** Classification system evolves
   - Version control: `taxonomy_version` field
   - Bulk re-classification job with new taxonomy
   - Maintain backward compatibility with version field

**Re-Classification Workflow:**

```python
def should_reclassify(entity_id, classification_data, entity_data):
    """Determine if entity needs re-classification"""

    # Check 1: Biography added since classification
    if entity_data.has_biography and not classification_data.used_biography:
        return True, "biography_added"

    # Check 2: Significant network growth
    old_connections = classification_data.connection_count_at_classification
    new_connections = entity_data.connection_count
    if (new_connections - old_connections) / old_connections > 0.20:
        return True, "network_growth"

    # Check 3: Low confidence original classification
    if classification_data.confidence_score < 0.60:
        return True, "low_confidence_original"

    # Check 4: Taxonomy version outdated
    if classification_data.taxonomy_version < CURRENT_TAXONOMY_VERSION:
        return True, "taxonomy_outdated"

    return False, None
```

---

## 5. API Integration Design

### 5.1 New Endpoints

**GET `/api/entities/classifications`**

Retrieve classification statistics and taxonomy information.

**Response:**
```json
{
  "taxonomy_version": "1.0",
  "total_classified": 1637,
  "classification_date": "2025-11-25",
  "categories": {
    "CORE_NETWORK": {
      "count": 15,
      "subcategories": {
        "core_network.primary": 1,
        "core_network.facilitator": 3,
        "core_network.associate": 11
      }
    },
    "BUSINESS_FINANCIAL": {
      "count": 120,
      "subcategories": {...}
    }
  },
  "relationship_modifiers": {
    "relationship.direct": 245,
    "relationship.frequent": 89,
    "relationship.occasional": 312,
    "relationship.minimal": 876,
    "relationship.unverified": 115
  },
  "confidence_distribution": {
    "high_0.80_1.00": 423,
    "medium_0.60_0.79": 589,
    "low_0.40_0.59": 412,
    "very_low_0.00_0.39": 213
  }
}
```

**GET `/api/entities/{entity_id}/classification`**

Retrieve classification for specific entity.

**Response:**
```json
{
  "entity_id": "glenn_dubin",
  "entity_name": "Glenn Dubin",
  "classification": {
    "primary_category": "BUSINESS_FINANCIAL",
    "primary_subcategory": "business.investor",
    "secondary_categories": ["SOCIAL_ELITE", "PHILANTHROPIC_NONPROFIT"],
    "relationship_modifier": "relationship.frequent",
    "temporal_categories": ["temporal.middle_period"],
    "confidence_score": 0.92,
    "classification_reasoning": "Hedge fund manager with financial ties...",
    "classified_by": "grok-4.1-fast",
    "classification_date": "2025-11-25T18:05:23+00:00",
    "manually_reviewed": false
  }
}
```

**GET `/api/entities?category={category}&confidence_min={score}`**

Filter entities by classification category and confidence threshold.

**Query Parameters:**
- `category`: Primary category to filter (e.g., "BUSINESS_FINANCIAL")
- `subcategory`: Specific subcategory (e.g., "business.investor")
- `secondary_category`: Filter by secondary category presence
- `relationship_modifier`: Filter by relationship strength
- `temporal_category`: Filter by time period
- `confidence_min`: Minimum confidence score (0.0-1.0)
- `confidence_max`: Maximum confidence score
- `needs_review`: Filter only those flagged for manual review
- `limit`: Results per page (default 50)
- `offset`: Pagination offset

**Example:**
```
GET /api/entities?category=CELEBRITY_ENTERTAINMENT&subcategory=celebrity.model&confidence_min=0.75&limit=20
```

**Response:**
```json
{
  "total": 15,
  "limit": 20,
  "offset": 0,
  "filters": {
    "category": "CELEBRITY_ENTERTAINMENT",
    "subcategory": "celebrity.model",
    "confidence_min": 0.75
  },
  "entities": [
    {
      "id": "naomi_campbell",
      "display_name": "Naomi Campbell",
      "classification": {
        "primary_category": "CELEBRITY_ENTERTAINMENT",
        "primary_subcategory": "celebrity.model",
        "confidence_score": 0.88,
        "relationship_modifier": "relationship.occasional"
      },
      "connection_count": 12,
      "flight_count": 8,
      "in_black_book": true
    },
    ...
  ]
}
```

### 5.2 Enhancing Existing Endpoints

**Modify `/api/entities` and `/api/entities/{id}` responses:**

Add `classification` field to entity objects:

```json
{
  "id": "glenn_dubin",
  "display_name": "Glenn Dubin",
  "entity_type": "person",
  "guid": "abc-123-def",
  "connection_count": 29,
  "flight_count": 15,
  "in_black_book": true,
  "classification": {
    "primary_category": "BUSINESS_FINANCIAL",
    "primary_subcategory": "business.investor",
    "secondary_categories": ["SOCIAL_ELITE"],
    "relationship_modifier": "relationship.frequent",
    "confidence_score": 0.92
  }
}
```

**Frontend Impact:**
- Entity cards can display category badges
- Filter panel gains category filters
- Network graph can color-code nodes by category
- Entity detail pages show classification reasoning

### 5.3 Admin/Review Endpoints

**GET `/api/admin/classifications/review-queue`**

Retrieve entities flagged for manual review.

**Response:**
```json
{
  "total_flagged": 245,
  "review_queue": [
    {
      "entity_id": "john_doe",
      "entity_name": "John Doe",
      "classification": {...},
      "review_reason": "Low confidence (0.58) - insufficient biography",
      "flagged_date": "2025-11-25T18:00:00+00:00"
    }
  ]
}
```

**POST `/api/admin/classifications/{entity_id}/review`**

Submit manual review and override classification.

**Request Body:**
```json
{
  "reviewer": "admin_user_id",
  "approved": false,
  "override_classification": {
    "primary_category": "STAFF_EMPLOYEES",
    "primary_subcategory": "staff.pilot",
    "reasoning": "Manual research identified as pilot based on aviation records"
  }
}
```

---

## 6. Implementation Strategy

### 6.1 Phase 1: Taxonomy and Schema Setup (Week 1)

**Tasks:**
1. **Finalize taxonomy** (2 days)
   - Review proposed categories with stakeholders
   - Adjust based on feedback
   - Document category definitions in `docs/ENTITY_CLASSIFICATION_TAXONOMY.md`

2. **Create data schema** (1 day)
   - Implement `entity_classifications.json` structure
   - Set up checkpoint mechanism
   - Create backup strategy

3. **Build classification script** (2 days)
   - Extend `scripts/analysis/classify_entity_relationships.py` (new file)
   - Implement Grok API integration (reuse `generate_entity_bios_grok.py` patterns)
   - Add confidence scoring algorithm
   - Implement checkpoint/resume logic

### 6.2 Phase 2: Initial Classification Run (Week 2)

**Priority 1: High-Value Entities (269 with biographies)**

```bash
# Dry run test with 10 entities
python3 scripts/analysis/classify_entity_relationships.py \
  --dry-run \
  --limit 10

# Full Tier 1 classification (entities with biographies)
python3 scripts/analysis/classify_entity_relationships.py \
  --tier 1 \
  --limit 269 \
  --output data/metadata/entity_classifications.json \
  --checkpoint-every 10
```

**Expected Results:**
- Runtime: ~15 minutes (269 entities @ 1 req/sec)
- Success rate: 95%+ (based on bio generation success rate)
- Manual review flagged: ~30-50 entities (ambiguous cases)

**Priority 2: Medium-Value Entities (400 without bios, 10+ connections)**

```bash
python3 scripts/analysis/classify_entity_relationships.py \
  --tier 2 \
  --min-connections 10 \
  --limit 400 \
  --output data/metadata/entity_classifications.json \
  --merge
```

**Expected Results:**
- Runtime: ~20 minutes
- Success rate: 70-80% (network inference less certain)
- Manual review flagged: ~120-150 entities (low confidence)

**Priority 3: Low-Value Entities (968 with <10 connections)**

**Rule-Based Classification:**
For entities with minimal data, use algorithmic classification:

```python
def rule_based_classification(entity_data):
    """Fast classification for low-data entities"""

    if entity_data.flight_count < 5 and entity_data.connection_count < 10:
        return {
            "primary_category": "UNKNOWN_PERIPHERAL",
            "primary_subcategory": determine_subcategory(entity_data),
            "confidence_score": 0.30,
            "classified_by": "rule-based",
            "needs_manual_review": False
        }
```

**Expected Results:**
- Runtime: ~2 minutes (rule-based, no API calls)
- Classification: 90%+ to UNKNOWN_PERIPHERAL
- Manual review: Only flagged if name matches known public figure

### 6.3 Phase 3: Manual Review Process (Week 3)

**Review Workflow:**

1. **Generate review queue** (245 entities flagged)
   ```bash
   python3 scripts/analysis/export_classification_review_queue.py \
     --output data/metadata/classification_review_queue.csv
   ```

2. **Manual review spreadsheet:**
   - Columns: Entity Name, Current Classification, Confidence, Evidence, Proposed Override
   - Distribute to 2-3 reviewers
   - Review criteria: evidence quality, category fit, sensitivity

3. **Apply manual overrides:**
   ```bash
   python3 scripts/analysis/apply_classification_overrides.py \
     --input data/metadata/classification_review_overrides.csv \
     --output data/metadata/entity_classifications.json
   ```

4. **Quality assurance:**
   - Spot-check 50 random classifications across confidence levels
   - Verify VICTIMS_SURVIVORS category accuracy (critical)
   - Check for systematic errors (e.g., all pilots miscategorized)

### 6.4 Phase 4: API Integration (Week 4)

**Backend Changes:**

1. **Add classification loading to entity service:**
   ```python
   # server/services/entity_service.py

   def load_classifications():
       """Load entity classifications from JSON"""
       with open('data/metadata/entity_classifications.json') as f:
           return json.load(f)

   def get_entity_with_classification(entity_id):
       """Merge entity data with classification"""
       entity = get_entity(entity_id)
       classifications = load_classifications()
       entity['classification'] = classifications['classifications'].get(entity_id)
       return entity
   ```

2. **Implement new endpoints:**
   - `/api/entities/classifications` (taxonomy stats)
   - `/api/entities/{id}/classification` (specific classification)
   - Filter support in `/api/entities?category=X`

3. **Add classification filters to search:**
   - Extend search index with category fields
   - Support multi-category filtering
   - Confidence-based filtering

**Frontend Changes:**

1. **Entity card enhancements:**
   - Display category badge (color-coded by category)
   - Show confidence indicator (high/medium/low)
   - Tooltip with classification reasoning

2. **Filter panel additions:**
   - Category dropdown (multi-select)
   - Relationship strength filter
   - Confidence slider

3. **Network graph visualization:**
   - Color nodes by primary category
   - Legend showing category colors
   - Filter graph by category

4. **Entity detail page:**
   - Classification section with full details
   - Evidence highlights display
   - Manual review status indicator

---

## 7. Quality Assurance Approach

### 7.1 Validation Metrics

**Classification Quality Metrics:**

1. **Coverage:**
   - Classified entities / Total entities
   - Target: 100% (even if UNKNOWN_PERIPHERAL)

2. **Confidence Distribution:**
   - High confidence (0.80+): Target 30%+
   - Medium confidence (0.60-0.79): Target 40%+
   - Low confidence (<0.60): Acceptable 30%

3. **Manual Review Rate:**
   - Entities flagged / Total classified
   - Target: <20% flagged for review

4. **Category Distribution:**
   - No single category should exceed 70% (except UNKNOWN_PERIPHERAL)
   - All categories should have >0 entities (except possibly VICTIMS_SURVIVORS)

5. **Consistency:**
   - Similar entities (same flight patterns, connections) should have similar categories
   - Measure via clustering analysis

### 7.2 Validation Tests

**Automated Validation:**

```python
def validate_classifications(classifications_file):
    """Run validation checks on classifications"""

    with open(classifications_file) as f:
        data = json.load(f)

    issues = []

    # Test 1: All entities classified
    total_entities = get_total_entity_count()
    classified = len(data['classifications'])
    if classified < total_entities:
        issues.append(f"Missing {total_entities - classified} classifications")

    # Test 2: Valid category values
    valid_categories = get_valid_categories()
    for entity_id, classification in data['classifications'].items():
        if classification['primary_category'] not in valid_categories:
            issues.append(f"{entity_id}: Invalid category {classification['primary_category']}")

    # Test 3: Confidence scores in range
    for entity_id, classification in data['classifications'].items():
        score = classification['confidence_score']
        if not (0.0 <= score <= 1.0):
            issues.append(f"{entity_id}: Invalid confidence score {score}")

    # Test 4: High-connection entities not in UNKNOWN_PERIPHERAL
    for entity_id, classification in data['classifications'].items():
        entity_data = get_entity_data(entity_id)
        if entity_data['connection_count'] > 30:
            if classification['primary_category'] == 'UNKNOWN_PERIPHERAL':
                issues.append(f"{entity_id}: High connections ({entity_data['connection_count']}) but classified as UNKNOWN")

    # Test 5: Black Book entities have high confidence
    for entity_id, classification in data['classifications'].items():
        entity_data = get_entity_data(entity_id)
        if entity_data['in_black_book'] and classification['confidence_score'] < 0.60:
            issues.append(f"{entity_id}: Black Book entity but low confidence {classification['confidence_score']}")

    return issues
```

**Run validation:**
```bash
python3 scripts/analysis/validate_classifications.py \
  --input data/metadata/entity_classifications.json \
  --output data/metadata/classification_validation_report.json
```

### 7.3 Sample Review Process

**Manual Review Sample:**

1. **Stratified sampling:**
   - 10 entities from each primary category
   - 10 high-confidence (0.90+)
   - 10 medium-confidence (0.60-0.79)
   - 10 low-confidence (<0.60)
   - Total: ~120 entities for spot-check

2. **Review criteria:**
   - Does classification match evidence?
   - Is confidence score appropriate?
   - Are secondary categories justified?
   - Is reasoning clear and accurate?

3. **Inter-rater reliability:**
   - 3 independent reviewers
   - Measure agreement (Cohen's kappa)
   - Target: >0.70 agreement

### 7.4 Error Correction Workflow

**When errors detected:**

1. **Document error pattern:**
   ```json
   {
     "error_type": "misclassification",
     "pattern": "Scientists miscategorized as BUSINESS_FINANCIAL",
     "affected_entities": 15,
     "root_cause": "Prompt emphasized financial connections over academic credentials"
   }
   ```

2. **Fix prompt or logic:**
   - Update system prompt to clarify category priority
   - Adjust confidence scoring algorithm
   - Add validation rule to catch pattern

3. **Re-classify affected entities:**
   ```bash
   python3 scripts/analysis/reclassify_entities.py \
     --entity-list affected_entities.csv \
     --reason "Prompt improvement for academic classification"
   ```

4. **Validate fix:**
   - Re-run validation tests
   - Spot-check corrected entities
   - Update documentation

---

## 8. Cost and Timeline Estimates

### 8.1 API Cost Analysis

**Grok-4.1-fast Pricing (post-December 3, 2025):**
- Input: $0.20 per 1M tokens
- Output: $0.50 per 1M tokens

**Token Estimation per Entity:**
- System prompt: ~800 tokens
- User prompt (with biography): ~500 tokens
- User prompt (without biography): ~200 tokens
- Expected output: ~300 tokens
- **Average per classification:** ~1,600 tokens (with bio), ~1,300 tokens (without bio)

**Total Token Usage:**
- 269 entities with bios: 269 × 1,600 = 430,400 tokens
- 1,368 entities without bios: 1,368 × 1,300 = 1,778,400 tokens
- **Total:** ~2.2M tokens

**Cost Calculation:**
- Input tokens (70%): 1.54M × $0.20/1M = $0.31
- Output tokens (30%): 0.66M × $0.50/1M = $0.33
- **Total estimated cost:** $0.64

**Currently FREE until December 3, 2025**

### 8.2 Development Timeline

| Phase | Tasks | Duration | Resources |
|-------|-------|----------|-----------|
| **Phase 1: Setup** | Taxonomy finalization, schema design, script development | 1 week | 1 developer |
| **Phase 2: Classification** | Run initial classification (all 3 tiers) | 3 days | Automated (API calls) |
| **Phase 3: Review** | Manual review of 245 flagged entities | 1 week | 2-3 reviewers |
| **Phase 4: API Integration** | Backend endpoints, frontend UI updates | 1 week | 1 developer |
| **Phase 5: Testing** | Validation, QA, bug fixes | 3 days | 1 developer + 1 QA |
| **Total** | | **~4 weeks** | 1-2 developers + reviewers |

### 8.3 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Grok API changes/pricing | Medium | High | Complete before Dec 3, 2025; fallback to manual classification |
| Low classification accuracy | Low | Medium | Extensive testing with sample set first; confidence thresholds |
| High manual review volume | Medium | Medium | Rule-based classification for low-data entities reduces LLM load |
| Privacy concerns (VICTIMS) | Low | High | Strict criteria for VICTIMS category; legal review required |
| Category taxonomy disputes | Medium | Low | Stakeholder review before implementation; version control for taxonomy |
| API rate limiting | Low | Low | Conservative 1 req/sec; checkpoint system allows resume |

---

## 9. Success Criteria

### 9.1 Launch Criteria

**Must Have:**
- [x] All 1,637 entities classified (even if UNKNOWN_PERIPHERAL)
- [x] Confidence score for every classification
- [x] Validation tests passing (95%+ pass rate)
- [x] API endpoints functional
- [x] Frontend category filters working
- [x] Manual review process documented

**Should Have:**
- [x] 70%+ classifications with confidence >0.60
- [x] <20% flagged for manual review
- [x] Inter-rater reliability >0.70 in sample review
- [x] Category distribution balanced (no single category >70% except UNKNOWN)

**Nice to Have:**
- [ ] Network graph color-coded by category
- [ ] Category-based statistics dashboard
- [ ] Temporal analysis by category
- [ ] External validation against known public figures

### 9.2 Post-Launch Metrics

**Monitor for 2 weeks post-launch:**

1. **User Engagement:**
   - Category filter usage rate
   - Most-filtered categories
   - Average categories per search query

2. **Data Quality:**
   - User-reported misclassifications
   - Manual override frequency
   - Confidence score correlation with user acceptance

3. **System Performance:**
   - API response time with classification filters
   - Frontend rendering performance with category badges
   - Database query performance (if migrated from JSON)

4. **Continuous Improvement:**
   - Re-classification rate (entities updated with new bios)
   - Taxonomy evolution needs
   - New category proposals from users

---

## 10. Recommendations

### 10.1 Implementation Priorities

**MUST DO (Critical Path):**

1. **Finalize taxonomy with stakeholder review** (2 days)
   - Get legal review for VICTIMS_SURVIVORS category criteria
   - Ensure category definitions are clear and non-overlapping

2. **Implement classification script** (3 days)
   - Reuse existing Grok API infrastructure
   - Add confidence scoring algorithm
   - Implement checkpoint/resume

3. **Run classification on Tier 1 (269 entities with bios)** (1 day)
   - Validate with sample review before full run
   - Monitor for systematic errors

4. **Manual review process** (5 days)
   - Review 245 flagged entities
   - Document common edge cases
   - Create override procedures

5. **API integration** (5 days)
   - Backend endpoints
   - Frontend filters and badges
   - Testing and QA

**SHOULD DO (High Value):**

1. **Rule-based classification for Tier 3** (1 day)
   - Fast algorithmic classification for low-data entities
   - Reduces API costs and review burden

2. **Validation test suite** (2 days)
   - Automated quality checks
   - Prevent systematic errors

3. **Category color scheme** (1 day)
   - Consistent UI/UX across frontend
   - Network graph visualization

**NICE TO HAVE (Future Enhancement):**

1. **External entity validation** (ongoing)
   - Cross-reference with Wikipedia, public databases
   - Auto-flag mismatches for review

2. **Temporal analysis dashboard** (1 week)
   - Category composition over time
   - Relationship evolution visualization

3. **Advanced network clustering** (2 weeks)
   - Identify category-based sub-networks
   - Detect hidden relationship patterns

### 10.2 Next Steps (Immediate Actions)

**Week 1 (Starting 2025-11-26):**

1. **Day 1-2:** Stakeholder review of taxonomy
   - Schedule meeting with legal, editorial, technical leads
   - Finalize category definitions
   - Get approval for VICTIMS_SURVIVORS criteria

2. **Day 3-5:** Implement classification script
   - Create `scripts/analysis/classify_entity_relationships.py`
   - Extend Grok API integration
   - Add confidence scoring
   - Write unit tests

**Week 2:**

3. **Day 6:** Dry run testing (10-20 entities)
   - Validate prompt effectiveness
   - Check confidence score distribution
   - Verify JSON schema correctness

4. **Day 7-8:** Full Tier 1 classification (269 entities)
   - Run batch classification with checkpoints
   - Monitor for errors
   - Initial quality review

5. **Day 9-10:** Tier 2 & 3 classification
   - Network inference for no-bio entities
   - Rule-based for minimal-data entities
   - Complete all 1,637 entities

**Week 3:**

6. **Day 11-15:** Manual review sprint
   - Distribute review queue to 2-3 reviewers
   - Daily sync on progress and edge cases
   - Apply overrides and corrections

**Week 4:**

7. **Day 16-20:** API integration and testing
   - Backend endpoints
   - Frontend UI updates
   - QA and bug fixes

8. **Day 21:** Launch
   - Deploy to production
   - Monitor metrics
   - User documentation

### 10.3 Long-Term Considerations

**Taxonomy Evolution:**
- Plan for taxonomy v2.0 after 6 months of usage
- Incorporate user feedback and edge cases discovered
- Consider adding new categories based on data growth

**Re-Classification Schedule:**
- Quarterly review of UNKNOWN_PERIPHERAL entities
- Re-classify when new biographies generated
- Update when significant network changes detected

**Quality Maintenance:**
- Monthly spot-checks (50 random entities)
- Annual comprehensive review
- User feedback integration process

**Scaling Considerations:**
- If entity count grows to 5,000+, migrate to database
- Consider caching classification data in Redis
- Implement lazy loading for frontend category filters

---

## Appendix A: Sample Classification Scenarios

### Scenario 1: High-Confidence Business Associate

**Input Data:**
```json
{
  "entity_id": "glenn_dubin",
  "entity_name": "Glenn Dubin",
  "biography_text": "Glenn Dubin is a hedge fund manager and co-founder of Highbridge Capital Management. He maintained a long-standing financial relationship with Jeffrey Epstein, serving as both an investor and personal friend. Dubin and his wife Eva were frequent passengers on Epstein's private aircraft, appearing in flight logs over 20 times between 2000-2007...",
  "flight_count": 23,
  "connection_count": 29,
  "in_black_book": true,
  "is_billionaire": true,
  "sources": ["black_book", "flight_logs", "documents"]
}
```

**Expected Classification:**
```json
{
  "primary_category": "BUSINESS_FINANCIAL",
  "primary_subcategory": "business.investor",
  "secondary_categories": ["SOCIAL_ELITE", "PHILANTHROPIC_NONPROFIT"],
  "relationship_modifier": "relationship.frequent",
  "temporal_categories": ["temporal.middle_period", "temporal.late_period"],
  "confidence_score": 0.92,
  "reasoning": "Hedge fund manager with documented financial relationship to Epstein. Black Book listing + 23 flights + 29 connections indicate sustained, high-frequency interaction. Also prominent in philanthropic circles and social elite.",
  "needs_manual_review": false
}
```

### Scenario 2: Medium-Confidence Peripheral Figure

**Input Data:**
```json
{
  "entity_id": "patricia_cayne",
  "entity_name": "Patricia Cayne",
  "biography_text": "Patricia Cayne appears in Jeffrey Epstein's flight logs as a passenger on six documented flights. No specific co-passengers or dates available. Limited network connections (4 total). No mentions in other documents.",
  "flight_count": 6,
  "connection_count": 4,
  "in_black_book": false,
  "sources": ["flight_logs"]
}
```

**Expected Classification:**
```json
{
  "primary_category": "UNKNOWN_PERIPHERAL",
  "primary_subcategory": "unknown.flight_only",
  "secondary_categories": [],
  "relationship_modifier": "relationship.occasional",
  "temporal_categories": [],
  "confidence_score": 0.58,
  "reasoning": "Limited data: 6 flights with no Black Book listing or document mentions. Single data source (flight logs only). Insufficient information to determine specific role or relationship type. Moderate flight count suggests more than one-off contact but unclear professional/social context.",
  "needs_manual_review": true,
  "review_reason": "Low confidence (0.58) - single data source, no biography details"
}
```

### Scenario 3: Staff Member (Network Inference)

**Input Data:**
```json
{
  "entity_id": "larry_visoski",
  "entity_name": "Larry Visoski",
  "biography_text": null,  // No biography available
  "flight_count": 142,
  "connection_count": 85,
  "in_black_book": false,
  "top_connections": [
    {"name": "Jeffrey Epstein", "category": "CORE_NETWORK"},
    {"name": "Ghislaine Maxwell", "category": "CORE_NETWORK"},
    {"name": "David Rodgers", "category": "STAFF_EMPLOYEES.pilot"}  // Another pilot
  ],
  "sources": ["flight_logs"]
}
```

**Expected Classification:**
```json
{
  "primary_category": "STAFF_EMPLOYEES",
  "primary_subcategory": "staff.pilot",
  "secondary_categories": [],
  "relationship_modifier": "relationship.frequent",
  "temporal_categories": [],
  "confidence_score": 0.72,
  "reasoning": "Very high flight count (142) with consistent co-passenger pattern matching known pilots. Network position suggests operational role rather than social relationship. Frequent co-traveler with core network figures consistent with pilot role.",
  "needs_manual_review": true,
  "review_reason": "No biography available - classification based on network inference"
}
```

---

## Appendix B: Implementation Code Samples

### Sample Classification Script Structure

```python
#!/usr/bin/env python3
"""
Entity Relationship Classification System
Classifies entities based on role and relationship to Epstein network.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime, timezone

class EntityClassifier:
    """Classifies entities using Grok-4.1-fast LLM"""

    def __init__(self, api_key: str, taxonomy_file: Path):
        self.api_key = api_key
        self.taxonomy = self._load_taxonomy(taxonomy_file)
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "x-ai/grok-4.1-fast:free"

    def classify_entity(self, entity_data: Dict) -> Dict:
        """Classify single entity"""

        # Build prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(entity_data)

        # Call Grok API
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 600
            }
        )

        response.raise_for_status()
        result = response.json()

        # Parse JSON response
        classification = json.loads(result["choices"][0]["message"]["content"])

        # Add metadata
        classification["classified_by"] = "grok-4.1-fast"
        classification["classification_date"] = datetime.now(timezone.utc).isoformat()

        return classification

    def calculate_confidence_score(self, entity_data: Dict, classification: Dict) -> float:
        """Calculate confidence score based on data quality"""

        score = 0.0

        # Biography presence
        if entity_data.get("biography_text"):
            score += 0.40

        # Black Book listing
        if entity_data.get("in_black_book"):
            score += 0.20

        # High flight count
        if entity_data.get("flight_count", 0) >= 20:
            score += 0.15

        # Multiple sources
        if len(entity_data.get("sources", [])) > 1:
            score += 0.10

        # High connection count
        if entity_data.get("connection_count", 0) >= 30:
            score += 0.05

        # Public figure (external validation)
        if entity_data.get("is_public_figure"):
            score += 0.05

        # Date information available
        if entity_data.get("has_dates"):
            score += 0.05

        # Penalties
        if len(entity_data.get("sources", [])) == 1:
            score -= 0.20

        if not entity_data.get("biography_text"):
            score -= 0.15

        return max(0.0, min(1.0, score))

# ... (rest of implementation)
```

---

## Appendix C: Taxonomy JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Entity Classification Taxonomy",
  "version": "1.0",
  "categories": {
    "CORE_NETWORK": {
      "description": "Central figures with extensive documented connections",
      "min_connections": 50,
      "subcategories": {
        "primary": "Principal figure (Jeffrey Epstein)",
        "facilitator": "Key enablers and organizers",
        "associate": "Close long-term associates"
      }
    },
    "BUSINESS_FINANCIAL": {
      "description": "Business associates, financial advisors, investors",
      "subcategories": {
        "financial_advisor": "Money managers, accountants",
        "investor": "Investment partners, VCs",
        "corporate_executive": "CEOs, board members",
        "legal_financial": "Lawyers in financial capacity"
      }
    },
    // ... (other categories)
  },
  "relationship_modifiers": {
    "direct": "Black Book listing or direct documented relationship",
    "frequent": "20+ flights or 30+ connections",
    "occasional": "5-19 flights or 10-29 connections",
    "minimal": "<5 flights, <10 connections",
    "unverified": "Single source, no corroboration"
  },
  "confidence_thresholds": {
    "high": 0.80,
    "medium": 0.60,
    "low": 0.40
  }
}
```

---

**END OF RESEARCH REPORT**

**Next Action:** Proceed with Phase 1 (Taxonomy Finalization and Script Development)

**Contact:** For questions or clarifications, refer to this document as the authoritative specification for the Entity Classification System.
