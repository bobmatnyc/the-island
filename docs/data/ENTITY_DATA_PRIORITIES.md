# Entity Data Quality - Priority Action List

**Quick Summary**: **Impact**: Network graph accuracy, entity counts...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `"Prince Andrew, Duke of York"` (canonical) ← `"Prince Andrew"` (duplicate)
- Sources: black_book + flight_logs
- Flights: 0 + 1 = 1
- `"Sarah Ferguson, Duchess of York"` (canonical) ← `"Sarah Ferguson"` (duplicate)
- Sources: black_book + flight_logs

---

**Immediate Actions Required**
**Date**: 2025-11-19

---

## 🔴 CRITICAL (Do Immediately - This Week)

### Priority 1: Merge Prince Andrew Duplicate
**Impact**: Network graph accuracy, entity counts
**Effort**: 1 hour
**Status**: ❌ Not Started

**Entities to Merge**:
- `"Prince Andrew, Duke of York"` (canonical) ← `"Prince Andrew"` (duplicate)
- Sources: black_book + flight_logs
- Flights: 0 + 1 = 1

**Action**:
```bash
# Create and run merge script
python3 scripts/data_quality/merge_royal_duplicates.py
```

**Verification**:
```bash
# Should return only 1 entity
jq '.entities | to_entries | map(.value | select(.name | contains("Prince Andrew"))) | length' \
  data/md/entities/ENTITIES_INDEX.json
```

---

### Priority 2: Merge Sarah Ferguson Duplicate
**Impact**: Network graph accuracy, entity counts
**Effort**: 1 hour (same script as Priority 1)
**Status**: ❌ Not Started

**Entities to Merge**:
- `"Sarah Ferguson, Duchess of York"` (canonical) ← `"Sarah Ferguson"` (duplicate)
- Sources: black_book + flight_logs
- Flights: 0 + 1 = 1

**Action**: Included in merge_royal_duplicates.py (same as Priority 1)

---

### Priority 3: Implement Alias System
**Impact**: Search functionality, user experience
**Effort**: 3 hours
**Status**: ❌ Not Started

**Entities Needing Aliases**: 19 priority entities (royals, politicians)

**Action**:
```bash
# Create and run alias script
python3 scripts/data_quality/add_entity_aliases.py
```

**Creates**:
- `ENTITIES_INDEX.json` updated with `aliases` field
- `ALIAS_INDEX.json` created (reverse mapping)

**Verification**:
```bash
# Should return 19+
jq '.entities | to_entries | map(.value | select(.aliases)) | length' \
  data/md/entities/ENTITIES_INDEX.json
```

---

### Priority 4: Update Search Functions
**Impact**: Search works with aliases
**Effort**: 2 hours
**Status**: ❌ Not Started

**Files to Update**:
- `/server/routes/entities.py` (or entity search route)
- Any front-end search components

**Required Changes**:
1. Load ALIAS_INDEX.json at startup
2. Add `get_canonical_name()` function
3. Update `search_entities()` to check aliases
4. Update `get_entity_by_name()` to accept aliases

**Test Cases**:
```python
# These should all work after implementation:
search_entities("Prince Andrew")  # → finds "Prince Andrew, Duke of York"
search_entities("Bill Clinton")    # → finds "William Clinton"
get_entity_by_name("Fergie")      # → returns "Sarah Ferguson, Duchess of York"
```

---

## 🟡 HIGH (Do This Week If Possible)

### Priority 5: Investigate Misspellings
**Impact**: Bio coverage improvement
**Effort**: 2 hours research + 1 hour implementation
**Status**: ❌ Not Started

**Top Candidates**:
1. **"Ronald Durkle"** (4 flights) → Likely **"Ronald Burkle"** (billionaire)
2. **"James Kennez"** (11 flights) → Possibly **"James Kennedy"**
3. **"Sherrie Crape"** (4 flights) → Unknown, needs research

**Action**:
```bash
# Manual Google research
# Query format: "[Name]" "Epstein" OR "Jeffrey Epstein"

# If confirmed misspelling:
# 1. Find/create correct entity
# 2. Merge misspelled entity into correct one
# 3. Update ENTITIES_INDEX.json
```

**Expected Outcome**: +5-10% bio coverage if billionaire names are corrected

---

### Priority 6: Research Top 10 Missing Bios
**Impact**: Bio coverage improvement
**Effort**: 5 hours (30 min per entity)
**Status**: ❌ Not Started

**Entities** (excluding generic names):
1. Gramza (20 flights)
2. Lang (18 flights)
3. Mucinska, Adriana (12 flights)
4. James Kennez (11 flights)
5. Swater, Rodey (11 flights)
6. Teal (6 flights)
7. Alexia Wallert (5 flights)
8. Cristalle Wasche (5 flights)
9. Natalya Malyshov (4 flights)
10. Pamela Johanao (4 flights)

**Research Sources**:
- Google: `"[Name]" "Epstein"`
- Court documents (PACER, CourtListener)
- LinkedIn, Facebook (public profiles)
- News archives

**Bio Template**:
```
[Name] is/was [brief description]. [Relation to Epstein if known]. [Additional context].

Source: [Manual Research - Date]
```

---

## 🟢 MEDIUM (Do Next Week)

### Priority 7: Create Manual Bio Enrichment Tool
**Impact**: Streamline research workflow
**Effort**: 4 hours
**Status**: ❌ Not Started

**Features**:
- Prioritized queue (by flight count)
- Research checklist (Google, court docs, social media)
- Bio template with source attribution
- Progress tracking
- Resume capability

**Usage**:
```bash
python3 scripts/research/manual_bio_enrichment.py
```

---

### Priority 8: Investigate Celina Entities
**Impact**: Potential duplicate merge
**Effort**: 1 hour research
**Status**: ❌ Not Started

**Question**: Are these the same person?
- "Dubin, Celina" (15 flights)
- "Midelfart, Celina" (18 flights)

**Research**:
1. Check if Celina Midelfart married Glenn Dubin
2. Compare flight dates (before/after marriage?)
3. Research public records

**Possible Outcomes**:
- **Same person**: Merge, add maiden name as alias
- **Different people**: No action needed

---

### Priority 9: Create Quality Metrics Dashboard
**Impact**: Ongoing quality monitoring
**Effort**: 3 hours
**Status**: ❌ Not Started

**Metrics to Track**:
- Total entities
- Bio coverage percentage
- Entities with aliases
- Recent merges
- Quality score trend

**Output**: `data/metadata/quality_dashboard.json`

---

## 📊 Week 1 Success Metrics

**Before** (Current State):
```
Total Entities:        1,639
Bio Coverage:          86.0% (1,409/1,639)
Active Duplicates:     2
Entities with Aliases: 0
Quality Score:         B+ (87/100)
```

**After** (Target by End of Week):
```
Total Entities:        1,637 (2 merged) ✅
Bio Coverage:          86.0% (same, but improved quality) ✅
Active Duplicates:     0 ✅
Entities with Aliases: 19+ ✅
Quality Score:         A- (90/100) ✅
```

---

## 🎯 Daily Implementation Schedule

### Monday
**Focus**: Duplicate merges
- [ ] Morning: Create `merge_royal_duplicates.py`
- [ ] Afternoon: Test merge script, verify results
- [ ] Evening: Generate merge report

**Deliverable**: 0 duplicates

---

### Tuesday
**Focus**: Alias system implementation
- [ ] Morning: Create `add_entity_aliases.py`
- [ ] Afternoon: Test alias script, create ALIAS_INDEX.json
- [ ] Evening: Verify 19+ entities have aliases

**Deliverable**: Alias system working

---

### Wednesday
**Focus**: Search function updates
- [ ] Morning: Update server-side search functions
- [ ] Afternoon: Update front-end search components
- [ ] Evening: Test all search scenarios

**Deliverable**: Alias search working

---

### Thursday
**Focus**: Misspelling investigation
- [ ] Morning: Research "Ronald Durkle" → "Ronald Burkle"
- [ ] Afternoon: Research "James Kennez", "Sherrie Crape"
- [ ] Evening: Create misspelling merge plan

**Deliverable**: 3-5 misspellings identified

---

### Friday
**Focus**: Testing & documentation
- [ ] Morning: End-to-end testing (search, network graph)
- [ ] Afternoon: Generate quality report
- [ ] Evening: Documentation updates

**Deliverable**: Week 1 complete, ready for Week 2

---

## ✅ Definition of Done (Week 1)

A task is complete when:
- [ ] Script created and tested
- [ ] ENTITIES_INDEX.json updated
- [ ] Backup created before changes
- [ ] Verification query passes
- [ ] No errors in entity network graph
- [ ] Search functions work with aliases
- [ ] Quality report generated

**Final Check**:
```bash
# All these should pass:
jq '.entities | length' data/md/entities/ENTITIES_INDEX.json  # = 1637
jq '.entities | to_entries | map(.value | select(.aliases)) | length' data/md/entities/ENTITIES_INDEX.json  # ≥ 19
jq 'keys | length' data/md/entities/ALIAS_INDEX.json  # ≥ 30
test -f data/md/entities/ENTITIES_INDEX.backup_*.json  # backups exist
```

---

## 🚨 Blockers & Risks

### Potential Blockers
1. **Entity references in other files** (documents, network graph)
   - **Mitigation**: Use aliases for backward compatibility

2. **Search performance degradation**
   - **Mitigation**: Index aliases separately, use O(1) lookups

3. **Incorrect merges** (false positive duplicates)
   - **Mitigation**: Manual review before each merge

### Risk Management
- ✅ Create backup before all operations
- ✅ Test on small subset first
- ✅ Preserve merge history in `merged_from` field
- ✅ Document all changes in commit messages

---

## 📞 Questions & Support

**Technical Questions**:
- Schema changes: See `/ENTITY_DATA_QUALITY_ANALYSIS.md` Section 5.3
- Merge strategy: See `/ENTITY_DATA_QUALITY_ANALYSIS.md` Section 6.3
- Alias implementation: See `/ENTITY_DATA_QUALITY_ANALYSIS.md` Section 7

**Implementation Questions**:
- Quick start: See `/DEDUPLICATION_IMPLEMENTATION_GUIDE.md`
- Code examples: See `/DEDUPLICATION_IMPLEMENTATION_GUIDE.md` Tasks 1-4

**Visual Overview**:
- Dashboard: See `/ENTITY_QUALITY_VISUAL_SUMMARY.md`

---

## 📝 Progress Tracking

**Mark completed items with ✅**

### Week 1 Progress
- [ ] Priority 1: Merge Prince Andrew ❌
- [ ] Priority 2: Merge Sarah Ferguson ❌
- [ ] Priority 3: Implement aliases ❌
- [ ] Priority 4: Update search functions ❌
- [ ] Priority 5: Investigate misspellings ❌
- [ ] Priority 6: Research top 10 bios ⏸️ (Optional for Week 1)

**Last Updated**: 2025-11-19
**Status**: 🔴 CRITICAL - Week 1 tasks not started
**Next Action**: Create and run merge_royal_duplicates.py
