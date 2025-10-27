"""Configuration management for Second Brain"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Second Brain"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API Keys (optional for advanced features)
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    
    # Qdrant Vector Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "memories"
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # for all-MiniLM-L6-v2
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Relationship Detection
    similarity_threshold_update: float = 0.70  # High similarity = likely an update
    similarity_threshold_extend: float = 0.60  # Medium similarity = likely extends
    
    # Memory Tiering Configuration
    hot_memory_age_days: int = 30  # Memories younger than this are "hot"
    hot_memory_access_threshold: int = 5  # Memories accessed more than this are "hot"
    cold_storage_enabled: bool = True  # Enable hot/cold tiering
    
    # Time Decay Configuration
    time_decay_half_life_days: int = 90  # Days for score to decay to 50%
    
    # CORS Configuration
    allowed_origins: Optional[str] = None  # Comma-separated list of allowed origins
    
    # Rate Limiting (Optional)
    rate_limit_requests: Optional[int] = None  # Max requests per period
    rate_limit_period: Optional[int] = None  # Period in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()

