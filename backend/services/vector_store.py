"""Vector store using Qdrant for semantic search"""

from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, SearchRequest
from backend.config import settings
from backend.models import Memory
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage and retrieval using Qdrant"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.collection_name = settings.qdrant_collection_name
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize the Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise
    
    def add_memory(self, memory: Memory):
        """
        Add a memory to the vector store.
        
        Args:
            memory: Memory object with embedding
        """
        if not memory.embedding:
            raise ValueError("Memory must have an embedding")
        
        point = PointStruct(
            id=memory.id,
            vector=memory.embedding,
            payload={
                "content": memory.content,
                "summary": memory.summary,
                "document_id": memory.document_id,
                "chunk_index": memory.chunk_index,
                "is_latest": memory.is_latest,
                "is_active": memory.is_active,
                "keywords": memory.keywords,
                "entities": memory.entities,
                "created_at": memory.created_at.isoformat(),
                "metadata": memory.metadata
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        logger.debug(f"Added memory to vector store: {memory.id}")
    
    def add_memories_batch(self, memories: List[Memory]):
        """
        Add multiple memories to the vector store.
        
        Args:
            memories: List of Memory objects with embeddings
        """
        points = []
        for memory in memories:
            if not memory.embedding:
                logger.warning(f"Skipping memory without embedding: {memory.id}")
                continue
            
            point = PointStruct(
                id=memory.id,
                vector=memory.embedding,
                payload={
                    "content": memory.content,
                    "summary": memory.summary,
                    "document_id": memory.document_id,
                    "chunk_index": memory.chunk_index,
                    "is_latest": memory.is_latest,
                    "is_active": memory.is_active,
                    "keywords": memory.keywords,
                    "entities": memory.entities,
                    "created_at": memory.created_at.isoformat(),
                    "metadata": memory.metadata
                }
            )
            points.append(point)
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} memories to vector store")
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Additional filters (e.g., {"is_latest": True})
            
        Returns:
            List of search results with memory data and scores
        """
        search_params = {
            "collection_name": self.collection_name,
            "query_vector": query_vector,
            "limit": limit
        }
        
        if score_threshold:
            search_params["score_threshold"] = score_threshold
        
        # TODO: Add filter support when needed
        
        results = self.client.search(**search_params)
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory data or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id]
            )
            if result:
                return {
                    "id": result[0].id,
                    "payload": result[0].payload,
                    "vector": result[0].vector
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None
    
    def delete_memory(self, memory_id: str):
        """
        Delete a memory from the vector store.
        
        Args:
            memory_id: Memory ID to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[memory_id]
        )
        logger.debug(f"Deleted memory from vector store: {memory_id}")
    
    def update_memory_payload(self, memory_id: str, payload: Dict[str, Any]):
        """
        Update the payload (metadata) of a memory.
        
        Args:
            memory_id: Memory ID
            payload: New payload data
        """
        self.client.set_payload(
            collection_name=self.collection_name,
            payload=payload,
            points=[memory_id]
        )
        logger.debug(f"Updated memory payload: {memory_id}")


# Global instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

