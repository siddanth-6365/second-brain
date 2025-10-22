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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

