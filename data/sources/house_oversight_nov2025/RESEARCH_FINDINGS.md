# DocETL Epstein Email Dataset - Research Findings

**Research Date:** November 16, 2025
**Researcher:** Claude (Sonnet 4.5)
**Project:** Epstein Email Archive Access & Analysis

---

## Executive Summary

The House Oversight Committee released 20,000+ pages of Epstein documents in November 2025. UC Berkeley's EPIC Data Lab processed 2,322 emails using their DocETL framework and created an interactive explorer. The original data is publicly accessible, but the processed dataset requires either replication of the pipeline or direct contact with the team for access.

---

## 1. Original Data Sources (DIRECT DOWNLOAD LINKS)

### House Oversight Committee Official Release
**Release Date:** November 12, 2025
**Total Documents:** 20,000+ pages from Epstein Estate

#### Primary Download Locations:

1. **Google Drive (Primary)**
   - Link: https://drive.google.com/drive/folders/1hTNH5woIRio578onLGElkTWofUSWRoH_?usp=sharing
   - Source: House Committee on Oversight and Government Reform
   - Format: PDF files

2. **Dropbox (Backup)**
   - Link: https://www.dropbox.com/scl/fo/9bq6uj0pnycpa4gxqiuzs/ABBA-BoYUAT7627MBeLiVYg?rlkey=3s6ggcjihou9nt8srsn2qt1n7&st=4aejaath&dl=0
   - Source: House Committee on Oversight and Government Reform
   - Format: PDF files

3. **Democrats Oversight Committee Press Release**
   - Link: https://oversightdemocrats.house.gov/news/press-releases/house-oversight-committee-releases-jeffrey-epstein-email-correspondence-raising
   - Contains: Specific email correspondence (3-emails_redacted.pdf)
   - Total from Estate: 23,000 documents (still under review)

### Additional Data Sources:

4. **Previous DOJ Release**
   - Link: https://oversight.house.gov/release/oversight-committee-releases-epstein-records-provided-by-the-department-of-justice/
   - Contains: Records from Department of Justice

5. **Earlier Estate Documents (September)**
   - Link: https://oversight.house.gov/release/oversight-committee-releases-records-provided-by-the-epstein-estate-chairman-comer-provides-statement/
   - Contains: 33,000+ pages of previous releases

---

## 2. DocETL Processed Dataset

### Interactive Explorer
- **URL:** https://www.docetl.org/showcase/epstein-email-explorer
- **Emails Processed:** 2,322 emails
- **Processing Cost:** $8.04 (using DocETL pipeline)
- **Features:**
  - Entity extraction (people, organizations, locations)
  - Tone and topic analysis
  - Potential concern identification
  - Email summaries
  - Searchable by participants, organizations, subject lines, content

### Data Access Status
**CURRENT STATUS:** The processed dataset is NOT directly downloadable from the showcase page.

**Options to Access Processed Data:**
1. Use the web-based explorer (browse only, no bulk export visible)
2. Replicate the pipeline using DocETL (see Section 5)
3. Contact UC Berkeley EPIC team directly (see Section 3)
4. Use alternative processed versions (see Section 4)

---

## 3. UC Berkeley EPIC Data Lab Contact Information

### Primary Contact - DocETL Creator
**Shreya Shankar**
- Role: PhD Student, UC Berkeley EECS (final year)
- Creator of DocETL
- Email: shreyashankar@berkeley.edu
- Twitter: @sh_reya
- GitHub: github.com/shreyashankar
- Website: www.sh-reya.com
- Google Scholar: https://scholar.google.com/citations?user=0WD1nZcAAAAJ&hl=en

### Lab Director
**Aditya Parameswaran**
- Role: Associate Professor, UC Berkeley EECS & School of Information
- Co-director of EPIC Data Lab
- Email: adityagp@berkeley.edu
- Website: https://people.eecs.berkeley.edu/~adityagp/
- Twitter: @adityagp

### Other Principal Investigators
- **Sarah Chasins** - Assistant Professor, EECS
- **Joseph Hellerstein** - Professor, EECS
- **Niloufar Salehi** - Assistant Professor, School of Information
- **Erin Kerrison** - Assistant Professor, School of Social Welfare

### Lab Information
- **Lab Website:** https://epic.berkeley.edu/
- **Discord Community:** discord.gg/fHp7B2X3xx
- **GitHub Organization:** https://github.com/ucbepic
- **Mission:** Democratize data work via no/low-code interfaces powered by AI

---

## 4. Alternative Public Datasets & Tools

### Third-Party Processing

1. **Google Pinpoint Searchable Database**
   - Created by: Courier Newsroom
   - Link: https://journaliststudio.google.com/pinpoint/search?collection=092314e384a58618
   - Features: Searchable interface for all 20,000 files
   - Contact: camaron@couriernewsroom.com
   - Note: Files described as "poorly organized" with "unhelpful labels"

2. **GitHub Repository with LLM-Optimized Index**
   - Creator: ChrisSc
   - Repository: https://github.com/ChrisSc/epstein-files (Note: Returned 404 during research)
   - Description: Hierarchical index system for 2,897 historical documents
   - Features: Navigate 60.7 MB using 665 KB of strategic indexes
   - Content mentions: Trump mentioned 4,437 times

3. **Obsidian Vault Conversion**
   - Repository: https://github.com/rodgzilla/epstein_email_obsidian_vault
   - Description: Emails processed into Obsidian Vault format
   - Tools used: Obsidian Importer plugin and Claude Code

4. **Other GitHub Projects**
   - https://github.com/maxandrews/Epstein-doc-explorer - Graph explorer
   - https://github.com/esteininger/epstein-docs - Document processing
   - https://github.com/cern1710/epstein-docanal - Text generator

### Academic/Research Repositories
**Status:** No HuggingFace or Kaggle datasets found during research.

---

## 5. DocETL Platform - Technical Details

### Open Source Status
- **License:** MIT License
- **GitHub:** https://github.com/ucbepic/docetl
- **Stars:** 3,100+ (as of research date)
- **Forks:** 324+
- **Status:** Fully open source, can be run locally

### Installation & Setup
- **Documentation:** https://ucbepic.github.io/docetl/
- **PyPI Package:** https://pypi.org/project/docetl/
- **Installation:** `pip install docetl`
- **Requirements:** Python, LLM API access (OpenAI, etc.)

### Pipeline Architecture
DocETL uses YAML configuration files to define data processing pipelines:

```yaml
datasets:
  email_data:
    type: file
    path: "emails.json"

operations:
  - name: extract_entities
    type: map
    # ... operation configuration

pipeline:
  steps:
    - name: process_emails
      operations: [extract_entities, analyze_tone, ...]
```

### Key Features
- Agentic LLM-powered data processing
- Support for complex document ETL
- YAML-based pipeline definition
- Python API available
- Web-based playground: https://www.docetl.org/playground
- CLI tool for local execution

### Example Pipelines Available
Repository: https://github.com/ucbepic/docetl-examples

**Current Examples:**
1. ICLR Reviews Analysis - Conference paper review theme extraction
2. SEC 8-Ks - Financial document processing

**Note:** Epstein email pipeline configuration NOT currently published in examples repo.

### Repository Structure (docetl-examples)
```
docetl-examples/
├── .gitattributes
├── .gitignore
├── README.md
├── iclr-reviews/
└── sec-8ks/
```

**Data Storage:** Uses Git LFS for large datasets
**Setup:** Requires `git lfs pull` after cloning

---

## 6. Replicating the DocETL Analysis

### Steps to Replicate

1. **Obtain Original Data**
   - Download from House Oversight Committee links (Section 1)
   - Format: PDF files, approximately 20,000 pages

2. **Extract Email Text**
   - Parse PDFs to extract email content
   - Structure as JSON (email body, sender, recipient, date, subject, etc.)

3. **Install DocETL**
   ```bash
   pip install docetl
   ```

4. **Define Pipeline YAML**
   - Reference: DocETL documentation (https://ucbepic.github.io/docetl/)
   - Operations needed:
     - Entity extraction (people, organizations, locations)
     - Tone analysis
     - Topic classification
     - Concern identification
     - Email summarization

5. **Run Pipeline**
   ```bash
   docetl run pipeline.yaml
   ```

6. **Estimated Cost**
   - Original pipeline: $8.04
   - May vary based on LLM provider and model choice

### Alternative: Request Pipeline Configuration
Contact Shreya Shankar (shreyashankar@berkeley.edu) to request:
- The YAML configuration used for the showcase
- Processed dataset (if shareable)
- Guidance on replication

---

## 7. Legal & Ethical Considerations

### Data Access Rights
✅ **LEGAL:** Original documents released by House Oversight Committee are public records
✅ **LEGAL:** No restrictions on downloading from official government sources
✅ **LEGAL:** Academic/journalistic use is encouraged per the showcase disclaimer

### Usage Guidelines
- **Attribution Required:** Reference original House Oversight Committee release
- **Verification Required:** AI assessments may contain errors, verify against primary sources
- **Privacy Considerations:** Some documents contain redactions for victim protection

### Citation Recommendation
When using this data:
1. Cite the House Oversight Committee as primary source
2. If using DocETL processed data, cite the DocETL showcase
3. If using DocETL tool, cite the DocETL paper: https://arxiv.org/html/2410.12189v2

---

## 8. Recommended Next Steps

### Immediate Actions

1. **Download Original Data**
   - Start with Google Drive link: https://drive.google.com/drive/folders/1hTNH5woIRio578onLGElkTWofUSWRoH_?usp=sharing
   - Use Dropbox backup if needed

2. **Explore Interactive Interface**
   - Visit: https://www.docetl.org/showcase/epstein-email-explorer
   - Understand the data structure and analysis approach

3. **Contact UC Berkeley Team**
   - Email Shreya Shankar: shreyashankar@berkeley.edu
   - Subject: "Request for Epstein Email Pipeline Configuration"
   - Ask for:
     - YAML pipeline configuration
     - Processed dataset (JSON format if available)
     - Any preprocessing scripts used

### Medium-Term Actions

4. **Set Up DocETL Environment**
   - Install DocETL: `pip install docetl`
   - Review documentation: https://ucbepic.github.io/docetl/
   - Test with example pipelines from docetl-examples repo

5. **PDF Processing**
   - Develop PDF parsing pipeline
   - Extract structured email data (sender, recipient, date, subject, body)
   - Handle multi-page email threads

6. **Replicate Analysis**
   - Create DocETL pipeline based on showcase description
   - Process 2,322 emails identified in showcase
   - Compare results with interactive explorer

### Alternative Approaches

7. **Use Existing Tools**
   - Google Pinpoint database: https://journaliststudio.google.com/pinpoint/search?collection=092314e384a58618
   - GitHub repositories with preprocessed data

8. **Community Collaboration**
   - Join DocETL Discord: discord.gg/fHp7B2X3xx
   - Ask community if anyone has replicated the pipeline
   - Share findings and scripts

---

## 9. Additional Resources

### Research Papers
- **DocETL Paper:** https://arxiv.org/html/2410.12189v2
  - Title: "DocETL: Agentic Query Rewriting and Evaluation for Complex Document Processing"
  - Authors: Shreya Shankar, et al.

### News Coverage
- NPR: https://www.npr.org/2025/11/13/nx-s1-5607057/house-committee-releases-over-20-000-documents-from-epstein-estate
- Axios: https://www.axios.com/2025/11/12/new-epstein-files-emails-released-doj-trump
- CNN: https://www.cnn.com/politics/live-news/trump-epstein-emails-11-12-25
- ABC News: https://abcnews.go.com/Politics/house-democrats-release-new-epstein-emails-referencing-trump/story?id=127435983

### EPIC Data Lab Projects
- Criminal justice big data tools (NACDL partnership)
- Public health data analysis
- Housing inequality research
- Hate speech detection

---

## 10. Summary & Key Takeaways

### ✅ What We Found

1. **Original Data:** Fully accessible via House Oversight Committee (Google Drive & Dropbox)
2. **DocETL Tool:** Open source (MIT), can replicate analysis locally
3. **Team Contact:** Direct email to creator Shreya Shankar available
4. **Alternative Tools:** Multiple third-party processed versions exist
5. **Legal Status:** Public records, free to use with attribution

### ❌ What's Not Available

1. **Processed Dataset:** No direct download from DocETL showcase
2. **Pipeline Config:** YAML configuration not published in examples repo
3. **API Access:** No programmatic API for the interactive explorer
4. **HuggingFace/Kaggle:** No standardized datasets on these platforms

### 🎯 Best Path Forward

**RECOMMENDED APPROACH:**
1. Email Shreya Shankar (shreyashankar@berkeley.edu) requesting:
   - Pipeline YAML configuration
   - Processed JSON dataset (if shareable)
   - PDF preprocessing approach

2. Parallel track: Download original PDFs and start extraction

3. Use DocETL documentation to build pipeline if no response

**ESTIMATED TIMELINE:**
- Immediate: Download original data (1-2 hours)
- Short-term: Contact team, await response (1-5 days)
- Medium-term: Replicate pipeline if needed (3-7 days development)

**ESTIMATED COST:**
- LLM processing: ~$8-20 (depending on provider)
- Development time: 20-40 hours (if building from scratch)
- $0 if team shares processed data

---

## Contact for Questions

**Primary Contact:** Shreya Shankar (shreyashankar@berkeley.edu)
**Lab Contact:** EPIC Data Lab (epic.berkeley.edu)
**Discord Community:** discord.gg/fHp7B2X3xx

---

*Research compiled by Claude (Anthropic) on November 16, 2025*
*All links verified as of research date*
