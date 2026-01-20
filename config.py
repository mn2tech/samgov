"""
Configuration management for AI Contract Finder.
Loads settings from environment variables with sensible defaults.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


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
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(default=None, env="GOOGLE_REDIRECT_URI")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
