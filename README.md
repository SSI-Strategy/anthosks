# AnthosKS - MOV Report Extraction System

Automated extraction of structured data from Monitoring Oversight Visit (MOV) clinical trial reports using Azure OpenAI.

## Overview

AnthosKS is a local Python application that extracts structured data from 41-page MOV reports using Azure OpenAI's `gpt-5-chat-deployment`. The system uses Azure CLI delegated credentials for authentication (no API keys required), maintains clean separation of concerns, and is architected for future cloud deployment.

### Key Features

- **LLM-First Extraction**: Uses Azure OpenAI GPT-5 for intelligent extraction
- **Structured Output**: Extracts 76+ questions, action items, risk assessments, and quality metrics
- **Validation Layer**: Business rule validation ensures data quality
- **Local Storage**: SQLite database and local file storage for development
- **Web UI**: Streamlit interface for report review and approval
- **Cloud-Ready**: Architecture supports future Azure deployment with minimal changes

## Architecture

```
┌─────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT                              │
├─────────────────────────────────────────────────┤
│  • Azure CLI credentials (az login)             │
│  • Local file storage (data/input, data/output) │
│  • SQLite database (data/reports.db)            │
│  • Streamlit UI (localhost:8501)                │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Azure CLI installed and configured
- Access to Azure OpenAI resource (`oai-shared-se-01-p`)

## Installation

### 1. Clone the Repository

```bash
cd AnthosKS
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI settings:

```env
AZURE_OPENAI_ENDPOINT=https://swedencentral.api.cognitive.microsoft.com/
AZURE_OPENAI_DEPLOYMENT=gpt-5-chat-deployment
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### 5. Authenticate with Azure

```bash
az login
az account show
```

### 6. Test Azure Connection

```bash
python scripts/test_azure_connection.py
```

You should see:
```
✅ ALL TESTS PASSED
```

## Usage

### Processing a Single Report (CLI)

```bash
python scripts/process_single_report.py data/input/your_report.pdf
```

Output:
- Structured JSON in `data/output/`
- Database record in `data/reports.db`
- Console summary with validation results

### Web Interface (Streamlit)

```bash
streamlit run src/ui/streamlit_app.py
```

Then open http://localhost:8501 in your browser.

Features:
- **Upload**: Upload and process MOV reports
- **Review**: Review extracted data with side-by-side view
- **Reports**: Browse all processed reports
- **Analytics**: View trends and patterns (coming soon)

## Project Structure

```
AnthosKS/
├── data/                         # Local data storage (git-ignored)
│   ├── input/                   # Upload MOV PDFs here
│   ├── output/                  # Extracted JSON outputs
│   ├── reports.db               # SQLite database
│   └── cache/                   # LLM response cache
│
├── references/                   # Reference materials
│   ├── suggestions.md           # Extraction strategy
│   └── sample_reports/          # Sample MOV PDFs
│
├── src/                          # Application source code
│   ├── config.py                # Configuration management
│   ├── models.py                # Pydantic data models
│   ├── extraction/
│   │   ├── pdf_parser.py       # PDF text extraction
│   │   ├── llm_extractor.py    # Azure OpenAI integration
│   │   └── validator.py        # Business rule validation
│   ├── storage/
│   │   ├── base.py             # Storage interface
│   │   └── local_storage.py    # Local file system
│   ├── database/
│   │   ├── base.py             # Database interface
│   │   └── sqlite_db.py        # SQLite implementation
│   └── ui/
│       └── streamlit_app.py    # Review interface
│
├── scripts/                      # Utility scripts
│   ├── test_azure_connection.py # Verify Azure OpenAI access
│   └── process_single_report.py # CLI tool for processing
│
└── tests/                        # Unit and integration tests
    ├── test_extraction.py
    └── test_models.py
```

## Data Models

The system extracts the following structured data:

### MOV Report Structure
- **Site Information**: Site number, country, PI, institution
- **Visit Details**: Visit type, dates, ANTHOS staff, CRA
- **Recruitment Statistics**: Screened, enrolled, completed, discontinued
- **Questions (76+)**: Question text, answer (Yes/No/N/A/NR), narrative, evidence
- **Action Items**: Description, responsible party, due date
- **Risk Assessment**: Site/CRA risks, impact levels, narrative
- **Quality Summary**: Overall rating, key concerns, key strengths

## Configuration

All configuration is managed via environment variables in `.env`:

### Azure OpenAI
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT`: Deployment name (default: gpt-5-chat-deployment)
- `AZURE_OPENAI_API_VERSION`: API version
- `AZURE_OPENAI_API_KEY`: (Optional) API key for authentication

### Storage
- `INPUT_PATH`: Input PDF directory (default: ./data/input)
- `OUTPUT_PATH`: Output JSON directory (default: ./data/output)
- `DATABASE_PATH`: SQLite database path (default: ./data/reports.db)
- `CACHE_PATH`: Cache directory (default: ./data/cache)

### Extraction
- `LLM_TEMPERATURE`: Temperature for LLM (default: 0.0)
- `LLM_MAX_TOKENS`: Max response tokens (default: 8000)
- `CONFIDENCE_THRESHOLD`: Confidence threshold for QC (default: 0.7)

## Testing

Run the test suite:

```bash
pytest tests/
```

Run specific tests:

```bash
pytest tests/test_models.py
pytest tests/test_extraction.py
```

## Cost Estimation

Per report processing (approximate):
- Input tokens: ~42,000
- Output tokens: ~6,000
- **Estimated cost**: $0.20-0.30 per report (based on GPT-5 pricing)

## Validation & Quality Control

The system includes comprehensive validation:

1. **Data Completeness**: Checks for minimum 70/85 questions extracted
2. **Recruitment Math**: Validates patient enrollment statistics
3. **Confidence Scoring**: Flags low-confidence extractions
4. **Business Rules**: Validates against clinical trial constraints
5. **Evidence Spans**: Includes text excerpts for manual QC

Quality scores: Excellent | Good | Fair | Needs Review | Poor

## Troubleshooting

### Azure Authentication Issues

If you see authentication errors:

```bash
# Re-authenticate with Azure
az login

# Verify credentials
az account show

# Check access to OpenAI resource
az cognitiveservices account show \
  --name oai-shared-se-01-p \
  --resource-group rg-shared_resources-se-01-p
```

### Missing Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### PDF Extraction Issues

- Ensure PDF is text-based (not scanned images)
- Check file size and page count with `pdfplumber`
- Review extraction logs for warnings

## Future Enhancements

### Cloud Deployment (Planned)
- Azure App Service or Container Apps
- Azure Blob Storage for PDFs
- Azure SQL Database
- Managed Identity authentication

### Analytics (Roadmap)
- Question answer distribution heatmaps
- Quality trends over time
- Action item categorization
- Risk pattern analysis

## Support

For issues or questions:
- Review PLAN.md for implementation details
- Check LLM_FIRST_APPROACH.md for extraction strategy
- Contact: johan.stromquist@ssistrategy.com

## License

Internal SSI Strategy project - All rights reserved
