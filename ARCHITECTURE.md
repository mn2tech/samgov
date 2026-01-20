# System Architecture

## Overview

The AI Contract Finder is a modular, production-ready system designed for extensibility into a multi-tenant SaaS platform.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Streamlit Web App (app.py)                  │  │
│  │  • Search & Filter Panel                                 │  │
│  │  • Ranked Opportunity Table                              │  │
│  │  • AI Reasoning Panels                                   │  │
│  │  • Capability Profile Manager                            │  │
│  │  • CSV Export                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          OR                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI REST API (api.py)                    │  │
│  │  • /opportunities/fetch                                   │  │
│  │  • /opportunities/score                                   │  │
│  │  • /profiles                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                    Application Core                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SAM.gov Ingestion (sam_ingestion.py)         │  │
│  │  • API Integration                                        │  │
│  │  • IT-focused Filtering (NAICS, Keywords)                │  │
│  │  • Error Handling & Mock Data Fallback                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI Classifier (ai_classifier.py)             │  │
│  │  • Domain Classification (AI/Data/Cloud/Cyber/etc.)      │  │
│  │  • Complexity Assessment (Low/Medium/High)               │  │
│  │  • Project Type (Modernization/Operations/Greenfield)    │  │
│  │  • OpenAI GPT-4 or Local Ollama                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI Scoring Engine (ai_scoring.py)             │  │
│  │  • Weighted Fit Score (0-100)                            │  │
│  │  • 6 Scoring Criteria                                    │  │
│  │  • Recommendation (BID/TEAM_SUB/IGNORE)                  │  │
│  │  • Plain-English Explanations                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Profile Manager (profile_manager.py)              │  │
│  │  • Create/Update Capability Profiles                     │  │
│  │  • Domain, Skills, NAICS, Agencies, Certifications       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                    Data Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Database (database.py)                       │  │
│  │  • SQLAlchemy ORM                                         │  │
│  │  • Opportunity Storage                                    │  │
│  │  • Score Storage                                          │  │
│  │  • Profile Storage                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│              SQLite (Default) or PostgreSQL                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Opportunity Ingestion Flow

```
SAM.gov API
    │
    ▼
SAM Ingestion Module
    │
    ├─► Filter by IT NAICS (541511, 541512, etc.)
    ├─► Filter by IT Keywords (AI, Data, Cloud, Cyber)
    └─► Parse & Normalize
    │
    ▼
Opportunity Models (Pydantic)
    │
    ▼
AI Classifier
    │
    ├─► Classify Domain
    ├─► Assess Complexity
    └─► Identify Project Type
    │
    ▼
Database Storage
```

### 2. Scoring Flow

```
Opportunity + Capability Profile
    │
    ▼
AI Scoring Engine
    │
    ├─► Domain Match (30%)
    ├─► NAICS Match (20%)
    ├─► Technical Skill Match (20%)
    ├─► Agency Alignment (10%)
    ├─► Contract Type Fit (10%)
    └─► Strategic Value (10%)
    │
    ▼
Weighted Fit Score (0-100)
    │
    ├─► ≥70: BID
    ├─► 50-69: TEAM/SUB
    └─► <50: IGNORE
    │
    ▼
OpportunityScore Model
    │
    ▼
Database Storage
```

## Component Details

### SAM.gov Ingestion (`sam_ingestion.py`)

**Responsibilities:**
- Fetch opportunities from SAM.gov API
- Filter by IT-focused NAICS codes
- Filter by IT/AI/Data/Cloud/Cyber keywords
- Parse and normalize opportunity data
- Handle API errors gracefully

**Key Features:**
- Async HTTP client (httpx)
- Mock data fallback for development
- Flexible date range filtering
- NAICS and keyword filtering

### AI Classifier (`ai_classifier.py`)

**Responsibilities:**
- Classify opportunities by primary domain
- Identify secondary domains
- Assess technical complexity
- Determine project type (Modernization vs Operations)
- Identify legacy systems

**AI Provider Support:**
- OpenAI GPT-4 (primary)
- Local Ollama (alternative)
- Rule-based fallback (no AI)

**Classification Output:**
- Primary Domain: AI, Data, Cloud, Cybersecurity, IT Operations, Software, Modernization, Other
- Secondary Domains: Multi-label classification
- Complexity: Low, Medium, High
- Project Type: Modernization, Operations, Greenfield, Legacy

### AI Scoring Engine (`ai_scoring.py`)

**Responsibilities:**
- Compute weighted fit scores
- Evaluate 6 scoring criteria
- Generate recommendations
- Provide plain-English explanations
- Identify risk factors

**Scoring Weights:**
- Domain Match: 30%
- NAICS Match: 20%
- Technical Skill Match: 20%
- Agency Alignment: 10%
- Contract Type Fit: 10%
- Strategic Value: 10%

**Recommendation Logic:**
- 70-100: BID (Strong fit)
- 50-69: TEAM/SUB (Moderate fit)
- 0-49: IGNORE (Weak fit)

### Profile Manager (`profile_manager.py`)

**Responsibilities:**
- Create capability profiles
- Update existing profiles
- Retrieve profiles by company name
- Default profile templates

**Profile Structure:**
- Company name
- Core domains (list)
- Technical skills (list)
- NAICS codes (list)
- Preferred agencies (list)
- Certifications (list)
- Role preference (Prime/Subcontractor/Either)

### Database Layer (`database.py`)

**Responsibilities:**
- SQLAlchemy ORM models
- Opportunity persistence
- Score persistence
- Profile persistence
- Query and filtering

**Database Models:**
- `OpportunityDB`: Opportunities with AI classification
- `OpportunityScoreDB`: Fit scores and recommendations
- `CapabilityProfileDB`: Company capability profiles

**Supported Databases:**
- SQLite (default, development)
- PostgreSQL (production, multi-tenant)

## Configuration Management

### Environment Variables (`config.py`)

Uses Pydantic Settings for type-safe configuration:

- **SAM.gov API**: API key, base URL
- **AI Provider**: OpenAI or Ollama configuration
- **Database**: Connection string (SQLite/Postgres)
- **Application**: Name, version, debug, logging

## Extensibility Points

### Phase 2 Features (Designed For)

1. **Multi-Tenant SaaS**
   - Add tenant_id to all models
   - Tenant isolation in database queries
   - Per-tenant API keys

2. **Email Alerts**
   - Background task scheduler (Celery)
   - Email service integration (SendGrid, SES)
   - Configurable alert thresholds

3. **Prime/Sub Matchmaking**
   - Prime contractor database
   - Subcontractor capability matching
   - Automated introductions

4. **Historical Analysis**
   - Award data ingestion
   - Win rate analysis
   - Competitive intelligence

5. **CRM Integration**
   - Salesforce API integration
   - HubSpot integration
   - Opportunity sync

## Security Considerations

- ✅ Environment variables for secrets
- ✅ No hardcoded credentials
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Input validation (Pydantic models)
- ✅ CORS configuration for API
- ✅ HTTPS in production (recommended)

## Performance Considerations

- **Async Operations**: SAM.gov API calls use async/await
- **Batch Processing**: Classify and score multiple opportunities
- **Database Indexing**: Indexed fields for fast queries
- **Caching**: Opportunity data cached in database
- **Rate Limiting**: Consider for OpenAI API calls

## Deployment Options

### Option 1: Streamlit Cloud
- Deploy `app.py` directly
- Configure environment variables
- Automatic HTTPS

### Option 2: Docker + Cloud
- Containerize application
- Deploy to AWS/Azure/GCP
- Use managed PostgreSQL

### Option 3: FastAPI + React
- Use `api.py` as backend
- Build React frontend
- Deploy separately

## Monitoring & Logging

- **Logging**: Python logging module (configurable level)
- **Error Handling**: Graceful degradation with fallbacks
- **Health Checks**: `/health` endpoint in FastAPI
- **Metrics**: Consider adding Prometheus metrics

---

**Architecture designed for production use and future SaaS expansion.**
