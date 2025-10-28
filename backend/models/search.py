"""Search models for querying memories"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .memory import Memory


class SearchQuery(BaseModel):
    """Query for searching memories"""
    
    query: str
    limit: int = Field(default=10, ge=1, le=100)
    
    # Filters
    keywords: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    
    # Search options
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)  # Weight of semantic vs keyword search
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0)  # Minimum similarity score
    include_inactive: bool = False  # Include expired/inactive memories
    only_latest: bool = True  # Only return latest versions of updated memories
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is my role at Supermemory?",
                "limit": 5,
                "only_latest": True
            }
        }


class SearchResult(BaseModel):
    """Result from memory search"""
    
    memory: Memory
    score: float = Field(ge=0.0, le=1.0)  # Relevance score
    explanation: Optional[str] = None  # Why this was returned
    related_memories: List[str] = Field(default_factory=list)  # IDs of related memories
    
    class Config:
        json_schema_extra = {
            "example": {
                "memory": {"id": "mem-123", "content": "You work at Supermemory as CMO"},
                "score": 0.95,
                "explanation": "Direct match to query about role"
            }
        }

