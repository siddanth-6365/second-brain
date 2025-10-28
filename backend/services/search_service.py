"""Search service for querying memories"""

from typing import List, Optional
from datetime import datetime
import math
from backend.models import SearchQuery, SearchResult, Memory
from backend.services.embedding_service import get_embedding_service
from backend.services.vector_store import get_vector_store
from backend.services.graph_store import get_graph_store
from backend.services.memory_tiering import get_memory_tiering
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching and retrieving memories"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.graph_store = get_graph_store()
        self.memory_tiering = get_memory_tiering()
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for memories using semantic and keyword search.
        
        Args:
            query: Search query with parameters
            
        Returns:
            List of search results with scores
        """
        logger.info(f"Searching for: {query.query}")
        
        # Generate query embedding for semantic search
        query_embedding = self.embedding_service.embed_text(query.query)
        logger.debug(f"Query embedding generated: {len(query_embedding)} dimensions")
        
        # Semantic search using vector store
        # Use lower threshold to get results, filter by similarity_threshold later
        vector_results = self.vector_store.search(
            query_vector=query_embedding,
            limit=query.limit * 2,  # Get more results for filtering
            score_threshold=None  # No threshold, we'll filter manually
        )
        logger.info(f"Vector store returned {len(vector_results)} results")
        
        # Build search results
        results = []
        for result in vector_results:
            memory_id = result["id"]
            vector_score = result["score"]
            payload = result["payload"]
            
            # Get full memory from graph store, or reconstruct from payload
            memory = self.graph_store.get_memory(memory_id)
            if not memory:
                # Reconstruct memory from vector store payload
                try:
                    from datetime import datetime
                    memory = Memory(
                        id=memory_id,
                        content=payload.get("content", ""),
                        summary=payload.get("summary", ""),
                        document_id=payload.get("document_id", ""),
                        chunk_index=payload.get("chunk_index", 0),
                        embedding=result.get("vector"),
                        embedding_model=settings.embedding_model,
                        is_latest=payload.get("is_latest", True),
                        is_active=payload.get("is_active", True),
                        keywords=payload.get("keywords", []),
                        entities=payload.get("entities", []),
                        created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
                        metadata=payload.get("metadata", {})
                    )
                except Exception as e:
                    logger.warning(f"Failed to reconstruct memory {memory_id} from payload: {e}")
                    continue
            
            # Apply filters
            if query.only_latest and not memory.is_latest:
                continue
            
            if not query.include_inactive and not memory.is_active:
                continue
            
            # Keyword matching (simple approach)
            keyword_score = 0.0
            if query.keywords:
                query_keywords_set = set(kw.lower() for kw in query.keywords)
                memory_keywords_set = set(kw.lower() for kw in memory.keywords)
                
                # Jaccard similarity
                intersection = query_keywords_set & memory_keywords_set
                union = query_keywords_set | memory_keywords_set
                keyword_score = len(intersection) / len(union) if union else 0.0
            
            # Apply similarity threshold filter
            if vector_score < query.similarity_threshold:
                logger.debug(f"Skipping result {memory_id}: score {vector_score} < threshold {query.similarity_threshold}")
                continue
            
            # Combined score (weighted by semantic_weight)
            if query.keywords:
                combined_score = (
                    query.semantic_weight * vector_score +
                    (1 - query.semantic_weight) * keyword_score
                )
            else:
                combined_score = vector_score
            
            logger.debug(f"Result {memory_id}: vector_score={vector_score}, combined_score={combined_score}")
            
            # Apply time-aware decay (exponential decay based on age)
            combined_score = self._apply_time_decay(combined_score, memory.created_at)
            
            # Promote from cold to hot if accessed
            self.memory_tiering.promote_to_hot(memory_id)
            
            # Get related memories
            related_memories = self.graph_store.get_related_memories(
                memory_id,
                max_depth=1
            )
            related_ids = [m.id for m in related_memories[:5]]  # Top 5 related
            
            # Update access statistics
            memory.accessed_at = datetime.utcnow()
            memory.access_count += 1
            
            # Create search result
            search_result = SearchResult(
                memory=memory,
                score=combined_score,
                explanation=self._generate_explanation(memory, query, vector_score, keyword_score),
                related_memories=related_ids
            )
            results.append(search_result)
        
        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Return top results
        results = results[:query.limit]
        
        logger.info(f"Found {len(results)} results for query: {query.query}")
        return results
    
    def _apply_time_decay(self, score: float, created_at: datetime, half_life_days: Optional[int] = None) -> float:
        """
        Apply exponential time decay to score based on memory age.
        
        Decay formula: score * exp(-age_days / half_life)
        After half_life_days, score is multiplied by 0.5
        
        Args:
            score: Original score
            created_at: Memory creation timestamp
            half_life_days: Days for score to decay to 50% (uses config if not provided)
            
        Returns:
            Decayed score
        """
        half_life = half_life_days or settings.time_decay_half_life_days
        age_days = (datetime.utcnow() - created_at).days
        decay_factor = math.exp(-age_days / half_life)
        return score * decay_factor
    
    def _generate_explanation(
        self,
        memory: Memory,
        query: SearchQuery,
        vector_score: float,
        keyword_score: float
    ) -> str:
        """Generate explanation for why this result was returned"""
        explanations = []
        
        if vector_score > 0.8:
            explanations.append(f"High semantic similarity ({vector_score:.2f})")
        elif vector_score > 0.6:
            explanations.append(f"Good semantic match ({vector_score:.2f})")
        else:
            explanations.append(f"Moderate relevance ({vector_score:.2f})")
        
        if keyword_score > 0:
            explanations.append(f"keyword match ({keyword_score:.2f})")
        
        if not memory.is_latest:
            explanations.append("older version")
        
        return "; ".join(explanations)
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory or None if not found
        """
        memory = self.graph_store.get_memory(memory_id)
        if memory:
            memory.accessed_at = datetime.utcnow()
            memory.access_count += 1
        return memory
    
    async def get_related_memories(self, memory_id: str, max_depth: int = 2) -> List[Memory]:
        """
        Get memories related to a specific memory.
        
        Args:
            memory_id: Starting memory ID
            max_depth: How many relationship hops to traverse
            
        Returns:
            List of related memories
        """
        return self.graph_store.get_related_memories(memory_id, max_depth=max_depth)
    
    async def get_memory_timeline(self, topic: str) -> List[Memory]:
        """
        Get timeline of memories about a topic, showing how information evolved.
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of memories sorted by creation time
        """
        # Search for relevant memories
        query = SearchQuery(query=topic, limit=50, only_latest=False)
        results = await self.search(query)
        
        # Extract memories and sort by time
        memories = [r.memory for r in results]
        memories.sort(key=lambda m: m.created_at)
        
        return memories


# Global instance
_search_service = None


def get_search_service() -> SearchService:
    """Get singleton search service instance"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

