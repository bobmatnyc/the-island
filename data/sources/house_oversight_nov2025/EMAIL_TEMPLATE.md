# Email Template for Requesting Epstein Dataset

---

## Option 1: Direct Request (Recommended)

**TO:** shreyashankar@berkeley.edu
**CC:** adityagp@berkeley.edu
**SUBJECT:** Request for Epstein Email Pipeline Configuration and Dataset

---

Dear Shreya,

I hope this message finds you well. I recently came across your impressive DocETL Epstein Email Archive Explorer (https://www.docetl.org/showcase/epstein-email-explorer), and I'm very interested in using this processed dataset for research purposes.

I am working on analyzing the November 2025 House Oversight Committee Epstein document release and would like to build upon the excellent work you've already done with DocETL.

**I am respectfully requesting access to:**

1. The YAML pipeline configuration file used for the Epstein email analysis
2. The processed dataset (JSON/CSV format) containing the 2,322 emails with extracted entities, topics, and analysis
3. Any preprocessing scripts used to extract and structure emails from the original PDFs

**Intended Use:**
[Customize this section with your specific use case. Examples:]
- Academic research on [specific topic]
- Investigative journalism project
- Development of complementary analysis tools
- Replication study for research purposes

I fully understand if there are limitations on data sharing and would be happy to discuss any conditions or attribution requirements. I will properly cite both the original House Oversight Committee source and your DocETL work in any publications or public outputs.

If the processed dataset is not available for sharing, I would be grateful for guidance on:
- The YAML configuration structure you used
- Recommendations for PDF text extraction from the source documents
- Any lessons learned during the pipeline development

**About me:**
[Add 2-3 sentences about yourself, your affiliation, and why you're interested in this data]

Thank you for your time and for creating such valuable open-source tools. DocETL is an impressive system, and I look forward to potentially using it for this and future projects.

Best regards,
[Your Name]
[Your Affiliation]
[Your Email]
[Your Website/LinkedIn - optional]

---

## Option 2: Community Request via Discord

**Discord Server:** discord.gg/fHp7B2X3xx
**Channel:** #general or #help (check server structure when joining)

**Message Template:**

---

Hi everyone! 👋

I'm interested in working with the Epstein email dataset that was processed for the DocETL showcase (https://www.docetl.org/showcase/epstein-email-explorer).

Has anyone in the community:
- Replicated this pipeline?
- Has access to the YAML configuration?
- Successfully extracted the emails from the House Oversight PDFs?

I've downloaded the original 20k pages from the House Oversight Committee and would love to collaborate or learn from others who have worked with this dataset.

Happy to share any scripts or findings I develop!

Background: [Brief description of your project/goals]

Thanks!
[Your Name]

---

## Option 3: Formal Academic Collaboration Request

**TO:** adityagp@berkeley.edu, shreyashankar@berkeley.edu
**SUBJECT:** Research Collaboration Proposal - Epstein Document Analysis

---

Dear Professor Parameswaran and Shreya,

I am writing to explore potential collaboration opportunities related to the Epstein Email Archive analysis using DocETL.

**Research Proposal:**
[Describe your research question, methodology, and goals]

**Why DocETL:**
Your team's approach to processing the Epstein emails demonstrates the power of LLM-based document analysis for investigative research. I believe there are opportunities to:

1. Extend the analysis to [specific area]
2. Validate findings through [specific methodology]
3. Connect this dataset with [related data sources]

**Requested Resources:**
- Access to the processed Epstein email dataset
- YAML pipeline configuration
- Potential co-authorship or collaboration on resulting publications

**Proposed Timeline:**
[Outline your research timeline]

**Institutional Support:**
[Describe your affiliation, funding, or institutional backing]

I would welcome the opportunity to discuss this further and explore how we might work together on this important research.

Please let me know if you would be available for a brief call to discuss this proposal.

Best regards,
[Your Full Name]
[Title/Position]
[Institution]
[Email]
[Phone]

---

## Tips for Successful Contact

### Do's ✅
- Be specific about your intended use
- Offer to cite and attribute their work
- Show you've done your research (mention DocETL, the $8.04 cost, etc.)
- Be respectful of their time
- Offer something in return (shared code, collaboration, co-authorship)
- Follow up politely if no response after 1 week

### Don'ts ❌
- Don't demand access - it's a request
- Don't be vague about your intended use
- Don't ignore attribution requirements
- Don't share data they provide without permission
- Don't spam with multiple emails

### Timeline Expectations
- **Response time:** 2-7 days (academics are busy)
- **Follow-up:** Wait at least 1 week before following up
- **Alternative:** If no response after 2 weeks, consider replicating pipeline yourself

### Increase Your Chances
1. **Show you're serious:** Mention you've already downloaded the original data
2. **Demonstrate value:** Explain what insights you hope to contribute
3. **Be professional:** Use institutional email if possible
4. **Offer collaboration:** Suggest sharing findings or co-authoring
5. **Join the community:** Participate in Discord before making big requests

---

## If Request is Denied or No Response

### Plan B: Build It Yourself

1. **Download source data:**
   - Google Drive: https://drive.google.com/drive/folders/1hTNH5woIRio578onLGElkTWofUSWRoH_?usp=sharing

2. **PDF Processing:**
   ```python
   # Example using PyPDF2 or pdfplumber
   import pdfplumber

   def extract_emails_from_pdf(pdf_path):
       with pdfplumber.open(pdf_path) as pdf:
           for page in pdf.pages:
               text = page.extract_text()
               # Parse email structure
               # Extract sender, recipient, date, subject, body
   ```

3. **Install DocETL:**
   ```bash
   pip install docetl
   ```

4. **Reference documentation:**
   - Tutorial: https://ucbepic.github.io/docetl/tutorial/
   - Examples: https://github.com/ucbepic/docetl-examples

5. **Estimated investment:**
   - Time: 3-7 days development
   - Cost: $8-20 in LLM API calls
   - Skills needed: Python, YAML, PDF processing

---

*Use these templates as starting points and customize based on your specific needs and relationship with the team.*
