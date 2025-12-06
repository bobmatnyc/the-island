# Entity Classification Taxonomy

**Version:** 2.0.0
**Last Updated:** 2025-12-06
**Issue:** #20 - Classifications: Define complete taxonomy

## Overview

This document defines the complete classification taxonomy for entities in the Epstein network archive. The taxonomy provides a standardized system for categorizing people, organizations, and locations based on their relationship to the Epstein case, their roles, legal status, and other characteristics.

## Table of Contents

1. [Classification Categories](#classification-categories)
2. [Classification Types](#classification-types)
3. [Classification Rules](#classification-rules)
4. [Multi-Classification Support](#multi-classification-support)
5. [Confidence Levels](#confidence-levels)
6. [Usage Guidelines](#usage-guidelines)
7. [Implementation Notes](#implementation-notes)

## Classification Categories

The taxonomy is organized into five main categories:

### 1. Relationship
Classifications based on relationship to Jeffrey Epstein and his network.

### 2. Role
Classifications based on professional or functional role.

### 3. Entity Characteristics
Additional characteristics and attributes of entities.

### 4. Legal Status
Classifications based on legal proceedings and status.

### 5. Location Type
Classifications for location entities.

### 6. Organization Type
Classifications for organization entities.

## Classification Types

### Relationship to Epstein

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `victims` | Victims | Individuals identified as victims of trafficking or abuse | 1 (highest) | person |
| `co_conspirators` | Co-Conspirators | Individuals charged or implicated as co-conspirators | 2 | person |
| `frequent_travelers` | Frequent Travelers | Multiple documented flights on Epstein's aircraft | 3 | person |
| `social_contacts` | Social Contacts | In Epstein's personal contact book or social circle | 4 | person |
| `associates` | Associates | Business or professional associates of Epstein | 5 | person, organization |
| `peripheral` | Peripheral | Minimal documented connections | 9 (lowest) | person, location, organization |

### Professional Roles

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `employees` | Employees | Staff, pilots, assistants, and other employees | 5 | person |
| `legal_professionals` | Legal Professionals | Attorneys, prosecutors, defense counsel, and legal staff | 6 | person |
| `investigators` | Investigators | Law enforcement, FBI, investigators, and prosecutors | 7 | person |
| `public_figures` | Public Figures | Politicians, celebrities, and other prominent individuals | 8 | person |
| `media` | Media | Journalists, reporters, and media organizations | 8 | person, organization |
| `financial` | Financial | Financial institutions, banks, and investment firms | 6 | organization |
| `family` | Family | Family members of Jeffrey Epstein or other key figures | 4 | person |

### Entity Characteristics

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `political` | Political Connections | Significant political connections or roles | 7 | person, organization |
| `celebrity` | Celebrity | High-profile celebrities, entertainers, or public personalities | 7 | person |
| `academic` | Academic | Academic professionals, researchers, or scholars | 7 | person, organization |
| `medical` | Medical | Medical professionals or healthcare organizations | 7 | person, organization |
| `royalty` | Royalty | Members of royal families or nobility | 6 | person |

### Legal Status

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `plaintiffs` | Plaintiffs | Individuals filing lawsuits or civil claims | 2 | person |
| `defendants` | Defendants | Named as defendants in legal proceedings | 2 | person, organization |
| `witnesses` | Witnesses | Providing testimony or depositions | 4 | person |

### Location Classifications

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `properties` | Properties | Real estate owned or controlled by Epstein | 1 | location |
| `travel_destinations` | Travel Destinations | Locations frequently visited via private aircraft | 3 | location |
| `mentioned_locations` | Mentioned Locations | Locations referenced in documents or testimony | 8 | location |

### Organization Classifications

| Type | Label | Description | Priority | Applies To |
|------|-------|-------------|----------|------------|
| `epstein_entities` | Epstein Entities | Companies, foundations, and entities controlled by Epstein | 1 | organization |
| `government_agencies` | Government Agencies | Government departments, law enforcement, regulatory bodies | 3 | organization |
| `law_firms` | Law Firms | Legal firms involved in Epstein-related cases | 5 | organization |
| `educational_institutions` | Educational Institutions | Universities, schools, and academic organizations | 7 | organization |

## Classification Rules

Classification rules define how entities are automatically classified during document ingestion. See `data/schemas/classification_rules.json` for complete details.

### Rule Components

Each classification has:

1. **Keywords**: Primary terms that indicate classification
2. **Context Keywords**: Terms that provide supporting context
3. **Evidence Types**: Document types and their reliability scores
4. **Confidence Thresholds**: Minimum scores for high/medium/low confidence
5. **Exclusions**: Terms that prevent classification
6. **Multi-classification**: Whether this can be combined with others

### Classification Strategies

Classification uses four complementary strategies:

1. **Keyword Matching (40% weight)**: Match entity mentions against keyword lists
2. **Evidence-Based (35% weight)**: Score based on document type and source quality
3. **Frequency Analysis (15% weight)**: Consider frequency of mentions and co-occurrences
4. **Hierarchical Inference (10% weight)**: Infer from related entities

### Evidence Quality Scores

Different document types have different reliability scores:

- **Court filings**: 1.0 (highest reliability)
- **Depositions**: 0.95
- **Legal documents**: 0.90-0.95
- **Flight logs**: 0.50-0.95 (varies by classification)
- **Black book entries**: 0.80
- **News reports**: 0.25-0.40 (lowest reliability)

## Multi-Classification Support

Entities can have multiple classifications that reflect real-world complexity.

### Allowed Combinations

Common valid multi-classifications:

- `victims` + `plaintiffs` + `witnesses`
- `associates` + `employees` + `frequent_travelers`
- `public_figures` + `social_contacts` + `associates`
- `legal_professionals` + `witnesses`
- `co_conspirators` + `defendants` + `associates`
- `employees` + `witnesses`

### Conflicting Classifications

These combinations are logically inconsistent and should not occur:

- `victims` + `co_conspirators` (victim and perpetrator)
- `legal_professionals` + `defendants` (representing vs. being represented)
- `investigators` + `defendants` (investigating vs. being investigated)

### Priority Display

When multiple classifications apply:

1. Display all applicable classifications
2. Sort by priority field (1 = highest priority)
3. Show highest priority classification prominently in UI
4. Allow expansion to see all classifications

## Confidence Levels

### High Confidence (0.85-1.0)

- **Definition**: Classification supported by multiple primary sources
- **Minimum Sources**: 3+
- **Examples**:
  - Documented in court filings
  - Multiple flight log entries
  - Named in depositions
  - Official legal documents

### Medium Confidence (0.60-0.84)

- **Definition**: Classification supported by secondary sources or single primary source
- **Minimum Sources**: 1-2
- **Examples**:
  - Single mention in document
  - Black book entry
  - News article reference
  - Single flight log entry

### Low Confidence (0.30-0.59)

- **Definition**: Classification inferred from context or minimal evidence
- **Minimum Sources**: 0-1
- **Examples**:
  - Peripheral mention
  - Indirect association
  - Inferred relationship
  - Context-based classification

### Confidence Calculation

```
confidence = weighted_sum(strategy_scores) × evidence_quality × source_count_factor

Where:
- strategy_scores: Results from each classification strategy (weighted)
- evidence_quality: Based on document type (primary=1.0, secondary=0.7, tertiary=0.4)
- source_count_factor: 1 source=0.7, 2=0.85, 3=0.95, 4+=1.0
```

## Usage Guidelines

### For Document Ingestion

1. **Apply Rules Automatically**: Use keyword matching and evidence scoring during ingestion
2. **Set Initial Confidence**: Calculate confidence based on available evidence
3. **Flag for Review**: Low confidence classifications should be reviewed manually
4. **Update Continuously**: Recalculate confidence as new evidence is added

### For Manual Classification

1. **Check Existing**: Review existing classifications before adding new ones
2. **Verify Evidence**: Ensure classification is supported by source documents
3. **Assign Confidence**: Use guidelines above to determine appropriate confidence level
4. **Document Sources**: Always link to specific source documents
5. **Consider Multi-classification**: Apply all relevant classifications, not just one

### For UI Display

1. **Show Primary**: Display highest priority classification prominently
2. **Expandable Details**: Allow users to see all classifications
3. **Visual Hierarchy**: Use priority to determine visual prominence
4. **Color Coding**: Use schema-defined colors consistently
5. **Confidence Indicators**: Show confidence level visually (high/medium/low)

### For Data Analysis

1. **Filter by Confidence**: Allow filtering by confidence thresholds
2. **Combine Classifications**: Support queries across multiple classification types
3. **Track Changes**: Log classification updates for audit trail
4. **Evidence Links**: Maintain links to source documents

## Implementation Notes

### Database Schema

Classifications should be stored with:

```json
{
  "entity_id": "uuid",
  "classification_type": "string (from taxonomy)",
  "confidence_score": "float (0.0-1.0)",
  "evidence_sources": ["array of source document references"],
  "assigned_date": "ISO 8601 timestamp",
  "assigned_by": "user or system identifier",
  "review_status": "pending|approved|rejected",
  "notes": "free text explanation"
}
```

### API Endpoints

Recommended API structure:

- `GET /entities/{id}/classifications` - Get all classifications for entity
- `POST /entities/{id}/classifications` - Add new classification
- `PUT /classifications/{id}` - Update classification confidence or status
- `DELETE /classifications/{id}` - Remove classification
- `GET /classifications/types` - Get taxonomy schema
- `GET /classifications/rules` - Get classification rules

### Validation Rules

1. **Type Validation**: Classification type must exist in taxonomy
2. **Entity Type Match**: Classification must apply to entity type (person/org/location)
3. **Confidence Range**: Score must be between 0.0 and 1.0
4. **Evidence Required**: High confidence requires minimum 3 sources
5. **Conflict Check**: Validate against conflicting classification rules

### Future Enhancements

Potential improvements to taxonomy:

1. **Machine Learning**: Train models on manual classifications
2. **Temporal Analysis**: Track classification changes over time
3. **Relationship Inference**: Derive classifications from network analysis
4. **Confidence Decay**: Lower confidence for old, unsupported classifications
5. **Crowd-sourced Review**: Allow community review and validation

## References

- **Schema**: `data/schemas/entity_classifications.json`
- **Rules**: `data/schemas/classification_rules.json`
- **Issue**: Linear #20 - Classifications: Define complete taxonomy

## Changelog

### Version 2.0.0 (2025-12-06)

- Added complete classification rules system
- Expanded entity characteristics category
- Added family relationship classification
- Added royalty characteristic classification
- Defined multi-classification rules and conflicts
- Specified confidence calculation formulas
- Added keyword lists for automatic classification
- Defined evidence quality scoring system
- Added implementation guidelines and best practices

### Version 1.0.0 (2025-12-06)

- Initial taxonomy with basic classifications
- Core categories: relationship, role, legal_status, location_type, organization_type
- Basic confidence level definitions
