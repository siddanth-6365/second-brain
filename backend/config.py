"""Configuration management for Second Brain"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


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
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_url: Optional[str] = Field(default=None, alias="QDRANT_URL")  # Use for Qdrant Cloud (https://...)
    qdrant_endpoint: Optional[str] = Field(default=None, alias="QDRANT_ENDPOINT")
    qdrant_cluster_id: Optional[str] = Field(default=None, alias="QDRANT_CLUSTER_ID")
    qdrant_use_https: bool = Field(default=False, alias="QDRANT_USE_HTTPS")
    qdrant_timeout: int = 10
    qdrant_relationship_collection_name: str = "memory_relationships"
    
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
    
    # Supabase Auth
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None  # Optional, for admin tasks
    supabase_jwt_secret: Optional[str] = None  # Optional, enables local JWT verification
    
    # CORS Configuration
    allowed_origins: Optional[str] = None  # Comma-separated list of allowed origins
    
    # Rate Limiting (Optional)
    rate_limit_requests: Optional[int] = None  # Max requests per period
    rate_limit_period: Optional[int] = None  # Period in seconds
    
    class Config:
        env_file = ENV_PATH
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()

