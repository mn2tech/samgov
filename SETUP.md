# Setup Guide

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` File

Create a `.env` file in the project root with the following content:

```bash
# SAM.gov API Configuration
SAM_API_KEY=your_sam_gov_api_key_here
SAM_API_BASE_URL=https://api.sam.gov/opportunities/v2
# For Alpha/Testing: SAM_API_BASE_URL=https://api-alpha.sam.gov/opportunities/v2

# OpenAI Configuration (for AI classification and scoring)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Alternative: Local Ollama (if not using OpenAI)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama2

# Database Configuration
DATABASE_URL=sqlite:///./samgov_contracts.db
# For Postgres: DATABASE_URL=postgresql://user:password@localhost/samgov

# Application Settings
APP_NAME=AI Contract Finder
APP_VERSION=1.0.0
DEBUG=False

# Logging
LOG_LEVEL=INFO
```

### 3. Get API Keys

#### SAM.gov API Key
1. Visit [SAM.gov API Portal](https://open.gsa.gov/api/entity-api/)
2. Register for an API key
3. Add to `.env` as `SAM_API_KEY`

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account and get an API key
3. Add to `.env` as `OPENAI_API_KEY`

**OR** use local Ollama:
1. Install [Ollama](https://ollama.ai/)
2. Run: `ollama pull llama2`
3. Configure in `.env`:
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

### 4. Run the Application

#### Option A: Streamlit UI (Recommended)
```bash
streamlit run app.py
```

Or use the runner script:
```bash
python run.py --mode streamlit
```

#### Option B: FastAPI Backend
```bash
python run.py --mode api
```

Or directly:
```bash
uvicorn api:app --reload
```

### 5. Access the Application

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **FastAPI Health**: http://localhost:8000/health

## First-Time Usage

1. **Create a Capability Profile**
   - Open the sidebar in Streamlit UI
   - Enter company name
   - Fill in core domains, skills, NAICS, agencies
   - Click "Save Profile"

2. **Fetch Opportunities**
   - Click "🔍 Fetch Opportunities from SAM.gov"
   - Wait for AI classification to complete

3. **Score Opportunities**
   - Click "📊 Score Opportunities"
   - Review ranked results

4. **Export Results**
   - Click "📥 Export to CSV"
   - Download the file

## Troubleshooting

### SAM.gov API Issues
- Verify API key is correct
- Check API endpoint URL
- System will use mock data if API fails (for development)

### OpenAI API Issues
- Verify API key and quota
- Check model name (gpt-4-turbo-preview or gpt-3.5-turbo)
- Consider using local Ollama as alternative

### Database Issues
- SQLite database is created automatically
- For PostgreSQL, ensure database exists and connection string is correct
- Check file permissions for SQLite

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version (3.9+ required)

## Development Mode

For development with mock data (no API keys needed):

1. Comment out API key requirements in `.env`
2. System will automatically use rule-based classification and scoring
3. Mock opportunities will be used if SAM.gov API fails

## Production Deployment

1. Use PostgreSQL instead of SQLite
2. Set `DEBUG=False` in `.env`
3. Configure proper CORS in `api.py`
4. Use environment-specific API keys
5. Enable HTTPS
6. Set up monitoring and logging
7. Consider containerization (Docker)

---

**Ready to find your next federal IT contract!** 🚀
