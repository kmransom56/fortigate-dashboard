""
Configuration settings for the FastAPI application.
"""
from pydantic import BaseSettings, Field, AnyHttpUrl
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import os
import sys

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Network Device MCP Server"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Application settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # FortiManager settings
    FMG_IP: Optional[str] = None
    FMG_USERNAME: Optional[str] = None
    FMG_PASSWORD: Optional[str] = None
    FMG_VERIFY_SSL: bool = False
    
    # Meraki settings
    MERAKI_API_KEY: Optional[str] = None
    MERAKI_ORG_ID: Optional[str] = None
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./network_devices.db"
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Initialize settings
settings = Settings()

# Update CORS origins
if settings.BACKEND_CORS_ORIGINS:
    if isinstance(settings.BACKEND_CORS_ORIGINS, str) and not settings.BACKEND_CORS_ORIGINS.startswith("["):
        settings.BACKEND_CORS_ORIGINS = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
