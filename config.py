"""
Configuration management for AI Contract Finder.
Loads settings from environment variables with sensible defaults.
Also supports Streamlit Cloud secrets via st.secrets.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# Try to import streamlit for secrets (only available in Streamlit context)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret from Streamlit Cloud secrets or environment variable.
    Priority: st.secrets > environment variable > default
    """
    # Try Streamlit Cloud secrets first
    if STREAMLIT_AVAILABLE and st is not None:
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass  # st.secrets might not be available in all contexts
    
    # Fallback to environment variable
    return os.getenv(key, default)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # SAM.gov API
    sam_api_key: Optional[str] = Field(default=None, env="SAM_API_KEY")
    sam_api_base_url: str = Field(
        default="https://api.sam.gov/opportunities/v2",
        env="SAM_API_BASE_URL"
    )
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Local Ollama (alternative to OpenAI)
    ollama_base_url: Optional[str] = Field(default=None, env="OLLAMA_BASE_URL")
    ollama_model: Optional[str] = Field(default="llama2", env="OLLAMA_MODEL")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./samgov_contracts.db",
        env="DATABASE_URL"
    )
    
    # Application
    app_name: str = Field(default="AI Contract Finder", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Google OAuth (for authentication)
    # These will be overridden by _get_secret() after initialization
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(default=None, env="GOOGLE_REDIRECT_URI")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Override with Streamlit secrets if available (for Streamlit Cloud)
if STREAMLIT_AVAILABLE and st is not None:
    try:
        if hasattr(st, 'secrets'):
            # Override Google OAuth settings from Streamlit secrets
            if 'GOOGLE_CLIENT_ID' in st.secrets:
                settings.google_client_id = st.secrets['GOOGLE_CLIENT_ID']
            if 'GOOGLE_CLIENT_SECRET' in st.secrets:
                settings.google_client_secret = st.secrets['GOOGLE_CLIENT_SECRET']
            if 'GOOGLE_REDIRECT_URI' in st.secrets:
                settings.google_redirect_uri = st.secrets['GOOGLE_REDIRECT_URI']
            
            # Override other secrets if available
            if 'SAM_API_KEY' in st.secrets:
                settings.sam_api_key = st.secrets['SAM_API_KEY']
            if 'OPENAI_API_KEY' in st.secrets:
                settings.openai_api_key = st.secrets['OPENAI_API_KEY']
    except Exception:
        pass  # st.secrets might not be available in all contexts
