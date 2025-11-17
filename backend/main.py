"""Main FastAPI application for Second Brain"""

from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime as dt
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel

from backend.config import settings
from backend.models import Document, Memory, SearchQuery, SearchResult
from backend.services import (
    get_ingestion_service,
    get_search_service,
    get_graph_store,
    get_vector_store,
    get_memory_tiering,
)
from backend.services.auth_service import AuthenticatedUser, get_current_user

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
    request: Request,
    background_tasks: BackgroundTasks = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Ingest a document (note, link, or file) and create memories.
    """
    try:
        payload, upload_file = await _parse_ingest_request(request)

        def _clean(value: Optional[str]) -> Optional[str]:
            if isinstance(value, str):
                value = value.strip()
                return value or None
            return value

        doc_type = (payload.get("type") or payload.get("doc_type") or "note").lower()
        title = _clean(payload.get("title") or payload.get("name"))
        description = _clean(payload.get("description") or payload.get("summary"))
        note_content = payload.get("content") or payload.get("text")
        link_url = _clean(payload.get("url") or payload.get("link"))
        source_override = _clean(payload.get("source"))

        if title and len(title) > 500:
            raise HTTPException(status_code=400, detail="Title too long. Maximum 500 characters")

        ingestion_service = get_ingestion_service()
        document = await ingestion_service.ingest_entry(
            user_id=current_user.id,
            entry_type=doc_type,
            title=title,
            description=description,
            note_content=note_content,
            link_url=link_url,
            upload_file=upload_file,
            explicit_source=source_override,
        )
        return document
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/memories", response_model=List[Memory])
async def get_document_memories(
    document_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
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
        m for m in graph_store.get_all_memories(user_id=current_user.id)
        if m.document_id == document_id
    ]
    
    if not memories:
        raise HTTPException(status_code=404, detail="Document not found or has no memories")
    
    # Apply pagination
    return memories[skip:skip + limit]


# Memory endpoints
@app.post("/memories/search", response_model=List[SearchResult])
async def search_memories(
    query: SearchQuery,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Search for memories using semantic and keyword search.
    
    Returns relevant memories ranked by relevance score.
    """
    try:
        search_service = get_search_service()
        results = await search_service.search(query, user_id=current_user.id)
        return results
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a specific memory by ID"""
    search_service = get_search_service()
    memory = await search_service.get_memory_by_id(memory_id, user_id=current_user.id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory


@app.get("/memories/{memory_id}/related", response_model=List[Memory])
async def get_related_memories(
    memory_id: str,
    max_depth: int = 2,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get memories related to a specific memory"""
    search_service = get_search_service()
    
    # First check if memory exists
    memory = await search_service.get_memory_by_id(memory_id, user_id=current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Get related memories
    related = await search_service.get_related_memories(memory_id, user_id=current_user.id, max_depth=max_depth)
    return related


@app.get("/memories/timeline/{topic}", response_model=List[Memory])
async def get_memory_timeline(
    topic: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get timeline of memories about a topic, showing evolution of information"""
    search_service = get_search_service()
    timeline = await search_service.get_memory_timeline(topic, user_id=current_user.id)
    return timeline


# Graph endpoints
@app.get("/graph/export")
async def export_graph(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Export the entire knowledge graph for visualization.
    
    Returns nodes (memories) and edges (relationships).
    """
    graph_store = get_graph_store()
    return graph_store.export_graph(user_id=current_user.id)


@app.get("/graph/stats")
async def get_graph_stats(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Get statistics about the knowledge graph"""
    graph_store = get_graph_store()
    return graph_store.get_graph_stats(user_id=current_user.id)


async def _parse_ingest_request(request: Request) -> Tuple[Dict[str, Any], Optional[UploadFile]]:
    """Support both JSON and multipart ingestion payloads."""
    content_type = (request.headers.get("content-type") or "").lower()
    upload_file: Optional[UploadFile] = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        payload: Dict[str, Any] = {}
        for key, value in form.multi_items():
            if isinstance(value, UploadFile):
                upload_file = value
            else:
                payload[key] = value
        return payload, upload_file

    try:
        data = await request.json()
        if isinstance(data, dict):
            return data, None
    except Exception:
        pass

    return {}, None


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
async def chat_with_memories(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
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
        
        search_results = await search_service.search(search_query, user_id=current_user.id)
        
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
async def clear_all_data(current_user: AuthenticatedUser = Depends(get_current_user)):
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
        memory_tiering = get_memory_tiering()
        
        # Delete vector embeddings for this user
        vector_store.delete_memories_by_user(current_user.id)
        
        # Remove graph data for this user
        removal_stats = graph_store.clear_user_data(current_user.id)
        memory_tiering.remove_memories(removal_stats.get("memory_ids", []))
        
        logger.info("Cleared data for user %s", current_user.id)
        
        return {
            "status": "success",
            "message": "All of your memories and relationships have been cleared",
            "memories_deleted": removal_stats.get("memories", 0),
            "relationships_deleted": removal_stats.get("relationships", 0),
            "timestamp": dt.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


