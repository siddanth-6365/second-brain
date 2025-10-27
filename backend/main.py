"""Main FastAPI application for Second Brain"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime as dt
from pydantic import BaseModel

from backend.config import settings
from backend.models import Document, Memory, SearchQuery, SearchResult
from backend.services import (
    get_ingestion_service,
    get_search_service,
    get_graph_store,
    get_vector_store
)

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Groq client (optional)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq package not installed. Chat functionality will be limited.")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Unified Memory Management Platform - Turn messy inputs into intelligent, connected memories"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": dt.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    graph_store = get_graph_store()
    stats = graph_store.get_graph_stats()
    
    return {
        "status": "healthy",
        "timestamp": dt.utcnow().isoformat(),
        "stats": stats
    }


# Document endpoints
@app.post("/documents/ingest", response_model=Document)
async def ingest_document(
    request: dict,
    background_tasks: BackgroundTasks = None
):
    """
    Ingest a document and create memories.
    
    The document will be chunked, embedded, and indexed into the knowledge graph.
    """
    try:
        content = request.get("content", "").strip()
        title = request.get("title", "").strip()
        source = request.get("source", "").strip()
        
        # Validation
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Max content size: 1MB
        if len(content) > 1_000_000:
            raise HTTPException(
                status_code=413,
                detail="Content too large. Maximum size is 1MB"
            )
        
        # Min content size: 10 characters
        if len(content) < 10:
            raise HTTPException(
                status_code=400,
                detail="Content too short. Minimum 10 characters required"
            )
        
        # Validate title length
        if title and len(title) > 500:
            raise HTTPException(
                status_code=400,
                detail="Title too long. Maximum 500 characters"
            )
        
        # Validate source length
        if source and len(source) > 500:
            raise HTTPException(
                status_code=400,
                detail="Source too long. Maximum 500 characters"
            )
        
        ingestion_service = get_ingestion_service()
        document = await ingestion_service.ingest_text(
            text=content,
            title=title if title else None,
            source=source if source else None
        )
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/memories", response_model=List[Memory])
async def get_document_memories(document_id: str, skip: int = 0, limit: int = 50):
    """
    Get memories created from a document with pagination.
    
    Args:
        document_id: Document ID
        skip: Number of results to skip (default: 0)
        limit: Maximum results to return (default: 50, max: 500)
    """
    if limit > 500:
        limit = 500
    if skip < 0:
        skip = 0
    
    graph_store = get_graph_store()
    memories = [
        m for m in graph_store.get_all_memories()
        if m.document_id == document_id
    ]
    
    if not memories:
        raise HTTPException(status_code=404, detail="Document not found or has no memories")
    
    # Apply pagination
    return memories[skip:skip + limit]


# Memory endpoints
@app.post("/memories/search", response_model=List[SearchResult])
async def search_memories(query: SearchQuery):
    """
    Search for memories using semantic and keyword search.
    
    Returns relevant memories ranked by relevance score.
    """
    try:
        search_service = get_search_service()
        results = await search_service.search(query)
        return results
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}", response_model=Memory)
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    search_service = get_search_service()
    memory = await search_service.get_memory_by_id(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory


@app.get("/memories/{memory_id}/related", response_model=List[Memory])
async def get_related_memories(memory_id: str, max_depth: int = 2):
    """Get memories related to a specific memory"""
    search_service = get_search_service()
    
    # First check if memory exists
    memory = await search_service.get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Get related memories
    related = await search_service.get_related_memories(memory_id, max_depth=max_depth)
    return related


@app.get("/memories/timeline/{topic}", response_model=List[Memory])
async def get_memory_timeline(topic: str):
    """Get timeline of memories about a topic, showing evolution of information"""
    search_service = get_search_service()
    timeline = await search_service.get_memory_timeline(topic)
    return timeline


# Graph endpoints
@app.get("/graph/export")
async def export_graph():
    """
    Export the entire knowledge graph for visualization.
    
    Returns nodes (memories) and edges (relationships).
    """
    graph_store = get_graph_store()
    return graph_store.export_graph()


@app.get("/graph/stats")
async def get_graph_stats():
    """Get statistics about the knowledge graph"""
    graph_store = get_graph_store()
    return graph_store.get_graph_stats()


# Chat endpoint models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str
    max_memories: int = 5
    model: str = "openai/gpt-oss-20b"  # Groq model
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are my favorite foods?",
                "max_memories": 5,
                "model": "openai/gpt-oss-20b"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    question: str
    answer: str
    memories_used: List[str]  # Memory IDs used for context
    memory_count: int
    model: str


# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_with_memories(request: ChatRequest):
    """
    Chat with your memories using Groq LLM.
    
    This endpoint:
    1. Retrieves relevant memories based on your question
    2. Uses those memories as context
    3. Generates a response using Groq's LLM
    
    Requires GROQ_API_KEY in environment variables.
    """
    if not GROQ_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Groq package not installed. Install with: pip install groq"
        )
    
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. Please set it in your .env file"
        )
    
    try:
        # Step 1: Search for relevant memories
        search_service = get_search_service()
        search_query = SearchQuery(
            query=request.question,
            limit=request.max_memories,
            only_latest=True
        )
        
        search_results = await search_service.search(search_query)
        
        if not search_results:
            return ChatResponse(
                question=request.question,
                answer="I don't have any memories related to your question yet. Try adding some documents first!",
                memories_used=[],
                memory_count=0,
                model=request.model
            )
        
        # Step 2: Build context from memories
        context_parts = []
        memory_ids = []
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"Memory {i} (relevance: {result.score:.2f}):")
            context_parts.append(result.memory.content)
            context_parts.append("")  # Empty line
            memory_ids.append(result.memory.id)
        
        context = "\n".join(context_parts)
        
        # Step 3: Create prompt for Groq
        system_prompt = """You are a helpful AI assistant with access to the user's personal memories. 
Your job is to answer questions based on the provided memories.

Guidelines:
- Answer based ONLY on the information in the provided memories
- If the memories don't contain enough information, say so
- Be conversational and friendly
- Reference specific memories when relevant
- If you detect contradictions or updates in memories, mention the most recent information"""

        user_prompt = f"""Based on these memories:

{context}

Question: {request.question}

Please provide a helpful answer based on the memories above."""

        # Step 4: Call Groq API
        client = Groq(api_key=settings.groq_api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=request.model,
            temperature=0.7,
            max_tokens=1024,
        )
        
        answer = chat_completion.choices[0].message.content
        
        return ChatResponse(
            question=request.question,
            answer=answer,
            memories_used=memory_ids,
            memory_count=len(memory_ids),
            model=request.model
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@app.delete("/admin/clear-all")
async def clear_all_data():
    """
    ⚠️ DANGER: Clear all memories and relationships from the system.
    
    This will:
    - Delete all memories from vector store
    - Clear the knowledge graph
    - Reset all data
    
    This operation cannot be undone!
    """
    try:
        vector_store = get_vector_store()
        graph_store = get_graph_store()
        
        # Delete the Qdrant collection and recreate it
        vector_store.client.delete_collection(
            collection_name=settings.qdrant_collection_name
        )
        
        # Reinitialize the collection
        vector_store._initialize_collection()
        
        # Clear the graph store by creating a new instance
        graph_store.graph.clear()
        graph_store.memories.clear()
        graph_store.relationships.clear()
        
        logger.info("All data cleared successfully")
        
        return {
            "status": "success",
            "message": "All memories and relationships have been cleared",
            "timestamp": dt.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


