# 🏛️ AI-Powered IT Contract Finder (SAM.gov)

A production-ready AI-powered web application that finds, classifies, and scores federal IT, AI, Data, Cloud, and Cybersecurity opportunities from SAM.gov.

## 🎯 Features

### Core Capabilities

- **🔍 SAM.gov Integration**: Automated ingestion of federal IT opportunities
- **🤖 AI Classification**: Intelligent classification by domain, complexity, and project type
- **📊 AI Fit Scoring**: Weighted scoring system matching opportunities to company capabilities
- **📋 Capability Profiles**: Create and manage company capability profiles
- **🎨 Modern UI**: Streamlit-based interface with search, filter, and detailed views
- **💾 Data Persistence**: SQLite/Postgres database for opportunities and scores
- **📥 Export**: CSV export for further analysis

### Target Opportunity Domains

The system intelligently identifies and prioritizes opportunities in:

- **🧠 AI & Advanced Analytics**: AI, ML, Generative AI, LLMs, RAG, NLP, Computer Vision
- **📊 Data & Analytics**: Data Engineering, Warehousing, BI, SAS, Python, R, ETL/ELT
- **☁️ Cloud & Modernization**: Cloud Migration, AWS/Azure/GCP, Containers, Kubernetes, IaC
- **🔐 Cybersecurity**: Zero Trust, FedRAMP, FISMA, RMF, IAM, SOC/SIEM
- **🧑‍💻 Software Engineering**: Full-stack, APIs, Microservices, CI/CD, DevSecOps
- **🏛️ Federal IT Support**: IT Consulting, Operations, PMO, ITSM, Systems Integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  (Search, Filter, Ranked Table, AI Reasoning Panels)        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Profile    │  │   SAM.gov    │  │     AI       │     │
│  │   Manager    │  │  Ingestion   │  │  Engines     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                   │             │
│         │                 │                   │             │
│  ┌──────▼─────────────────▼───────────────────▼──────────┐ │
│  │              AI Classifier & Scorer                    │ │
│  │  (OpenAI GPT-4 / Local Ollama)                        │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Database Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Opportunities│  │    Scores    │  │   Profiles   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              SQLite / PostgreSQL Database                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

1. **SAM.gov Ingestion** (`sam_ingestion.py`)
   - Fetches opportunities from SAM.gov API
   - Filters by IT-focused NAICS codes and keywords
   - Handles API errors gracefully with mock data fallback

2. **AI Classifier** (`ai_classifier.py`)
   - Classifies opportunities by domain (AI, Data, Cloud, Cyber, etc.)
   - Determines complexity (Low/Medium/High)
   - Identifies project type (Modernization, Operations, Greenfield, Legacy)
   - Uses OpenAI GPT-4 or local Ollama

3. **AI Scoring Engine** (`ai_scoring.py`)
   - Computes weighted fit scores (0-100)
   - Evaluates 6 criteria: Domain, NAICS, Skills, Agency, Contract Type, Strategic Value
   - Recommends: BID, TEAM/SUB, or IGNORE
   - Provides plain-English explanations and risk factors

4. **Capability Profile Manager** (`profile_manager.py`)
   - Creates and manages company capability profiles
   - Stores domains, skills, NAICS, agencies, certifications
   - Supports role preferences (Prime, Subcontractor, Either)

5. **Database Layer** (`database.py`)
   - SQLAlchemy ORM models
   - Stores opportunities, scores, and profiles
   - Supports SQLite (default) and PostgreSQL

6. **Streamlit UI** (`app.py`)
   - Interactive search and filter interface
   - Ranked opportunity table with color-coded scores
   - Expandable AI reasoning panels
   - CSV export functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- SAM.gov API key ([Get one here](https://open.gsa.gov/api/entity-api/))
- OpenAI API key (or local Ollama setup)

### Installation

1. **Clone the repository**
   ```bash
   cd samgov
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy .env.example to .env
   cp .env.example .env
   
   # Edit .env with your API keys
   SAM_API_KEY=your_sam_gov_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the UI**
   - Open your browser to `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Create Capability Profile

1. Open the sidebar
2. Enter your company name
3. Select core domains (AI, Data, Cloud, etc.)
4. Enter technical skills (comma-separated)
5. Add NAICS codes
6. Specify preferred agencies
7. Add certifications (SDVOSB, 8(a), etc.)
8. Choose role preference (Prime/Subcontractor/Either)
9. Click "Save Profile"

### Step 2: Fetch Opportunities

1. Set "Days Ahead" filter (7, 14, 30, 60, 90 days)
2. Optionally filter by domain or agency
3. Click "🔍 Fetch Opportunities from SAM.gov"
4. Wait for AI classification to complete

### Step 3: Score Opportunities

1. Click "📊 Score Opportunities"
2. AI will score each opportunity against your profile
3. Opportunities are ranked by fit score

### Step 4: Review & Export

1. Review ranked opportunities in the table
2. Click on an opportunity to see detailed AI reasoning
3. Export to CSV for further analysis

## 🔧 Configuration

### Environment Variables

```bash
# SAM.gov API
SAM_API_KEY=your_key_here
SAM_API_BASE_URL=https://api.sam.gov/prod/opportunities/v2

# OpenAI (for AI classification/scoring)
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Alternative: Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Database
DATABASE_URL=sqlite:///./samgov_contracts.db
# Or PostgreSQL: DATABASE_URL=postgresql://user:pass@localhost/samgov

# Application
APP_NAME=AI Contract Finder
DEBUG=False
LOG_LEVEL=INFO
```

### Scoring Weights

The fit score uses weighted criteria (configurable in `ai_scoring.py`):

| Category | Weight |
|----------|--------|
| Domain Match | 30% |
| NAICS Match | 20% |
| Technical Skill Match | 20% |
| Agency Alignment | 10% |
| Contract Type Fit | 10% |
| Strategic Value | 10% |

## 🏗️ Project Structure

```
samgov/
├── app.py                 # Streamlit UI (main entry point)
├── config.py              # Configuration management
├── models.py              # Pydantic data models
├── sam_ingestion.py       # SAM.gov API integration
├── ai_classifier.py       # AI classification engine
├── ai_scoring.py          # AI fit scoring engine
├── profile_manager.py     # Capability profile manager
├── database.py            # Database models and storage
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔐 Security Best Practices

- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Use environment variables for all secrets
- ✅ Rotate API keys regularly
- ✅ Use least-privilege database access
- ✅ Enable HTTPS in production

## 🚧 Phase 2 Features (Future)

- 📧 Auto email alerts for high-fit contracts
- 📊 Capture planning summaries
- 🤝 Prime/Sub matchmaking
- 📈 Historical award analysis
- 🔗 CRM integration (Salesforce, HubSpot)
- 🏢 Multi-tenant SaaS support
- 🔄 Automated daily opportunity scans
- 📱 Mobile-responsive UI

## 🐛 Troubleshooting

### SAM.gov API Errors

- **Issue**: API returns 401/403 errors
  - **Solution**: Verify `SAM_API_KEY` in `.env` is correct

- **Issue**: No opportunities returned
  - **Solution**: Check API endpoint URL, try mock data mode for testing

### AI Classification Issues

- **Issue**: OpenAI API errors
  - **Solution**: Verify `OPENAI_API_KEY`, check API quota, or use local Ollama

- **Issue**: Classification seems inaccurate
  - **Solution**: Review opportunity descriptions, adjust prompts in `ai_classifier.py`

### Database Issues

- **Issue**: SQLite database locked
  - **Solution**: Ensure only one instance is running, or switch to PostgreSQL

## 📝 License

This project is provided as-is for federal IT contracting use.

## 🤝 Contributing

This is a production-ready system designed for extensibility. Key extension points:

1. **Custom AI Prompts**: Modify prompts in `ai_classifier.py` and `ai_scoring.py`
2. **Additional Filters**: Add filters in `sam_ingestion.py`
3. **New Scoring Criteria**: Extend `FitScoreBreakdown` in `models.py`
4. **UI Enhancements**: Customize `app.py` Streamlit components

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs (set `LOG_LEVEL=DEBUG` for detailed logs)
3. Verify API keys and configuration

## 🎓 Understanding the Fit Score

The fit score (0-100) indicates how well an opportunity matches your company:

- **🟢 70-100**: Strong fit - **BID** recommended
- **🟡 50-69**: Moderate fit - **TEAM/SUB** recommended
- **🔴 0-49**: Weak fit - **IGNORE** recommended

The score considers:
- Domain alignment with your core capabilities
- NAICS code matches
- Technical skill requirements
- Agency preferences
- Contract type and set-aside compatibility
- Strategic value for growth

---

**Built for federal IT contractors who think like capture managers + AI architects.** 🚀
