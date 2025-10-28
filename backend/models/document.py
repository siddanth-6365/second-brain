"""Document model - represents raw input to the system"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class DocumentStatus(str, Enum):
    """Processing status of a document"""
    QUEUED = "queued"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    DONE = "done"
    FAILED = "failed"


class Document(BaseModel):
    """
    Document represents raw input to the system.
    It gets transformed into one or more Memories.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    content: str
    title: Optional[str] = None
    source: Optional[str] = None  # URL, file path, or source identifier
    
    # Metadata
    document_type: str = "text"  # text, pdf, web, email, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing
    status: DocumentStatus = DocumentStatus.QUEUED
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Relationships
    memory_ids: List[str] = Field(default_factory=list)  # IDs of memories created from this document
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Dhravya is the founder of Supermemory, an AI-focused company.",
                "title": "About Supermemory",
                "source": "notes.txt",
                "document_type": "text"
            }
        }

