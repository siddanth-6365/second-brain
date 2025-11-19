from mcp.server.fastmcp import FastMCP
from services.ingestion_service import IngestionService
from services.search_service import SearchService
from services.graph_store import GraphStore
from services.memory_tiering import MemoryTieringService
from services.entity_service import EntityService
from services.embedding_service import EmbeddingService
from core.database import get_vector_store
from models.memory import Memory, IngestedDocument
from typing import List, Optional
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Second Brain")

# Helper to get services (similar to main.py dependencies)
def get_services():
    vector_store = get_vector_store()
    embedding_service = EmbeddingService()
    graph_store = GraphStore(vector_store=vector_store)
    memory_tiering = MemoryTieringService(vector_store=vector_store)
    entity_service = EntityService()
    
    ingestion_service = IngestionService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        graph_store=graph_store,
        memory_tiering=memory_tiering,
        entity_service=entity_service
    )
    
    search_service = SearchService(
        vector_store=vector_store,
        embedding_service=embedding_service,
        graph_store=graph_store,
        memory_tiering=memory_tiering
    )
    
    return ingestion_service, search_service

@mcp.tool()
async def add_memory(content: str, title: Optional[str] = None, type: str = "note") -> str:
    """
    Add a new memory to the Second Brain.
    
    Args:
        content: The content of the memory (note text or URL).
        title: Optional title for the memory.
        type: Type of memory ('note' or 'link').
    """
    ingestion_service, _ = get_services()
    
    # Create a mock user ID for local MCP usage
    user_id = "mcp-user"
    
    try:
        memories = await ingestion_service.process_content(
            content=content,
            source_type=type,
            user_id=user_id,
            title=title
        )
        return f"Successfully added {len(memories)} memory chunks."
    except Exception as e:
        return f"Error adding memory: {str(e)}"

@mcp.tool()
async def search_memories(query: str, limit: int = 5) -> str:
    """
    Search for memories in the Second Brain.
    
    Args:
        query: The search query.
        limit: Number of results to return.
    """
    _, search_service = get_services()
    user_id = "mcp-user"
    
    from services.search_service import SearchQuery
    
    try:
        results = await search_service.search(
            SearchQuery(query=query, limit=limit),
            user_id=user_id
        )
        
        if not results:
            return "No matching memories found."
        
        response = "Found the following memories:\n\n"
        for i, res in enumerate(results, 1):
            response += f"{i}. [Score: {res.score:.2f}] {res.memory.content[:200]}...\n"
            
        return response
    except Exception as e:
        return f"Error searching memories: {str(e)}"

@mcp.tool()
async def chat_with_brain(question: str) -> str:
    """
    Chat with the Second Brain using its memories as context.
    
    Args:
        question: The question to ask.
    """
    # This reuses the logic from main.py but adapted for MCP
    # For simplicity, we'll just do a search and return context for now,
    # or we could import the chat logic if we refactor it.
    # Let's do a search + simple formatting.
    
    return await search_memories(question, limit=5)

if __name__ == "__main__":
    mcp.run()
