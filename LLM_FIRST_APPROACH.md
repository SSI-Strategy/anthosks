# LLM-First Automation Approach
## Simplified Architecture with Advanced LLM Extraction

**Date:** September 30, 2025
**Scenario:** Assuming highly capable LLM (GPT-4, Claude 3.5 Sonnet, or Gemini Pro) with excellent structured extraction

---

## Key Changes from Hybrid Approach

### 1. Architecture Simplification

#### **Before (Hybrid Approach):**
```
PDF → Text Extraction → Deterministic Parser (regex/rules)
                      → LLM Fallback (for ambiguous cases)
                      → Merge Results → Validation
```

#### **After (LLM-First Approach):**
```
PDF → Text Extraction → LLM Structured Extraction → Validation
```

**Eliminated Components:**
- Complex regex pattern libraries
- Rule-based parsers for different report sections
- Template detection logic
- Deterministic/LLM merge logic
- Multiple extraction pathways

---

## 2. Simplified Python Implementation

### **Complete Extraction Pipeline (LLM-First)**

```python
from anthropic import Anthropic
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import pdfplumber

# === Data Models (Same as before) ===

class SiteInfo(BaseModel):
    site_number: str
    country: str
    institution: str
    pi_first_name: str
    pi_last_name: str
    city: Optional[str] = None
    anthos_staff: str
    cra_name: Optional[str] = None

class RecruitmentStats(BaseModel):
    screened: int
    screen_failures: int
    randomized_enrolled: int
    early_discontinued: int
    completed_treatment: int
    completed_study: int

class QuestionResponse(BaseModel):
    question_number: int
    question_text: str
    answer: str  # Yes, No, NA, NR
    narrative_summary: Optional[str] = None  # 2-3 sentence summary
    key_finding: Optional[str] = None  # One-liner if critical

class ActionItem(BaseModel):
    item_number: int
    description: str
    action_to_be_taken: str
    responsible: str
    due_date: str  # Let LLM format, parse later

class RiskAssessment(BaseModel):
    site_level_risks_identified: bool
    cra_level_risks_identified: bool
    impact_country_level: bool
    impact_study_level: bool
    narrative: str

class MOVReport(BaseModel):
    # Metadata
    protocol_number: str
    site_info: SiteInfo
    visit_start_date: str
    visit_end_date: str
    visit_type: str

    # Core Data
    recruitment_stats: RecruitmentStats
    question_responses: List[QuestionResponse]
    action_items: List[ActionItem]
    risk_assessment: RiskAssessment

    # Quality Summary
    overall_site_quality: str  # Excellent, Good, Adequate, Needs Improvement, Poor
    key_concerns: List[str]
    key_strengths: List[str]

    # Metrics
    extraction_timestamp: datetime
    llm_model: str

# === Single-Pass LLM Extraction ===

def extract_mov_report_llm_first(pdf_path: str) -> MOVReport:
    """
    Extract entire MOV report using single LLM call with structured output.

    This approach leverages Claude 3.5 Sonnet's vision + long context (200K tokens)
    OR GPT-4V's multimodal capabilities to process the entire PDF.
    """

    client = Anthropic(api_key="your-api-key")

    # Extract text from PDF (or use vision models directly on PDF pages)
    full_text = extract_pdf_text(pdf_path)

    # Create JSON schema for structured output
    schema = MOVReport.model_json_schema()

    # Single LLM call with structured extraction prompt
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8000,
        temperature=0,  # Deterministic extraction
        messages=[
            {
                "role": "user",
                "content": f"""
You are extracting structured data from a Monitoring Oversight Visit (MOV) report for a clinical trial.

**CRITICAL INSTRUCTIONS:**
1. Extract ALL data exactly as it appears in the report
2. For Yes/No questions, look for checkbox symbols (☒ vs ☐)
3. For missing data, use null rather than guessing
4. For dates, extract in YYYY-MM-DD format
5. For narrative summaries, condense to 2-3 sentences maximum
6. Return ONLY valid JSON matching the schema below

**REPORT TEXT:**
{full_text}

**OUTPUT SCHEMA:**
{schema}

**IMPORTANT FIELDS TO EXTRACT:**

1. HEADER SECTION (Page 1):
   - Protocol Number (format: "Protocol ANT-XXX")
   - Site Number (6-digit number)
   - Country
   - Principal Investigator name
   - Visit dates
   - ANTHOS Staff (Clinical Oversight Manager)
   - CRA name
   - Visit Type (SIV MOV, IMV MOV, or COV MOV)

2. RECRUITMENT STATISTICS (Pages 1-2):
   - # screened patients
   - # screen failures
   - # randomized enrolled
   - # early discontinued
   - # completed treatment
   - # completed study

3. QUESTIONS (Pages 2-34):
   - Extract all 76+ questions
   - For each: question number, question text, answer (Yes/No/NA/NR)
   - Summarize narrative response in 2-3 sentences
   - Flag critical findings

4. ACTION ITEMS TABLE (Pages 35-39):
   - Item number
   - Description of issue
   - Action to be taken
   - Responsible party
   - Due date

5. RISK ASSESSMENT (Page 34):
   - Site-level risks (Yes/No)
   - CRA-level risks (Yes/No)
   - Impact levels
   - Narrative summary

6. OVERALL ASSESSMENT:
   - Site quality rating (Excellent/Good/Adequate/Needs Improvement/Poor)
   - Top 3-5 key concerns
   - Top 3-5 key strengths

Return structured JSON ONLY. No additional text.
"""
            }
        ]
    )

    # Parse LLM response to Pydantic model
    extracted_data = message.content[0].text
    report = MOVReport.model_validate_json(extracted_data)

    # Add metadata
    report.extraction_timestamp = datetime.now()
    report.llm_model = "claude-3-5-sonnet-20241022"

    return report


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF while preserving structure."""
    with pdfplumber.open(pdf_path) as pdf:
        # Extract with layout preservation
        pages_text = []
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text(layout=True)
            pages_text.append(f"--- PAGE {i} ---\n{text}\n")

        return "\n".join(pages_text)


# === Validation (Simplified) ===

def validate_extracted_report(report: MOVReport) -> dict:
    """
    Light validation since LLM handles most consistency checks.
    Focus on business rules and data quality.
    """

    issues = []

    # Completeness check
    if not report.action_items:
        issues.append("WARNING: No action items found (unusual)")

    if len(report.question_responses) < 70:
        issues.append(f"WARNING: Only {len(report.question_responses)} questions extracted (expected 76+)")

    # Business rule: recruitment math
    stats = report.recruitment_stats
    expected_total = stats.randomized_enrolled + stats.screen_failures
    if abs(stats.screened - expected_total) > 2:  # Allow small discrepancy
        issues.append(f"ALERT: Recruitment math inconsistent (Screened: {stats.screened} vs Sum: {expected_total})")

    # Date validation
    try:
        start = datetime.strptime(report.visit_start_date, "%Y-%m-%d")
        end = datetime.strptime(report.visit_end_date, "%Y-%m-%d")
        if end < start:
            issues.append("ERROR: Visit end date before start date")
    except ValueError:
        issues.append("ERROR: Invalid date format")

    # Risk flagging
    if report.risk_assessment.site_level_risks_identified:
        issues.append("ALERT: Site-level risks identified - review required")

    return {
        "valid": len([i for i in issues if i.startswith("ERROR")]) == 0,
        "issues": issues,
        "completeness_score": len(report.question_responses) / 76,
        "data_quality": "High" if len(issues) <= 2 else "Medium" if len(issues) <= 5 else "Low"
    }


# === Main Pipeline (Drastically Simplified) ===

def process_mov_report(pdf_path: str) -> dict:
    """
    Complete pipeline: PDF → LLM extraction → Validation → Output

    This is the ENTIRE extraction pipeline in one function.
    Compare to 500+ lines in hybrid approach.
    """

    print(f"Processing: {pdf_path}")

    # Step 1: LLM extraction (single call)
    report = extract_mov_report_llm_first(pdf_path)
    print(f"✓ Extracted {len(report.question_responses)} questions, {len(report.action_items)} action items")

    # Step 2: Validation
    validation = validate_extracted_report(report)
    print(f"✓ Validation: {validation['data_quality']} quality")

    if validation['issues']:
        print("Issues found:")
        for issue in validation['issues']:
            print(f"  - {issue}")

    # Step 3: Output to Excel
    update_excel_tracker(report, "references/Anthos_ABRS_Global_Deployment_Tracker.xlsx")
    print(f"✓ Updated Excel tracker")

    # Step 4: Generate analytics
    generate_dashboard_data(report)
    print(f"✓ Updated dashboard")

    return {
        "report": report,
        "validation": validation,
        "status": "success" if validation['valid'] else "needs_review"
    }


# === Excel Output (Unchanged) ===

def update_excel_tracker(report: MOVReport, excel_path: str):
    """Update Excel tracker with extracted data."""
    from openpyxl import load_workbook

    wb = load_workbook(excel_path)
    ws = wb["All Visits"]
    next_row = ws.max_row + 1

    # Map extracted data to Excel columns
    ws[f"A{next_row}"] = report.protocol_number
    ws[f"B{next_row}"] = report.site_info.site_number
    ws[f"C{next_row}"] = report.site_info.institution
    ws[f"D{next_row}"] = report.site_info.pi_first_name
    ws[f"E{next_row}"] = report.site_info.pi_last_name
    ws[f"F{next_row}"] = report.site_info.city
    ws[f"H{next_row}"] = report.site_info.country
    ws[f"I{next_row}"] = report.site_info.cra_name
    ws[f"K{next_row}"] = report.site_info.anthos_staff
    ws[f"L{next_row}"] = report.visit_type
    ws[f"M{next_row}"] = "Completed"
    ws[f"O{next_row}"] = report.visit_start_date
    ws[f"P{next_row}"] = report.visit_end_date

    # Quality metrics from questions
    sdv_q = next((q for q in report.question_responses if "discrepancies" in q.question_text.lower()), None)
    ws[f"W{next_row}"] = sdv_q.answer if sdv_q else "NR"

    # Comments
    ws[f"AF{next_row}"] = f"Quality: {report.overall_site_quality}. Concerns: {', '.join(report.key_concerns[:3])}"

    wb.save(excel_path)
```

---

## 3. Cost Comparison

### **Token Usage Estimation**

**Input:**
- 41-page MOV report ≈ 40,000 tokens (with layout preservation)
- System prompt + schema ≈ 2,000 tokens
- **Total input: 42,000 tokens**

**Output:**
- Structured JSON response ≈ 6,000 tokens (all questions, action items, summaries)
- **Total output: 6,000 tokens**

### **Cost Per Report (Claude 3.5 Sonnet)**

| Model | Input Cost | Output Cost | Total Cost |
|-------|------------|-------------|------------|
| Claude 3.5 Sonnet | 42,000 × $3/MTok = $0.126 | 6,000 × $15/MTok = $0.090 | **$0.22/report** |
| Claude 3 Haiku (cheaper) | 42,000 × $0.25/MTok = $0.011 | 6,000 × $1.25/MTok = $0.008 | **$0.02/report** |
| GPT-4 Turbo | 42,000 × $10/MTok = $0.42 | 6,000 × $30/MTok = $0.18 | **$0.60/report** |
| GPT-4o (newer) | 42,000 × $2.50/MTok = $0.105 | 6,000 × $10/MTok = $0.06 | **$0.17/report** |

**Annual LLM Cost (10 reports/month):**
- Claude 3.5 Sonnet: $0.22 × 10 × 12 = **$26/year**
- Claude 3 Haiku: $0.02 × 10 × 12 = **$2.40/year**
- GPT-4o: $0.17 × 10 × 12 = **$20/year**

**With 100 reports/month (scaled):**
- Claude 3.5 Sonnet: **$264/year**
- Claude 3 Haiku: **$24/year**

---

## 4. Revised Cost-Benefit Analysis

### **Development Costs (LLM-First)**

| Phase | Hybrid Approach | LLM-First Approach | Savings |
|-------|----------------|-------------------|---------|
| **Phase 1: POC** | $15K-$25K | $8K-$12K | -40% |
| **Phase 2: MVP** | $40K-$60K | $20K-$30K | -50% |
| **Phase 3: Production** | $30K-$50K | $15K-$25K | -50% |
| **Total Development** | $85K-$135K | **$43K-$67K** | **-49%** |

**Why 50% cheaper?**
- No complex regex libraries to build/maintain
- No template detection logic
- No multi-pathway extraction merge logic
- Simpler codebase (500 lines → 200 lines)
- Faster development iterations
- Less testing surface area

### **Annual Operating Costs (LLM-First)**

| Item | Hybrid Approach | LLM-First Approach | Change |
|------|----------------|-------------------|--------|
| LLM API costs | $2,400/year | $26-$264/year | **-89% to -99%** |
| Infrastructure | $3,600/year | $1,800/year | -50% (simpler) |
| Database | $1,200/year | $1,200/year | Same |
| Maintenance (20%) | $17K-$27K | $8.6K-$13.4K | -50% |
| **Total Operating** | $24.2K-$34.2K | **$11.6K-$16.6K** | **-52%** |

### **Net ROI (LLM-First)**

| Metric | Year 1 | Year 2 | Year 3 | Year 5 |
|--------|--------|--------|--------|--------|
| **Costs** | | | | |
| Development | $43K-$67K | $0 | $0 | $0 |
| Operating | $11.6K-$16.6K | $11.6K-$16.6K | $11.6K-$16.6K | $11.6K-$16.6K |
| **Total Costs** | **$54.6K-$83.6K** | **$11.6K-$16.6K** | **$11.6K-$16.6K** | **$11.6K-$16.6K** |
| | | | | |
| **Benefits** | | | | |
| Labor savings | $14.4K | $14.4K | $14.4K | $14.4K |
| Error reduction | $0.9K | $0.9K | $0.9K | $0.9K |
| Faster insights | $10K | $10K | $10K | $10K |
| **Total Benefits** | **$25.3K** | **$25.3K** | **$25.3K** | **$25.3K** |
| | | | | |
| **Net Benefit (Annual)** | -$29.3K to -$58.3K | +$8.7K to +$13.7K | +$8.7K to +$13.7K | +$8.7K to +$13.7K |
| **Cumulative** | -$29.3K to -$58.3K | -$20.6K to -$44.6K | -$11.9K to -$30.9K | +$13.9K to +$10.5K |
| **Break-Even** | N/A | **Year 2-3** | **Year 2-3** | ✓ Profitable |

**New Break-Even: Year 2-3** (vs. Year 4-6 with hybrid approach)

---

## 5. Key Advantages of LLM-First

### **Technical Benefits**

1. **Simpler Architecture**
   - Single extraction pathway (no deterministic/LLM merge)
   - 60% less code to maintain
   - Easier to debug (one extraction method)
   - Faster to iterate and improve

2. **Better Handling of Format Variations**
   - No brittle regex patterns that break on layout changes
   - Natural language understanding handles varied phrasings
   - Works across protocol versions without rewriting rules
   - Handles scanned/poor-quality PDFs better (with vision models)

3. **Richer Extraction**
   - Can extract nuanced information (e.g., sentiment, risk levels)
   - Summarizes narrative responses automatically
   - Identifies key concerns/strengths without rules
   - Contextual understanding (e.g., "adequate" in context)

4. **Self-Documenting**
   - Extraction prompt serves as documentation
   - Clear what LLM is being asked to extract
   - Easy for non-programmers to understand

### **Operational Benefits**

1. **Faster Time-to-Market**
   - POC in 2-3 weeks (vs. 4-6 weeks)
   - MVP in 6-8 weeks (vs. 8-12 weeks)
   - Production in 10-14 weeks (vs. 16-20 weeks)
   - **Total: 10-14 weeks vs. 16-20 weeks** (30% faster)

2. **Lower Maintenance Burden**
   - Protocol changes → Update prompt (not regex patterns)
   - LLM improvements → Better extraction over time (no code changes)
   - Less technical debt accumulation

3. **Easier Scaling**
   - Add new protocols → Modify prompt template
   - Add new fields → Update Pydantic model + prompt
   - No complex extraction logic to extend

### **Business Benefits**

1. **50% Lower Development Cost**
   - $43K-$67K vs. $85K-$135K
   - Break-even in Year 2-3 (vs. Year 4-6)

2. **Negligible LLM Costs**
   - $26-$264/year for LLM API (vs. thousands for compute)
   - Scales sublinearly (batch processing, caching)

3. **Higher Accuracy Potential**
   - Modern LLMs (Claude 3.5 Sonnet, GPT-4) excel at structured extraction
   - Can achieve 90-95% accuracy on well-formatted documents
   - Continuous improvement as LLMs get better

---

## 6. Potential Concerns & Mitigations

### **Concern 1: LLM Hallucination**

**Risk:** LLM invents data that doesn't exist in report

**Mitigation:**
- Use `temperature=0` for deterministic extraction
- Explicit instruction: "For missing data, use null rather than guessing"
- Request evidence spans: LLM must cite text it extracted from
- Validation layer checks for impossible values (e.g., negative patient counts)
- Human spot-checks on 5-10% of reports initially

**Reality Check:** Modern LLMs (GPT-4, Claude 3.5) with structured output are very reliable for extraction tasks. Hallucination is minimal with proper prompting.

### **Concern 2: LLM API Reliability**

**Risk:** API downtime or rate limits

**Mitigation:**
- Use enterprise SLA (99.9% uptime for Azure OpenAI)
- Implement retry logic with exponential backoff
- Fallback to alternative provider (GPT-4o → Claude 3.5)
- Queue reports during outages, process when API recovers
- Cache extracted reports (don't re-extract same report)

### **Concern 3: Cost Variability**

**Risk:** LLM costs increase if token usage spikes

**Mitigation:**
- Monitor token usage per report (alert if >50K tokens)
- Use cheaper models for batch processing (Claude Haiku: $0.02/report)
- Implement caching for repeated extractions
- Budget ceiling: Even 100 reports/month = $264/year max

### **Concern 4: Data Privacy**

**Risk:** Sending clinical trial data to third-party LLM API

**Mitigation:**
- Use **Azure OpenAI** (HIPAA-compliant, BAA available)
- Data residency controls (keep data in EU/US regions)
- Zero data retention policy (API doesn't train on your data)
- OR: Self-hosted LLM (Llama 3.1 405B, Claude in AWS Bedrock)
- Encrypt data in transit (TLS) and at rest

**Note:** Azure OpenAI is specifically designed for regulated industries and is HIPAA/GDPR compliant.

### **Concern 5: Loss of Determinism**

**Risk:** LLM may extract differently each time

**Mitigation:**
- Use `temperature=0` for fully deterministic behavior
- Schema validation ensures consistent structure
- Track extraction version (prompt + model version)
- A/B test: Run same report through LLM 3x, compare outputs
- If critical fields vary, flag for human review

---

## 7. Recommended LLM-First Stack

### **Primary Recommendation: Claude 3.5 Sonnet (via Anthropic API or AWS Bedrock)**

**Why Claude 3.5 Sonnet?**
- Excellent at structured extraction tasks
- 200K context window (entire 41-page report + schema)
- Vision capabilities (can process PDF images if needed)
- Strong instruction following
- Affordable ($3/$15 per MTok)
- Available on AWS Bedrock (BAA for HIPAA compliance)

**Alternative:** Claude 3 Haiku for cost optimization
- 10x cheaper ($0.25/$1.25 per MTok)
- Still excellent accuracy for structured data
- Use for batch processing or non-critical reports

### **Fallback: GPT-4o (via Azure OpenAI)**

**Why GPT-4o?**
- Multimodal (text + vision)
- Azure OpenAI = HIPAA compliant, enterprise SLA
- BAA available for healthcare/clinical trials
- Similar pricing to Claude ($2.50/$10 per MTok)
- Microsoft support and integration with Azure ecosystem

### **Self-Hosted Option: Llama 3.1 405B**

**When to consider:**
- Extreme data sensitivity (no external API calls)
- Very high volume (>1000 reports/month)
- Long-term cost optimization

**Trade-offs:**
- Upfront infrastructure cost ($10K-$50K for GPU servers)
- More complex deployment
- Need ML engineering expertise
- May have lower accuracy than Claude/GPT-4 initially

---

## 8. Revised Implementation Timeline

### **Phase 1: POC (2-3 weeks) - $8K-$12K**

**Week 1:**
- Set up Anthropic API / Azure OpenAI account
- Extract 5 sample MOV reports to text
- Write basic Pydantic models
- Create initial extraction prompt

**Week 2:**
- Run LLM extraction on 5 reports
- Compare extracted data vs. ground truth (manual)
- Calculate accuracy metrics
- Refine prompt based on errors

**Week 3:**
- Test on 10 additional reports
- Document accuracy (target: ≥85%)
- Present results to stakeholders
- Get approval for MVP phase

**Deliverables:**
- Extraction script (100 lines of code)
- Accuracy report with metrics
- Cost estimate for production

---

### **Phase 2: MVP (6-8 weeks) - $20K-$30K**

**Weeks 4-5: Core Pipeline**
- Build end-to-end pipeline (PDF → LLM → validation → Excel)
- Implement Pydantic validation rules
- Create Excel update function
- Add error handling and logging

**Weeks 6-7: Review Interface**
- Simple web UI for human review (Streamlit)
- Display extracted data + original PDF side-by-side
- Approve/Edit/Reject workflow
- Save validated data to database

**Weeks 8-9: Testing & Refinement**
- Process 20 real reports
- Measure accuracy and review rate
- Refine prompt and validation rules
- User acceptance testing

**Week 10:**
- Documentation and training
- Deploy to staging environment
- Parallel run with manual process

**Deliverables:**
- Production-ready extraction pipeline
- Web UI for review
- PostgreSQL database schema
- Excel export functionality
- User documentation

---

### **Phase 3: Production (6-8 weeks) - $15K-$25K**

**Weeks 11-12: Orchestration**
- Set up Prefect/Airflow workflow
- Schedule daily report processing
- Email notifications for new reports

**Weeks 13-14: Dashboard**
- Power BI connection to database
- OR: Build Plotly Dash web dashboard
- Real-time metrics and visualizations

**Weeks 15-16: Monitoring & Ops**
- Set up monitoring (Sentry, DataDog)
- Alert system for errors
- Backup and disaster recovery
- Performance optimization

**Weeks 17-18:**
- Production deployment
- Handoff to operations team
- 2 weeks of monitored operation

**Deliverables:**
- Fully automated production system
- Dashboard for stakeholders
- Operational runbooks
- Monitoring and alerting

---

**Total Timeline: 10-14 weeks** (vs. 16-20 weeks for hybrid approach)

---

## 9. Updated Recommendations

### **Go with LLM-First if:**

✅ You want faster time-to-market (10-14 weeks vs. 16-20 weeks)
✅ You want lower development cost ($43K-$67K vs. $85K-$135K)
✅ You want simpler, maintainable code (200 lines vs. 500+)
✅ You expect report formats to evolve over time
✅ You value faster break-even (Year 2-3 vs. Year 4-6)
✅ Modern LLMs (Claude 3.5, GPT-4o) meet your accuracy needs (≥90%)
✅ You can use enterprise LLM API (Azure OpenAI, AWS Bedrock) for compliance

### **Stick with Hybrid if:**

❌ You need 99.9%+ extraction accuracy (deterministic > LLM)
❌ LLM API costs are prohibitive (but they're <$300/year even at 100 reports/month)
❌ You cannot use external APIs (but self-hosted LLMs are an option)
❌ You have very high volume (>10,000 reports/month) where $0.22/report adds up
❌ Your reports have extremely consistent structure (regex is faster)

---

## 10. Final Recommendation

### **Go LLM-First**

**Reasoning:**
1. **50% cost reduction** in development ($43K-$67K vs. $85K-$135K)
2. **30% faster delivery** (10-14 weeks vs. 16-20 weeks)
3. **Negligible LLM costs** ($26-$264/year for 10-100 reports/month)
4. **Simpler architecture** (200 lines of code vs. 500+)
5. **Break-even in Year 2-3** (vs. Year 4-6)
6. **Modern LLMs are excellent** at structured extraction (Claude 3.5 Sonnet, GPT-4o)
7. **Easier to maintain** and extend over time
8. **More resilient** to format changes

**Key Success Factor:** Use enterprise-grade LLM API (Azure OpenAI or AWS Bedrock) for HIPAA compliance and reliability.

**Fallback Strategy:** If LLM accuracy is insufficient after POC (unlikely), you can always add deterministic preprocessing as a hybrid, but start LLM-first and add complexity only if needed.

---

## Code Comparison: Hybrid vs. LLM-First

### **Hybrid Approach (500+ lines)**

```python
# Complex regex patterns
SITE_NUMBER_PATTERN = r"Site Number:\s*(\d{6})"
PI_NAME_PATTERN = r"Principal Investigator:\s*Dr\.\s*([A-Z][a-z]+)\s+([A-Z][a-z\s]+)"
DATE_PATTERN = r"(\d{1,2})\/([A-Za-z]+)\/(\d{4})"

# Template detection
def detect_template_version(text):
    if "Protocol ANT-007" in text:
        return "ANT-007_v1"
    elif "Protocol ANT-008" in text:
        return "ANT-008_v1"
    # ... 50 more lines

# Question extraction with checkbox detection
def extract_question_17(pdf_page):
    # Find Question 17
    pattern = r"17\.\s+Is the Site Delegation Log.*?☒Yes|☐Yes.*?☐No|☒No"
    # ... 30 more lines of parsing logic

# ... repeat for 76 questions
# ... 200+ lines of regex patterns
# ... 100+ lines of merge logic (deterministic + LLM)
```

### **LLM-First Approach (200 lines)**

```python
# Single extraction function
def extract_mov_report(pdf_text: str) -> MOVReport:
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{
            "role": "user",
            "content": f"Extract structured data from this MOV report:\n\n{pdf_text}\n\nReturn JSON matching this schema: {schema}"
        }]
    )
    return MOVReport.model_validate_json(response.content[0].text)

# That's it. 10 lines vs. 500+.
```

**Complexity Reduction: 96%**

---

**Conclusion:** With modern LLMs like Claude 3.5 Sonnet or GPT-4o, the LLM-first approach is superior in almost every dimension: cost, speed, simplicity, and maintainability. The only scenario where hybrid makes sense is if you need deterministic 99.9%+ accuracy, but even then, start LLM-first and add deterministic components only where absolutely necessary.
