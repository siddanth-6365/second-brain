"""Memory tiering service for hot/cold storage management"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.models import Memory
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class MemoryTiering:
    """Manages hot/cold memory tiering for performance optimization"""
    
    def __init__(
        self,
        hot_age_days: Optional[int] = None,
        hot_access_threshold: Optional[int] = None,
        cold_storage_enabled: Optional[bool] = None
    ):
        """
        Initialize memory tiering.
        
        Args:
            hot_age_days: Memories younger than this are considered "hot"
            hot_access_threshold: Memories accessed more than this are "hot"
            cold_storage_enabled: Whether to use cold storage tier
        """
        self.hot_age_days = hot_age_days or settings.hot_memory_age_days
        self.hot_access_threshold = hot_access_threshold or settings.hot_memory_access_threshold
        self.cold_storage_enabled = cold_storage_enabled if cold_storage_enabled is not None else settings.cold_storage_enabled
        self.hot_memories: Dict[str, Memory] = {}  # Fast-access layer
        self.cold_memories: Dict[str, Memory] = {}  # Archived layer
    
    def classify_memory(self, memory: Memory) -> str:
        """
        Classify memory as 'hot' or 'cold' based on age and access patterns.
        
        Args:
            memory: Memory to classify
            
        Returns:
            'hot' or 'cold'
        """
        if not self.cold_storage_enabled:
            return 'hot'
        
        age_days = (datetime.utcnow() - memory.created_at).days
        
        # Hot criteria: recent OR frequently accessed
        is_recent = age_days <= self.hot_age_days
        is_frequently_accessed = memory.access_count >= self.hot_access_threshold
        
        if is_recent or is_frequently_accessed:
            return 'hot'
        else:
            return 'cold'
    
    def add_to_hot(self, memory: Memory):
        """Add memory to hot storage"""
        self.hot_memories[memory.id] = memory
        # Remove from cold if it was there
        self.cold_memories.pop(memory.id, None)
        logger.debug(f"Added memory to hot tier: {memory.id}")
    
    def add_to_cold(self, memory: Memory):
        """Add memory to cold storage"""
        if self.cold_storage_enabled:
            self.cold_memories[memory.id] = memory
            # Remove from hot
            self.hot_memories.pop(memory.id, None)
            logger.debug(f"Added memory to cold tier: {memory.id}")
    
    def promote_to_hot(self, memory_id: str) -> bool:
        """
        Promote memory from cold to hot (e.g., when accessed).
        
        Args:
            memory_id: Memory ID to promote
            
        Returns:
            True if promotion occurred
        """
        if memory_id in self.cold_memories:
            memory = self.cold_memories.pop(memory_id)
            self.hot_memories[memory_id] = memory
            logger.debug(f"Promoted memory to hot tier: {memory_id}")
            return True
        return False
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get memory from either hot or cold tier.
        Promotes from cold to hot on access.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory or None
        """
        # Check hot first (faster)
        if memory_id in self.hot_memories:
            return self.hot_memories[memory_id]
        
        # Check cold
        if memory_id in self.cold_memories:
            self.promote_to_hot(memory_id)
            return self.cold_memories.get(memory_id) or self.hot_memories.get(memory_id)
        
        return None
    
    def rebalance_tiers(self) -> Dict[str, int]:
        """
        Rebalance memories between hot and cold tiers based on current criteria.
        Should be called periodically (e.g., daily).
        
        Returns:
            Statistics: {promoted: count, demoted: count}
        """
        promoted_count = 0
        demoted_count = 0
        
        # Check hot memories for demotion
        hot_ids = list(self.hot_memories.keys())
        for memory_id in hot_ids:
            memory = self.hot_memories[memory_id]
            if self.classify_memory(memory) == 'cold':
                self.add_to_cold(memory)
                demoted_count += 1
        
        # Check cold memories for promotion
        cold_ids = list(self.cold_memories.keys())
        for memory_id in cold_ids:
            memory = self.cold_memories[memory_id]
            if self.classify_memory(memory) == 'hot':
                self.add_to_hot(memory)
                promoted_count += 1
        
        logger.info(
            f"Rebalanced tiers: {promoted_count} promoted, {demoted_count} demoted"
        )
        return {
            "promoted": promoted_count,
            "demoted": demoted_count
        }
    
    def get_hot_memories(self) -> List[Memory]:
        """Get all hot memories"""
        return list(self.hot_memories.values())
    
    def get_cold_memories(self) -> List[Memory]:
        """Get all cold memories"""
        return list(self.cold_memories.values())
    
    def get_tier_stats(self) -> Dict[str, Any]:
        """Get statistics about tier distribution"""
        total = len(self.hot_memories) + len(self.cold_memories)
        return {
            "hot_count": len(self.hot_memories),
            "cold_count": len(self.cold_memories),
            "total_count": total,
            "hot_percentage": (len(self.hot_memories) / total * 100) if total > 0 else 0,
            "cold_percentage": (len(self.cold_memories) / total * 100) if total > 0 else 0
        }
    
    def remove_memories(self, memory_ids: List[str]):
        """Remove a batch of memories from both tiers"""
        for memory_id in memory_ids:
            self.hot_memories.pop(memory_id, None)
            self.cold_memories.pop(memory_id, None)


# Global instance
_memory_tiering = None


def get_memory_tiering() -> MemoryTiering:
    """Get singleton memory tiering instance"""
    global _memory_tiering
    if _memory_tiering is None:
        _memory_tiering = MemoryTiering()
    return _memory_tiering
