# ANALYTICS.md

## Overview

This document defines the analytics capabilities for the AnthosKS MOV Report system. The analytics layer provides multi-dimensional analysis of site monitoring data with drill-down capabilities and executive-ready dashboard views.

---

## Data Model Summary

### Core Entities

**MOV Report** (Primary Entity)
- Protocol Number
- Site Information (Site Number, Country, Institution, PI, CRA, Clinical Oversight Manager)
- Visit Dates (Start, End) and Visit Type (SIV MOV, IMV MOV, COV MOV)
- Recruitment Statistics (Screened, Failures, Randomized, Discontinued, Completed)
- 85 Question Responses (Question Number, Text, Answer [Yes/No/N/A/NR], Sentiment, Narrative Summary)
- Action Items (Description, Owner, Due Date, Status)
- Risk Assessment (Site-level, CRA-level, Country-level, Study-level impacts)
- Overall Site Quality (Excellent/Good/Adequate/Needs Improvement/Poor)
- Key Concerns and Strengths
- Data Quality Metrics (Completeness Score, Review Flags)

**Question Response** (Detail Entity)
- Answer Types: Yes, No, N/A, NR (Not Reported)
- Sentiment: Positive (compliant), Negative (issues), Neutral, Unknown
- Evidence and Confidence Score

---

## Analytics Dimensions

### 1. Time Dimensions
- **Visit Date** (primary temporal axis)
  - Day, Week, Month, Quarter, Year
  - Rolling periods (Last 30/60/90/180 days, Last 12 months)
  - Year-over-Year comparisons

- **Extraction Timestamp** (system tracking)
  - Processing time analysis
  - Recent additions/updates

### 2. Geographic Dimensions
- **Country** (primary geographic dimension)
  - Country-level aggregations
  - Regional groupings (configurable)
  - Multi-country comparisons

### 3. Organizational Dimensions
- **Site** (site_number)
  - Individual site performance
  - Site comparison and ranking

- **Clinical Oversight Manager** (anthos_staff)
  - Manager portfolio view
  - Performance across sites under management

- **Clinical Research Associate** (cra_name)
  - CRA performance tracking
  - Site coverage per CRA

### 4. Clinical Dimensions
- **Protocol Number**
  - Study-specific analytics
  - Cross-protocol comparisons

- **Visit Type** (SIV MOV, IMV MOV, COV MOV)
  - Visit type comparisons
  - Temporal progression (SIV → IMV → COV)

### 5. Quality Dimensions
- **Overall Site Quality** (Excellent → Poor)
  - Quality distribution
  - Quality trends over time

- **Data Completeness Score** (0-1)
  - Extraction quality tracking
  - Confidence metrics

---

## Key Metrics and KPIs

### Compliance Metrics

**1. Overall Compliance Rate**
- Formula: `(Yes answers) / (Total non-NR answers) × 100`
- Definition: Percentage of compliant responses across all questions
- Drillable by: Time, Country, Site, Question Category

**2. Non-Compliance Rate**
- Formula: `(No answers) / (Total non-NR answers) × 100`
- Definition: Percentage of non-compliant responses
- Alerts: Threshold-based warnings (e.g., >15%)

**3. Data Completeness Rate**
- Formula: `(Non-NR answers) / 85 × 100`
- Definition: Percentage of questions with actual data
- Drillable by: Site, Visit Type, CRA

**4. Question-Specific Compliance**
- Per-question compliance rates (85 questions)
- Trend analysis per question over time
- Comparison across sites/countries

### Recruitment Metrics

**5. Enrollment Rate**
- Formula: `(Randomized) / (Screened) × 100`
- Definition: Percentage of screened patients enrolled
- Benchmark: Track against study targets

**6. Screen Failure Rate**
- Formula: `(Screen Failures) / (Screened) × 100`
- Definition: Percentage of screened patients not enrolled

**7. Early Discontinuation Rate**
- Formula: `(Early Discontinued) / (Randomized) × 100`
- Definition: Patient dropout rate post-enrollment

**8. Study Completion Rate**
- Formula: `(Completed Study) / (Randomized) × 100`
- Definition: Percentage of enrolled patients completing study

### Risk Metrics

**9. Site Risk Score**
- Composite score based on:
  - Non-compliance rate (40% weight)
  - Action items count (20% weight)
  - Risk assessment flags (30% weight)
  - Data quality concerns (10% weight)
- Range: 0-100 (higher = more risk)

**10. Action Item Load**
- Total open action items per site
- Overdue action items percentage
- Action item closure rate

**11. Critical Findings Rate**
- Questions with "Negative" sentiment per visit
- Trend over time per site
- Category breakdown

### Quality Metrics

**12. Site Quality Score**
- Categorical: Excellent (5), Good (4), Adequate (3), Needs Improvement (2), Poor (1)
- Distribution across portfolio
- Trend over time per site

**13. Data Quality Score**
- Based on `completeness_score` field
- Percentage of reports requiring review
- Evidence confidence average

---

## Analytics Views

### Executive Dashboard (PowerPoint-Ready)

**Purpose**: High-level overview for leadership presentations

**Components**:

1. **KPI Scorecard** (Top Banner)
   - Total Sites Monitored
   - Average Compliance Rate (with trend arrow)
   - Average Site Quality Score
   - High-Risk Sites Count
   - Time Period Selector (configurable: Last 30/60/90 days, QTD, YTD)

2. **Compliance Trends** (Line Chart)
   - X-axis: Time (monthly or weekly)
   - Y-axis: Compliance Rate %
   - Multiple lines: Overall, By Visit Type, By Region
   - Annotations for significant drops

3. **Geographic Heatmap** (World/Regional Map)
   - Color-coded by average compliance rate
   - Size bubbles by number of sites
   - Click to drill into country

4. **Site Quality Distribution** (Donut Chart)
   - Segments: Excellent, Good, Adequate, Needs Improvement, Poor
   - Center: Total site count
   - Percentage labels on each segment

5. **Top Issues Dashboard** (Horizontal Bar Chart)
   - Top 10 questions with highest non-compliance rate
   - Color-coded by severity
   - Count of affected sites

6. **Risk Alerts** (Status Table)
   - High-risk sites (Site Risk Score > 70)
   - Columns: Site Number, Country, Risk Score, Last Visit Date, Primary Concerns
   - Sortable and filterable

**Export Options**:
- PNG/PDF for embedding in PowerPoint
- High-resolution (300 DPI)
- Configurable date range in header
- Auto-generated timestamp

---

### Compliance Analytics View

**Purpose**: Deep-dive into compliance patterns

**Sections**:

1. **Compliance Overview**
   - Overall compliance rate with trend
   - Compliance by answer type (Yes/No/N/A/NR) - stacked bar
   - Compliance by visit type - grouped bar chart
   - Filters: Date range, Country, Protocol, Visit Type

2. **Question Analysis** (Interactive Table)
   - Columns: Question #, Question Text, Compliance Rate, Total Responses, Trend
   - Sortable by any column
   - Click question to see detailed breakdown
   - Color-coded compliance rate (Red <70%, Yellow 70-85%, Green >85%)

3. **Question Deep-Dive** (Drill-Down Panel)
   - Triggered by clicking question in table
   - Shows:
     - Answer distribution pie chart (Yes/No/N/A/NR)
     - Trend over time (line chart)
     - Top non-compliant sites (list with details)
     - Common narrative themes (word cloud or bullet points)
     - Sentiment distribution

4. **Site Comparison Matrix** (Heatmap)
   - Rows: Sites
   - Columns: Question numbers (1-85)
   - Cell color: Green (Yes), Red (No), Yellow (N/A), Gray (NR)
   - Click cell to see full question response detail
   - Filter by question category

5. **Compliance Trends** (Multi-Line Chart)
   - X-axis: Time
   - Y-axis: Compliance Rate %
   - Lines: Selectable (Overall, By Country, By Site, By Question Category)
   - Show/hide individual lines
   - Zoom and pan

**Drillable Filters**:
- Date Range (slider or date picker)
- Country (multi-select dropdown)
- Protocol Number (dropdown)
- Visit Type (checkboxes)
- Site Quality Level (checkboxes)

---

### Site Performance View

**Purpose**: Monitor individual site and portfolio performance

**Sections**:

1. **Site Portfolio Summary**
   - Total sites count
   - Sites by quality tier (bar chart)
   - Sites by country (treemap)
   - Average compliance rate per site (distribution histogram)

2. **Site Leaderboard** (Sortable Table)
   - Columns: Rank, Site Number, Country, Institution, Latest Compliance Rate,
     Average Quality Score, Last Visit Date, Trend
   - Top performers highlighted (green)
   - Bottom performers highlighted (red)
   - Click site to open detailed profile

3. **Site Detail Profile** (Drill-Down Panel)
   - Site Header: Site Number, Country, Institution, PI Name
   - Visit History Timeline
   - Compliance Trend Chart (line chart over visits)
   - Quality Score Trend (line chart)
   - Recent Action Items (table with status)
   - Key Concerns and Strengths (bullet lists)
   - Recruitment Stats Overview (table)
   - Question Response Detail (full 85-question table with sentiment)

4. **CRA/Manager Performance** (Grouped Table)
   - Group by: Clinical Oversight Manager or CRA
   - Aggregated metrics:
     - Number of sites managed
     - Average compliance rate across sites
     - Average site quality score
     - Total action items
     - High-risk sites count
   - Expand to see individual sites under each manager/CRA

5. **Recruitment Performance** (Multi-Metric Dashboard)
   - Enrollment Rate by Site (bar chart)
   - Screen Failure Rate by Site (bar chart)
   - Completion Rate by Site (bar chart)
   - Scatter plot: Enrollment Rate vs. Compliance Rate (identify patterns)
   - Filters: Country, Protocol, Date Range

---

### Risk & Action Management View

**Purpose**: Identify and track risks and corrective actions

**Sections**:

1. **Risk Dashboard**
   - Risk Heat Matrix (2x2):
     - X-axis: Site-level risk (Low/High)
     - Y-axis: Study-level risk impact (Low/High)
     - Quadrants color-coded
     - Sites plotted as points (size = action item count)
   - Risk Score Distribution (histogram)
   - High-Risk Sites Alert Box (list with quick actions)

2. **Risk Trend Analysis**
   - Line chart: Average Risk Score over time
   - Stacked area: Sites by risk category (Low/Medium/High) over time
   - Risk flag counts: Site-level, CRA-level, Country-level, Study-level

3. **Action Item Tracker** (Interactive Table)
   - Columns: Site, Item #, Description, Owner (Responsible), Due Date, Status, Days Overdue
   - Filters: Status (Open/Closed), Overdue (Yes/No), Site, Date Range
   - Sortable by due date, overdue days
   - Color-coded: Green (on-time), Yellow (due soon), Red (overdue)
   - Inline status update (if user has permissions)

4. **Action Item Analytics**
   - Total open action items (KPI card)
   - Overdue percentage (KPI card with trend)
   - Average time to closure (KPI card)
   - Action items by site (bar chart)
   - Action items by responsible person (bar chart)
   - Action item aging analysis (histogram: 0-30, 31-60, 61-90, 90+ days)

5. **Critical Findings Feed** (Scrollable List)
   - Recent critical findings (key_finding field populated)
   - Shows: Site, Question, Finding, Date, Sentiment
   - Click to see full context
   - Filter by date range, site, sentiment

---

### Data Quality & Operations View

**Purpose**: Monitor extraction quality and system operations

**Sections**:

1. **Data Quality Dashboard**
   - Average Completeness Score (KPI card with trend)
   - Reports Requiring Review (KPI card with count)
   - Average Confidence Score (KPI card)
   - Low-Quality Alerts (reports with completeness < 0.7)

2. **Extraction Performance** (Table)
   - Columns: Source File, Extraction Date, Completeness Score, Questions Extracted,
     Requires Review, Review Reason
   - Filter: Date Range, Completeness Threshold, Review Status
   - Click file to see full report
   - Export to Excel for QC team

3. **Question Coverage Analysis** (Heatmap)
   - Rows: Reports (by date or site)
   - Columns: Question Numbers (1-85)
   - Cell color: Green (extracted), Red (NR), Gray (missing)
   - Identify systematic extraction gaps

4. **Confidence Distribution** (Histogram)
   - X-axis: Confidence Score (0-1)
   - Y-axis: Count of question responses
   - Overlay: Threshold line (e.g., 0.7)
   - Highlight low-confidence responses

5. **Processing Log** (Timeline View)
   - Chronological list of processed files
   - Shows: File name, Processing time, Success/Fail status, Errors
   - Filter by date range, status
   - Useful for troubleshooting

---

### Trend & Prediction View

**Purpose**: Identify patterns and forecast future trends

**Sections**:

1. **Compliance Trend Forecasting**
   - Historical compliance rate (line chart)
   - Projected compliance rate (dashed line with confidence interval)
   - Seasonality detection
   - Annotation: Expected compliance rate in next quarter

2. **Question Hotspots Over Time** (Animated Heatmap)
   - X-axis: Time periods
   - Y-axis: Question Numbers (1-85)
   - Color: Non-compliance rate
   - Play button to animate through time
   - Identify emerging problem areas

3. **Site Trajectory Analysis** (Scatter Plot with Vectors)
   - X-axis: Compliance Rate
   - Y-axis: Site Quality Score
   - Points: Sites
   - Vectors: Direction of change (improving/declining)
   - Quadrants: High-Quality/Low-Quality × High-Compliance/Low-Compliance

4. **Recruitment Trends** (Multi-Metric Time Series)
   - Enrollment rate trend
   - Screen failure rate trend
   - Completion rate trend
   - Stacked view or separate panels

5. **Anomaly Detection**
   - Table of anomalies detected:
     - Sudden compliance drops (>15% decrease from previous visit)
     - Unusual question response patterns (compared to historical)
     - Outlier sites (statistically different from peer group)
   - Each anomaly clickable for details

---

## Drillable Hierarchies

### Geographic Hierarchy
```
Global View
  ├─ Region (e.g., North America, Europe, APAC)
  │   ├─ Country
  │   │   ├─ Site
  │   │   │   ├─ Visit (by date)
  │   │   │   │   ├─ Question Responses (85 questions)
```

**Navigation**: Click any level to drill down, breadcrumb trail for navigation up

### Time Hierarchy
```
Year
  ├─ Quarter
  │   ├─ Month
  │   │   ├─ Week
  │   │   │   ├─ Day
```

**Navigation**: Date range picker with predefined options (Last 30/60/90 days, QTD, YTD, All Time)

### Question Hierarchy
```
All Questions (1-85)
  ├─ Category (if defined, e.g., Documentation, Data Quality, Safety)
  │   ├─ Individual Question
  │   │   ├─ Answer Distribution
  │   │   │   ├─ Site-Specific Responses
```

**Navigation**: Collapsible tree or tabbed interface

### Organizational Hierarchy
```
All Sites
  ├─ Clinical Oversight Manager
  │   ├─ CRA (if assigned)
  │   │   ├─ Sites
  │   │   │   ├─ Visits
```

**Navigation**: Expandable table with group headers

---

## Dashboard Configuration

### User Preferences
- **Default Time Range**: Last 90 days, QTD, YTD, All Time
- **Default View**: Executive Dashboard, Compliance, Site Performance, Risk
- **Favorite Filters**: Save filter combinations for quick access
- **Theme**: Light/Dark mode for visualizations

### Export Options
- **PowerPoint Export**:
  - Executive Dashboard → Single slide with all components
  - High-resolution images (300 DPI)
  - Includes date range and generation timestamp
  - Editable title and subtitle fields

- **Excel Export**:
  - Any table view → Excel workbook
  - Preserves filters and sorting
  - Multiple sheets for multi-dimensional data

- **PDF Report**:
  - Full analytics report with all sections
  - Configurable sections (select which views to include)
  - Auto-generated summary page

- **CSV Export**:
  - Raw data exports for further analysis
  - Respects current filters

### Refresh & Scheduling
- **Manual Refresh**: Button to reload latest data
- **Auto-Refresh**: Configurable interval (Off, 5 min, 15 min, 30 min, 1 hour)
- **Scheduled Reports**: Email delivery of dashboard PDFs (daily, weekly, monthly)

---

## Technical Implementation Considerations

### Data Aggregation Strategy
- **Pre-compute** common aggregations (daily/weekly):
  - Compliance rates by site/country/protocol
  - Question-level statistics
  - Risk scores
- **On-demand** computation for custom filters and drill-downs
- **Caching** for frequently accessed views (TTL: configurable)

### Performance Optimization
- **Database Indexes**:
  - `(site_number, visit_date)` - Primary lookup
  - `(country, visit_date)` - Geographic queries
  - `(protocol_number, visit_date)` - Protocol-specific queries
  - `(visit_date)` - Time-based filtering
  - `(completeness_score)` - Quality filtering

- **Materialized Views** (PostgreSQL):
  - `mv_compliance_by_site_month`: Pre-aggregated compliance per site per month
  - `mv_question_statistics`: Pre-aggregated per-question stats
  - `mv_site_risk_scores`: Pre-computed risk scores

- **Incremental Updates**: Only recompute metrics for new/changed reports

### API Endpoints (Proposed)

```
GET /api/analytics/kpi
  Query params: date_from, date_to, country, protocol, site_number
  Returns: JSON with all KPI metrics

GET /api/analytics/compliance/overview
  Query params: date_from, date_to, filters...
  Returns: Compliance rates, trends, distributions

GET /api/analytics/compliance/questions
  Query params: filters...
  Returns: Per-question compliance data

GET /api/analytics/compliance/questions/{question_number}
  Returns: Deep-dive data for single question

GET /api/analytics/sites
  Query params: filters...
  Returns: Site leaderboard and summary stats

GET /api/analytics/sites/{site_number}
  Returns: Full site profile with history

GET /api/analytics/risks
  Query params: filters...
  Returns: Risk scores, flags, heat matrix data

GET /api/analytics/action-items
  Query params: status, overdue, site_number, filters...
  Returns: Action item list with details

GET /api/analytics/data-quality
  Query params: filters...
  Returns: Data quality metrics and reports requiring review

GET /api/analytics/trends
  Query params: metric, date_from, date_to, grouping
  Returns: Time-series data for specified metric

GET /api/analytics/export/dashboard
  Query params: format (png|pdf), date_range, ...
  Returns: High-resolution dashboard export
```

### Frontend Visualization Libraries
- **Charting**: Recharts, Chart.js, or Plotly.js (for interactive drill-downs)
- **Tables**: AG Grid or TanStack Table (for large datasets with filtering/sorting)
- **Maps**: Leaflet.js or Mapbox GL (for geographic visualizations)
- **Dashboards**: React Grid Layout (for customizable dashboard layouts)

---

## Analytics Roadmap

### Phase 1: Foundation (MVP)
- Executive Dashboard with core KPIs
- Compliance Overview with question table
- Site Performance leaderboard
- Basic drill-down on questions
- PowerPoint-ready export

### Phase 2: Deep Analytics
- Full drill-down hierarchies (geo, time, org)
- Site Detail Profile view
- Risk Dashboard with heat matrix
- Action Item Tracker
- Data Quality monitoring

### Phase 3: Advanced Intelligence
- Trend forecasting
- Anomaly detection
- Sentiment analysis on narratives
- Theme clustering (ML-based)
- Predictive risk scoring

### Phase 4: Collaboration & Workflow
- Inline action item updates
- Commenting on findings
- Report sharing and permissions
- Scheduled report delivery
- Alert notifications (email/Slack) for critical findings

---

## Success Metrics for Analytics

1. **Adoption Rate**: % of users accessing analytics views weekly
2. **Time to Insight**: Average time from question to finding answer in analytics
3. **Export Usage**: Number of PowerPoint/PDF exports per week
4. **Drill-Down Depth**: Average number of drill-down actions per session
5. **Data Freshness**: Time lag between report extraction and analytics availability
6. **User Satisfaction**: Quarterly survey scores on analytics usefulness

---

## Glossary

- **Compliance Rate**: Percentage of "Yes" answers out of total answered questions (excluding NR)
- **Non-Compliance Rate**: Percentage of "No" answers out of total answered questions
- **Data Completeness**: Percentage of questions with non-NR responses (out of 85 total)
- **Site Risk Score**: Composite metric (0-100) indicating site risk level
- **Sentiment**: Auto-categorization of question responses (Positive/Negative/Neutral/Unknown)
- **NR (Not Reported)**: Question was not answered or data unavailable in source document
- **Evidence**: Text excerpt from source document supporting the extracted answer
- **Confidence**: Score (0-1) indicating extraction algorithm's confidence in the answer

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Owner**: Analytics Team
