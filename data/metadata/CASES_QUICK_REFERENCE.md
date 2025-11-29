# Legal Cases Quick Reference Guide

**Last Updated**: 2025-11-17

---

## Quick Case Lookup

### Criminal Cases

| Case | Docket | Status | Documents |
|------|--------|--------|-----------|
| **Florida v. Epstein** (2008) | 08-CF-000916-A | ✅ Served sentence | Available |
| **US v. Epstein** (2019) | 1:19-cr-00490-RMB | ❌ Dismissed (death) | [CourtListener](https://www.courtlistener.com/docket/15887848/united-states-v-epstein/) |
| **US v. Maxwell** (2020-2022) | 1:20-cr-00330-AJN | ⚖️ Serving 20 years | [CourtListener](https://www.courtlistener.com/docket/17318376/united-states-v-maxwell/) |

### Major Civil Cases

| Case | Docket | Settlement | Documents |
|------|--------|------------|-----------|
| **Giuffre v. Maxwell** (2015) | 1:15-cv-07433 | ✅ Settled 2017 | **4,553 pages** [CourtListener](https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/) |
| **Giuffre v. Andrew** (2021) | 1:21-cv-06702 | ✅ ~£12M (2022) | [CourtListener](https://www.courtlistener.com/docket/60119368/giuffre-v-prince-andrew/) |
| **Araoz v. Estate** (2019) | NY State Court | ✅ Compensation fund | Limited |
| **Wild v. US** (2008) | S.D. Florida | ⚖️ CVRA violation | [11th Circuit](https://media.ca11.uscourts.gov/opinions/pub/files/201913843.enb.pdf) |

### Bank Settlements

| Bank | Amount | Date | Class Size |
|------|--------|------|------------|
| **JPMorgan Chase** | $290M | June 2023 | 100+ victims |
| **Deutsche Bank** | $75M | May 2023 | Unknown |

### Estate Claims

| Claim | Amount | Recipients |
|-------|--------|------------|
| **USVI Settlement** | $105M | USVI victim trust |
| **Compensation Fund** | $125M | 136 individuals |

---

## Document Download Priority

### 🔴 High Priority - Download First

1. **Giuffre v. Maxwell unsealed documents** (4,553 pages)
   - Docket: 1:15-cv-07433
   - 8 batches released Jan 2024
   - Contains: Depositions, flight logs, witness testimony
   - Source: [CourtListener RECAP](https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/)

2. **US v. Epstein indictment** (2019)
   - Docket: 1:19-cr-00490-RMB
   - Federal sex trafficking charges
   - Source: [CourtListener](https://www.courtlistener.com/docket/15887848/united-states-v-epstein/)

3. **US v. Maxwell trial transcripts** (2021)
   - Docket: 1:20-cr-00330-AJN
   - Four victim testimonies
   - Source: [CourtListener](https://www.courtlistener.com/docket/17318376/united-states-v-maxwell/)

### 🟡 Medium Priority

4. **Giuffre v. Andrew settlement documents**
   - Docket: 1:21-cv-06702
   - Settlement announcement Feb 2022

5. **DOJ OPR Report on 2008 Plea Deal**
   - Alex Acosta "poor judgment" findings
   - Source: [DOJ Archives](https://www.justice.gov/archives/opa/press-release/file/1336416/dl)

### 🟢 Lower Priority - Already in Archive

6. **House Oversight Release** (67,144 PDFs)
   - Already downloaded in this project
   - Location: `data/raw/house_oversight_nov2025/`

---

## Key Victims (Public Identification)

### Full Names (Testified Publicly)

| Name | Age | Years | Case/Testimony |
|------|-----|-------|----------------|
| **Virginia Giuffre** | 17 | 1999-2002 | 2 lawsuits, BBC Panorama |
| **Annie Farmer** | 16 | 1996 | Maxwell trial (full name) |
| **Sarah Ransome** | 22 | 2006-07 | Lawsuit, Netflix doc |
| **Courtney Wild** | 14 | Early 2000s | CVRA lawsuit |
| **Jennifer Araoz** | 14-15 | 2001-02 | Estate lawsuit |
| **Michelle Licata** | 16 | Mid-2000s | Palm Beach investigation |
| **Maria Farmer** | Adult | 1995-96 | FBI lawsuit |
| **Johanna Sjoberg** | College age | Early 2000s | Deposition testimony |

### Pseudonyms (Maxwell Trial)

| Pseudonym | Age | Year |
|-----------|-----|------|
| **"Jane"** | 14 | 1994 |
| **"Kate"** | 17 | Mid-1990s |
| **Carolyn** | 14 | Early 2000s |

---

## Download Commands

### List all available cases
```bash
python3 scripts/download/download_case_files.py --list
```

### Download specific case
```bash
# Download Giuffre v Maxwell documents
python3 scripts/download/download_case_files.py --case giuffre_v_maxwell_2015
```

### Download all CourtListener cases
```bash
python3 scripts/download/download_case_files.py --source courtlistener
```

### Dry run (see what would be downloaded)
```bash
python3 scripts/download/download_case_files.py --all --dry-run
```

---

## Search by Case Type

### Want to find: Sexual abuse victims' testimony
**→ Download**: Giuffre v. Maxwell unsealed docs + Maxwell trial transcripts

### Want to find: Flight logs and travel records
**→ Download**: Giuffre v. Maxwell unsealed docs (contains unredacted flight logs)

### Want to find: Email correspondence
**→ Already have**: House Oversight release (67,144 PDFs)
**→ Also see**: Bloomberg analysis (18,000 emails - not publicly released)

### Want to find: Financial records
**→ Download**: Bank settlement documents (JPMorgan, Deutsche Bank)
**→ Already have**: House Oversight release

### Want to find: Criminal evidence
**→ Download**: US v. Epstein indictment, US v. Maxwell trial exhibits

---

## Case Status Summary

| Status | Count | Cases |
|--------|-------|-------|
| ✅ **Completed** | 9 | FL plea, Maxwell conviction, Giuffre settlements, bank settlements, estate settlements |
| ⚖️ **Ongoing** | 1 | Maxwell serving sentence (appeal possible) |
| ❌ **Dismissed** | 2 | Epstein death, Doe v Trump voluntary dismissal |
| 📊 **Resolved** | 6 | Compensation fund, class actions settled |

---

## Total Compensation to Victims

```
Estate Compensation Fund:    $125M  (136 individuals)
JPMorgan Settlement:         $290M  (100+ class)
Deutsche Bank Settlement:     $75M  (Unknown count)
USVI Settlement:             $105M  (Victim trust)
                            -------
TOTAL:                       $595M+ (250+ victims)
```

---

## Quick Links

- **Cases Index**: `data/metadata/cases_index.json`
- **Victims Index**: `data/metadata/victims_index.json`
- **Full Research**: `data/metadata/LEGAL_CASES_RESEARCH_SUMMARY.md`
- **Timeline**: `data/metadata/timeline_events.json`
- **Download Script**: `scripts/download/download_case_files.py`

---

## CourtListener Search Tips

### By Docket Number
1. Go to https://www.courtlistener.com/
2. Search bar: "1:15-cv-07433"
3. Click case → Browse documents

### By Party Name
- Search: "Virginia Giuffre"
- Filter: Court = SDNY
- Date range: 2015-2024

### By Judge
- Search: "Judge Loretta Preska"
- Filter: Document type = Opinion

### RECAP Extensions
- Install browser extension
- Automatically saves PACER docs to free archive
- Reduces PACER fees

---

## PACER Access (Paid Option)

**Registration**: https://pacer.uscourts.gov/
**Cost**: $0.10/page, capped at $3.00/document
**Fee Waiver**: Quarterly charges under $30 waived

**Recommended for**:
- Documents not yet in RECAP
- Official certified copies
- Recent filings

**Not needed if**:
- Document already on CourtListener
- Using RECAP browser extension
- Can wait for documents to appear in archive

---

## Important Notes

⚠️ **Respect Victim Privacy**:
- Only publicly identified victims listed
- Do not attempt to identify pseudonym victims
- Anonymous class members remain anonymous

⚠️ **Document Sensitivity**:
- Some documents contain graphic testimony
- Redactions protect victim identities
- Handle with appropriate care

⚠️ **Legal Use Only**:
- Documents for research/journalism
- Respect court sealing orders
- Do not redistribute sealed materials

---

**For detailed information, see**: `LEGAL_CASES_RESEARCH_SUMMARY.md`
