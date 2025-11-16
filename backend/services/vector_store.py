"""Vector store using Qdrant for semantic search"""

from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)
from backend.config import settings
from backend.models import Memory, MemoryRelationship
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage and retrieval using Qdrant"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self.relationship_collection = settings.qdrant_relationship_collection_name
        self._connect_with_retry()
    
    def _resolve_qdrant_url(self) -> Optional[str]:
        if settings.qdrant_url:
            return settings.qdrant_url
        if settings.qdrant_endpoint:
            return settings.qdrant_endpoint
        if settings.qdrant_cluster_id:
            return f"https://{settings.qdrant_cluster_id}.aws.cloud.qdrant.io"
        return None

    def _connect_with_retry(self, max_retries: int = 3, retry_delay: int = 2):
        """Connect to Qdrant with retry logic"""
        import time
        
        resolved_url = self._resolve_qdrant_url()
        target_desc = resolved_url or f"{settings.qdrant_host}:{settings.qdrant_port}"
        
        for attempt in range(max_retries):
            try:
                client_kwargs: Dict[str, Any] = {
                    "timeout": settings.qdrant_timeout,
                }

                if resolved_url:
                    client_kwargs["url"] = resolved_url
                else:
                    client_kwargs["host"] = settings.qdrant_host
                    client_kwargs["port"] = settings.qdrant_port
                    client_kwargs["https"] = settings.qdrant_use_https

                if settings.qdrant_api_key:
                    client_kwargs["api_key"] = settings.qdrant_api_key

                self.client = QdrantClient(**client_kwargs)
                # Test connection
                self.client.get_collections()
                logger.info(f"Successfully connected to Qdrant at {target_desc}")
                self._initialize_collections()
                return
            except Exception as e:
                attempt_num = attempt + 1
                if attempt_num < max_retries:
                    logger.warning(
                        f"Failed to connect to Qdrant (attempt {attempt_num}/{max_retries}). "
                        f"Retrying in {retry_delay}s... Error: {e}"
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error(
                        f"Failed to connect to Qdrant after {max_retries} attempts. "
                        f"Please ensure Qdrant is reachable at {target_desc}"
                    )
                    raise ConnectionError(
                        f"Cannot connect to Qdrant at {target_desc}. "
                        f"Make sure it's running with: docker compose up -d"
                    ) from e
    
    def _ensure_payload_indexes(self, collection_name: str, fields: Optional[List[str]] = None):
        """Ensure payload indexes exist for filtered fields."""
        fields = fields or ["user_id"]
        try:
            for field in fields:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema="keyword",
                )
                logger.info(f"Created payload index on {field} ({collection_name})")
        except Exception as exc:  # Qdrant returns error if index already exists
            message = str(exc).lower()
            if "already exists" in message:
                logger.debug(f"Payload index on {field} already exists ({collection_name})")
            else:
                logger.warning(f"Failed to create payload index on {field}: {exc}")

    def _initialize_collections(self):
        """Initialize required Qdrant collections"""
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
                self._ensure_payload_indexes(self.collection_name)
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
                self._ensure_payload_indexes(self.collection_name)

            if self.relationship_collection not in collection_names:
                logger.info(f"Creating relationship collection: {self.relationship_collection}")
                self.client.create_collection(
                    collection_name=self.relationship_collection,
                    vectors_config=VectorParams(size=1, distance=Distance.COSINE),
                )
                logger.info(f"Relationship collection created: {self.relationship_collection}")
                self._ensure_payload_indexes(self.relationship_collection, ["user_id", "from_memory_id", "to_memory_id"])
            else:
                logger.info(f"Relationship collection already exists: {self.relationship_collection}")
                self._ensure_payload_indexes(self.relationship_collection, ["user_id", "from_memory_id", "to_memory_id"])
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
                "metadata": memory.metadata,
                "user_id": memory.user_id,
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
                    "metadata": memory.metadata,
                    "user_id": memory.user_id,
                }
            )
            points.append(point)
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} memories to vector store")

    def add_relationship(self, relationship: MemoryRelationship):
        """
        Persist a relationship in the relationship collection.
        """
        payload = {
            "from_memory_id": relationship.from_memory_id,
            "to_memory_id": relationship.to_memory_id,
            "relationship_type": relationship.relationship_type.value,
            "confidence": relationship.confidence,
            "similarity_score": relationship.similarity_score,
            "reason": relationship.reason,
            "created_at": relationship.created_at.isoformat(),
            "user_id": relationship.user_id,
            "metadata": relationship.metadata,
        }

        point = PointStruct(
            id=relationship.id,
            vector=[relationship.confidence or 0.0],
            payload=payload,
        )

        self.client.upsert(
            collection_name=self.relationship_collection,
            points=[point],
        )
        logger.debug(f"Persisted relationship {relationship.id} in vector store")

    def _build_filter(self, user_id: Optional[str], filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        """Create a Qdrant filter for the provided payload filters and user scope"""
        must_conditions = []

        if user_id:
            must_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            )

        if filters:
            for key, value in filters.items():
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )

        if must_conditions:
            return Filter(must=must_conditions)
        return None

    def _scroll_collection(
        self,
        collection_name: str,
        user_id: Optional[str] = None,
        limit: int = 256,
    ):
        """Scroll through entire collection, returning all records (payload only)."""
        records = []
        offset = None
        payload_filter = self._build_filter(user_id, None)

        while True:
            batch, offset = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=payload_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            records.extend(batch)
            if offset is None:
                break
        return records

    def fetch_all_memories(self, user_id: Optional[str] = None):
        """Retrieve all memories (payloads) for optional user scope."""
        return self._scroll_collection(self.collection_name, user_id=user_id)

    def fetch_all_relationships(self, user_id: Optional[str] = None):
        """Retrieve all relationships stored in Qdrant (payloads)."""
        return self._scroll_collection(self.relationship_collection, user_id=user_id, limit=512)
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
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
        
        payload_filter = self._build_filter(user_id, filters)
        if payload_filter:
            search_params["query_filter"] = payload_filter
        
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

    def delete_memories_by_user(self, user_id: str):
        """
        Delete all memories associated with a specific user.
        
        Args:
            user_id: Supabase user ID
        """
        if not user_id:
            return
        selector = FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=selector
        )
        self.delete_relationships_by_user(user_id)
        logger.info(f"Deleted Qdrant memories and relationships for user {user_id}")

    def delete_relationships_by_user(self, user_id: str):
        """Delete all persisted relationships belonging to a user."""
        if not user_id:
            return
        selector = FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )
        self.client.delete(
            collection_name=self.relationship_collection,
            points_selector=selector
        )
        logger.debug(f"Deleted relationships for user {user_id}")


# Global instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

