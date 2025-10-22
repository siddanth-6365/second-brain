"""Memory model - represents intelligent knowledge units"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class RelationshipType(str, Enum):
    """Types of relationships between memories"""
    
    UPDATES = "updates"  # New information contradicts/updates existing knowledge
    EXTENDS = "extends"  # New information adds to existing knowledge
    DERIVES = "derives"  # System infers connection from patterns
    SIMILAR = "similar"  # Semantically similar memories


class MemoryRelationship(BaseModel):
    """Represents a relationship between two memories"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Relationship
    from_memory_id: str
    to_memory_id: str
    relationship_type: RelationshipType
    
    # Strength and confidence
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    similarity_score: Optional[float] = None
    
    # Context
    reason: Optional[str] = None  # Why this relationship was created
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_memory_id": "abc-123",
                "to_memory_id": "def-456",
                "relationship_type": "updates",
                "confidence": 0.95,
                "reason": "New role supersedes previous role"
            }
        }


class Memory(BaseModel):
    """
    Memory represents an intelligent knowledge unit.
    Created from documents, enriched with embeddings and relationships.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    content: str
    summary: Optional[str] = None  # Brief summary of the memory
    
    # Source
    document_id: str  # Parent document
    chunk_index: int = 0  # Position in the original document
    
    # Embedding
    embedding: Optional[List[float]] = None  # Vector representation
    embedding_model: Optional[str] = None
    
    # Graph properties
    is_latest: bool = True  # False if this memory has been updated
    is_active: bool = True  # False if memory has expired
    
    # Metadata
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)  # Named entities extracted
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None  # Last time this memory was retrieved
    expires_at: Optional[datetime] = None  # When this memory should expire
    
    # Relationships
    relationships: List[MemoryRelationship] = Field(default_factory=list)
    
    # Statistics
    access_count: int = 0  # How many times this memory has been retrieved
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "You work at Supermemory as the CMO",
                "document_id": "doc-123",
                "chunk_index": 0,
                "is_latest": True,
                "keywords": ["work", "Supermemory", "CMO"]
            }
        }

