# Entity Research Tools

This directory contains tools and workflows for enriching entity data with biographical information and Epstein relationship details, maintaining full source provenance.

## Quick Start

### Research a Single Entity

```bash
cd /Users/masa/Projects/Epstein

# Use web search to research entity
# Then manually add to enriched_entity_data.json following the schema

# View current progress
python3 -c "
import json
with open('data/metadata/enriched_entity_data.json', 'r') as f:
    data = json.load(f)
print(f'Entities researched: {len(data[\"entities\"])}')
for e in data['entities']:
    print(f'  - {e[\"name\"]}')
"
```

### View Priority List

```bash
python3 -c "
import json
with open('data/metadata/priority_entities_for_research.json', 'r') as f:
    data = json.load(f)
print(f'Total priority entities: {len(data[\"entities\"])}')
print('\nTop 20:')
for i, e in enumerate(data['entities'][:20], 1):
    print(f'{i:2}. {e[\"name\"]:30} - {e[\"flights\"]:3} flights')
"
```

## Files in This Directory

### `entity_data_schema.json`
**Purpose**: Template and guidelines for entity enrichment
**Contains**:
- Complete data structure template
- Source reliability tier definitions (1-5)
- Ethical guidelines (what to include/exclude)
- Verification requirements

**Key concepts**:
- Tier 1 = Court documents (highest reliability)
- Tier 2 = Investigative journalism (high reliability)
- Tier 3 = Public records (verified)
- Tier 4 = Biographical databases (general)
- Tier 5 = Secondary sources (requires verification)

### `enrich_entity_data.py`
**Purpose**: Automated research tool (framework for future enhancement)
**Status**: Framework created, web search integration needed

**Usage**:
```bash
# Single entity mode
python3 enrich_entity_data.py --entity "Clinton, Bill"

# Batch mode (processes priority list)
python3 enrich_entity_data.py --batch --start 0 --end 10

# Help
python3 enrich_entity_data.py --help
```

**Current limitations**:
- Web search APIs not yet integrated
- Manual research still required
- Framework in place for future automation

### `add_researched_entities.py`
**Purpose**: Helper script to add manually researched entities
**Contains**: Examples for Prince Andrew, Leslie Wexner, Donald Trump

## Research Workflow

### Step 1: Select Entity from Priority List

```bash
# View priority list sorted by importance
cat data/metadata/priority_entities_for_research.json | jq '.entities[] | {name, flights, priority_reason}' | head -20
```

### Step 2: Conduct Web Research

**Search queries to use**:
1. `"{Entity Name}" + "Jeffrey Epstein" + biography`
2. `"{Entity Name}" + "Epstein case" + court`
3. `"{Entity Name}" + "Ghislaine Maxwell"`
4. `"{Entity Name}" + "Virginia Giuffre"`

**Prioritize sources**:
1. Court documents (PACER, CourtListener)
2. Reputable journalism (NYT, WSJ, Miami Herald, ProPublica)
3. Public records (flight logs, property records)
4. Biographical databases (Wikipedia, Britannica for basic facts)

### Step 3: Structure Data According to Schema

Follow the template in `entity_data_schema.json`:

```json
{
  "entity_id": "unique_identifier",
  "name": "Primary name",
  "name_variations": ["Alternative names"],
  "biographical_data": {
    "full_legal_name": {
      "value": "Full name",
      "confidence": "high|medium|low",
      "sources": [
        {
          "type": "court_document|journalism|public_record|biographical_database",
          "citation": "Full citation",
          "url": "URL if available",
          "date_accessed": "YYYY-MM-DD",
          "reliability_tier": 1
        }
      ]
    }
  },
  "epstein_relationship": {
    "relationship_summary": "Brief description",
    "documented_interactions": [],
    "public_statements": [],
    "legal_involvement": []
  }
}
```

### Step 4: Add to Database

Manually add to `data/metadata/enriched_entity_data.json` following examples of completed entities.

### Step 5: Verify Quality

**Checklist**:
- [ ] Every fact has at least one source
- [ ] Sources include URL and access date
- [ ] Reliability tier assigned to each source
- [ ] Biographical facts have 2+ independent sources
- [ ] Court documents cited where available
- [ ] No unverified allegations included
- [ ] Privacy guidelines followed

## Completed Entities (6)

1. **Ghislaine Maxwell** - Convicted sex trafficker, Epstein accomplice
2. **Virginia Roberts Giuffre** - Victim/survivor, key witness (deceased 2025)
3. **Glenn Dubin** - Billionaire hedge fund manager, financial ties
4. **Prince Andrew** - British royal, settled lawsuit with Giuffre
5. **Leslie Wexner** - Billionaire, Victoria's Secret founder, Epstein's client
6. **Donald Trump** - Former president, social ties in 1990s

## Priority Entities for Next Research Phase

### Phase 1 - High-Profile Cases (Recommended next 10):
1. **Doug Band** (13 flights) - Clinton aide
2. **Christopher Tucker** (11 flights) - Actor
3. **Luc Brunel** (30 flights) - Modeling agent, subject of testimony
4. **Alan Dershowitz** (multi-source) - Attorney
5. **Leon Black** (billionaire) - Apollo Global Management
6. **Bill Clinton** - Former president, reported flights
7. **Teala Davies** (23 flights)
8. **Eva Dubin** (15 flights) - Glenn Dubin's wife
9. **Sarah Kellen** (291 flights with Epstein) - Assistant
10. **Emmy Tayler** (194 flights with Epstein)

### Phase 2 - Remaining Billionaires (29 entities)
### Phase 3 - Top 50 Frequent Flyers (44 remaining)

## Data Outputs

### `data/metadata/enriched_entity_data.json`
- 6 entities fully researched
- Complete provenance for all facts
- 45 sources cited across all entities

### `data/metadata/priority_entities_for_research.json`
- 131 priority entities identified
- Sorted by relevance (flights, billionaire status, public interest)

### `data/metadata/ENTITY_RESEARCH_REPORT.md`
- Comprehensive research report
- Methodology documentation
- Quality metrics and statistics
- Next steps and recommendations

## Source Reliability Guidelines

### Tier 1 - Court Documents (Highest Reliability)
**Use for**: Criminal charges, convictions, lawsuit settlements, depositions, testimony
**Examples**:
- United States v. Ghislaine Maxwell (conviction)
- Giuffre v. Prince Andrew (settlement)
- Court exhibits (flight logs from trials)

### Tier 2 - Investigative Journalism (High Reliability)
**Use for**: Reported facts, interviews, investigative findings
**Trusted sources**:
- Miami Herald (Julie K. Brown's investigation)
- New York Times, Wall Street Journal
- ProPublica, NPR, BBC
- TIME, Bloomberg, Vanity Fair (for specific stories)

### Tier 3 - Public Records (Verified)
**Use for**: Official government/legal documents
**Examples**:
- DOJ-released flight logs
- Property records (public databases)
- SEC filings, corporate registrations

### Tier 4 - Biographical Databases (General)
**Use for**: Basic biographical facts only
**Examples**:
- Wikipedia (with verification from other sources)
- Britannica, Forbes profiles
- IMDb (for entertainment industry figures)

### Tier 5 - Secondary Sources (Requires Verification)
**Use with caution**: Must corroborate with higher tiers
**Examples**:
- News aggregators, smaller publications
- Not used in current research without corroboration

## Ethical Guidelines

### Include Only:
✓ Publicly reported information
✓ Court-documented facts
✓ Verified journalism from reputable sources
✓ Public statements by entities themselves
✓ Public records accessible to anyone

### Explicitly Exclude:
✗ Unverified allegations
✗ Social media rumors
✗ Tabloid speculation without verification
✗ Information about minors (unless adults who publicly identified)
✗ Private information not in public record

## Statistics

**Current Progress**:
- 6 of 131 priority entities completed (4.6%)
- 45 total sources cited
- 100% source provenance tracking
- 20% Tier 1 (court documents)
- 44% Tier 2 (journalism)

**Estimated Effort**:
- 15-20 minutes per entity (manual research)
- 15-20 hours for next 44 entities (Phase 1 + 2)
- 40-50 hours total for all 131 priority entities

## Next Steps

1. **Continue manual research** on Phase 1 entities (Doug Band, Christopher Tucker, etc.)
2. **Integrate web search APIs** into automation script
3. **Build human review interface** for quality assurance
4. **Link enriched data** to document mentions in OCR'd files
5. **Generate entity relationship graphs** from enriched data

## Questions?

Refer to:
- `entity_data_schema.json` - Complete template and guidelines
- `data/metadata/ENTITY_RESEARCH_REPORT.md` - Full research report
- `data/metadata/enriched_entity_data.json` - Examples of completed research

---

**Last Updated**: 2025-11-17
**Entities Completed**: 6 of 131
**Research Status**: Foundation established, ready for continued research
