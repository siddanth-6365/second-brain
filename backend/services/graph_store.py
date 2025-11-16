"""Graph store for managing memory relationships"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import networkx as nx
from backend.models import Memory, MemoryRelationship, RelationshipType
from backend.services.vector_store import get_vector_store
import logging

logger = logging.getLogger(__name__)


class GraphStore:
    """Manages the knowledge graph of memory relationships"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.memories: Dict[str, Memory] = {}  # In-memory storage of memories
        self.relationships: Dict[str, MemoryRelationship] = {}  # Relationships by ID
        self._hydrated = False
        self._hydrate_from_storage()

    def _ensure_hydrated(self):
        if not self._hydrated:
            self._hydrate_from_storage()

    def _parse_datetime(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.utcnow()

    def _hydrate_from_storage(self):
        if self._hydrated:
            return
        try:
            vector_store = get_vector_store()
        except Exception as exc:
            logger.warning(f"Vector store unavailable during graph hydration: {exc}")
            return

        try:
            records = vector_store.fetch_all_memories()
            for record in records:
                payload = record.payload or {}
                try:
                    memory = Memory(
                        id=str(record.id),
                        user_id=payload.get("user_id"),
                        content=payload.get("content", ""),
                        summary=payload.get("summary"),
                        document_id=payload.get("document_id", ""),
                        chunk_index=payload.get("chunk_index", 0),
                        embedding=None,
                        embedding_model=payload.get("embedding_model"),
                        keywords=payload.get("keywords", []),
                        entities=payload.get("entities", []),
                        metadata=payload.get("metadata", {}),
                        is_latest=payload.get("is_latest", True),
                        is_active=payload.get("is_active", True),
                        created_at=self._parse_datetime(payload.get("created_at")),
                        updated_at=self._parse_datetime(payload.get("created_at")),
                    )
                    self.add_memory(memory)
                except Exception as exc:
                    logger.warning(f"Failed to hydrate memory {record.id}: {exc}")

            relationship_records = vector_store.fetch_all_relationships()
            for record in relationship_records:
                payload = record.payload or {}
                try:
                    relationship = MemoryRelationship(
                        id=str(record.id),
                        from_memory_id=payload.get("from_memory_id"),
                        to_memory_id=payload.get("to_memory_id"),
                        relationship_type=RelationshipType(payload.get("relationship_type", RelationshipType.SIMILAR.value)),
                        confidence=payload.get("confidence", 0.0),
                        similarity_score=payload.get("similarity_score"),
                        reason=payload.get("reason"),
                        metadata=payload.get("metadata", {}),
                        created_at=self._parse_datetime(payload.get("created_at")),
                        user_id=payload.get("user_id"),
                    )
                    self.add_relationship(relationship, persist=False)
                except Exception as exc:
                    logger.warning(f"Failed to hydrate relationship {record.id}: {exc}")

            self._hydrated = True
            logger.info("Hydrated graph store from vector store persistence")
        except Exception as exc:
            logger.error(f"Error hydrating graph store: {exc}")
    
    def add_memory(self, memory: Memory):
        """
        Add a memory node to the graph.
        
        Args:
            memory: Memory object
        """
        if memory.id in self.memories:
            return
        self.memories[memory.id] = memory
        self.graph.add_node(
            memory.id,
            content=memory.content[:100],  # Store truncated content
            is_latest=memory.is_latest,
            is_active=memory.is_active,
            created_at=memory.created_at.isoformat(),
            user_id=memory.user_id,
        )
        logger.debug(f"Added memory node to graph: {memory.id}")
    
    def add_relationship(self, relationship: MemoryRelationship, persist: bool = True):
        """
        Add a relationship edge between memories.
        
        Args:
            relationship: MemoryRelationship object
        """
        from_memory = self.memories.get(relationship.from_memory_id)
        to_memory = self.memories.get(relationship.to_memory_id)

        if from_memory and to_memory:
            if from_memory.user_id != to_memory.user_id:
                logger.warning(
                    "Skipping relationship between memories that belong to different users: "
                    f"{relationship.from_memory_id} -> {relationship.to_memory_id}"
                )
                return
            relationship.user_id = relationship.user_id or from_memory.user_id
        else:
            logger.warning(
                "Skipping relationship because one of the memories is missing: "
                f"{relationship.from_memory_id} -> {relationship.to_memory_id}"
            )
            return

        self.relationships[relationship.id] = relationship
        
        self.graph.add_edge(
            relationship.from_memory_id,
            relationship.to_memory_id,
            key=relationship.id,
            type=relationship.relationship_type.value,
            confidence=relationship.confidence,
            similarity_score=relationship.similarity_score,
            reason=relationship.reason,
            created_at=relationship.created_at.isoformat(),
            user_id=relationship.user_id,
        )
        
        # Update the memory's relationship IDs (avoid circular references)
        if relationship.from_memory_id in self.memories:
            memory = self.memories[relationship.from_memory_id]
            if relationship.id not in memory.relationship_ids:
                memory.relationship_ids.append(relationship.id)
        
        # Persist relationship in vector store for durability
        if persist:
            try:
                vector_store = get_vector_store()
                vector_store.add_relationship(relationship)
            except Exception as exc:
                logger.error(f"Failed to persist relationship {relationship.id}: {exc}")
        
        logger.debug(
            f"Added relationship: {relationship.from_memory_id} "
            f"-[{relationship.relationship_type.value}]-> "
            f"{relationship.to_memory_id}"
        )
    
    def get_memory(self, memory_id: str, user_id: Optional[str] = None) -> Optional[Memory]:
        """Get a memory by ID (optionally scoped to a user)"""
        self._ensure_hydrated()
        memory = self.memories.get(memory_id)
        if not memory:
            return None
        if user_id and memory.user_id != user_id:
            return None
        return memory
    
    def get_all_memories(self, user_id: Optional[str] = None) -> List[Memory]:
        """Get all memories (optionally scoped to a user)"""
        self._ensure_hydrated()
        if not user_id:
            return list(self.memories.values())
        return [memory for memory in self.memories.values() if memory.user_id == user_id]
    
    def get_relationships(
        self,
        memory_id: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "outgoing",
        user_id: Optional[str] = None,
    ) -> List[MemoryRelationship]:
        """
        Get relationships for a memory.
        
        Args:
            memory_id: Memory ID
            relationship_type: Filter by relationship type (optional)
            direction: "outgoing" (from this memory), "incoming" (to this memory), or "both"
            
        Returns:
            List of relationships
        """
        self._ensure_hydrated()
        relationships = []
        
        if direction in ["outgoing", "both"]:
            # Get outgoing edges
            if memory_id in self.graph:
                for _, target, key, data in self.graph.out_edges(memory_id, keys=True, data=True):
                    rel = self.relationships.get(key)
                    if rel and (not relationship_type or rel.relationship_type == relationship_type):
                        if not user_id or rel.user_id == user_id:
                            relationships.append(rel)
        
        if direction in ["incoming", "both"]:
            # Get incoming edges
            if memory_id in self.graph:
                for source, _, key, data in self.graph.in_edges(memory_id, keys=True, data=True):
                    rel = self.relationships.get(key)
                    if rel and (not relationship_type or rel.relationship_type == relationship_type):
                        if not user_id or rel.user_id == user_id:
                            relationships.append(rel)
        
        return relationships
    
    def get_related_memories(
        self,
        memory_id: str,
        relationship_type: Optional[RelationshipType] = None,
        max_depth: int = 1,
        user_id: Optional[str] = None,
    ) -> List[Memory]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: Starting memory ID
            relationship_type: Filter by relationship type
            max_depth: Maximum traversal depth
            
        Returns:
            List of related memories
        """
        self._ensure_hydrated()
        if memory_id not in self.graph:
            return []
        
        start_memory = self.memories.get(memory_id)
        if user_id and start_memory and start_memory.user_id != user_id:
            logger.warning("User attempted to access a memory that does not belong to them")
            return []
        
        related_ids: Set[str] = set()
        
        # BFS traversal
        queue = [(memory_id, 0)]
        visited = {memory_id}
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # Get neighbors (both outgoing and incoming)
            for neighbor in self.graph.successors(current_id):
                if neighbor in visited:
                    continue
                neighbor_memory = self.memories.get(neighbor)
                if user_id and neighbor_memory and neighbor_memory.user_id != user_id:
                    continue
                edges = self.graph.get_edge_data(current_id, neighbor)
                for key, edge_data in edges.items():
                    if user_id and edge_data.get("user_id") != user_id:
                        continue
                    if not relationship_type or edge_data.get('type') == relationship_type.value:
                        related_ids.add(neighbor)
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
                        break
            
            for neighbor in self.graph.predecessors(current_id):
                if neighbor in visited:
                    continue
                neighbor_memory = self.memories.get(neighbor)
                if user_id and neighbor_memory and neighbor_memory.user_id != user_id:
                    continue
                edges = self.graph.get_edge_data(neighbor, current_id)
                for key, edge_data in edges.items():
                    if user_id and edge_data.get("user_id") != user_id:
                        continue
                    if not relationship_type or edge_data.get('type') == relationship_type.value:
                        related_ids.add(neighbor)
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
                        break
        
        return [self.memories[mid] for mid in related_ids if mid in self.memories]
    
    def mark_memory_outdated(self, memory_id: str):
        """
        Mark a memory as outdated (not latest).
        
        Args:
            memory_id: Memory ID to mark as outdated
        """
        if memory_id in self.memories:
            self.memories[memory_id].is_latest = False
            if memory_id in self.graph:
                self.graph.nodes[memory_id]['is_latest'] = False
            logger.debug(f"Marked memory as outdated: {memory_id}")
    
    def get_graph_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the knowledge graph (optionally scoped to a user)"""
        self._ensure_hydrated()
        memories = self.get_all_memories(user_id)
        total_relationships = (
            len([rel for rel in self.relationships.values() if not user_id or rel.user_id == user_id])
        )
        graph_nodes = (
            self.graph.number_of_nodes()
            if not user_id
            else len([node for node, data in self.graph.nodes(data=True) if data.get("user_id") == user_id])
        )
        graph_edges = (
            self.graph.number_of_edges()
            if not user_id
            else len(
                [
                    1
                    for _, _, data in self.graph.edges(data=True)
                    if data.get("user_id") == user_id
                ]
            )
        )
        return {
            "total_memories": len(memories),
            "total_relationships": total_relationships,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "relationship_types": {
                rt.value: sum(
                    1
                    for r in self.relationships.values()
                    if r.relationship_type == rt and (not user_id or r.user_id == user_id)
                )
                for rt in RelationshipType
            }
        }
    
    def export_graph(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Export the graph for visualization (optionally scoped to a user)"""
        self._ensure_hydrated()
        nodes = []
        edges = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if user_id and node_data.get("user_id") != user_id:
                continue
            memory = self.memories.get(node_id)
            nodes.append({
                "id": node_id,
                "label": node_data.get("content", ""),
                "is_latest": node_data.get("is_latest", True),
                "is_active": node_data.get("is_active", True),
                "created_at": node_data.get("created_at"),
                "full_content": memory.content if memory else ""
            })
        
        for source, target, key, edge_data in self.graph.edges(keys=True, data=True):
            if user_id and edge_data.get("user_id") != user_id:
                continue
            edges.append({
                "id": key,
                "source": source,
                "target": target,
                "type": edge_data.get("type"),
                "confidence": edge_data.get("confidence"),
                "reason": edge_data.get("reason")
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": self.get_graph_stats(user_id=user_id)
        }

    def clear_user_data(self, user_id: str) -> Dict[str, int]:
        """Remove all memories and relationships for a specific user"""
        if not user_id:
            return {"memories": 0, "relationships": 0}

        memory_ids = [mid for mid, mem in self.memories.items() if mem.user_id == user_id]
        relationship_ids = [rid for rid, rel in self.relationships.items() if rel.user_id == user_id]

        for memory_id in memory_ids:
            self.memories.pop(memory_id, None)
            if self.graph.has_node(memory_id):
                self.graph.remove_node(memory_id)

        for relationship_id in relationship_ids:
            self.relationships.pop(relationship_id, None)

        for memory in self.memories.values():
            if memory.relationship_ids:
                memory.relationship_ids = [
                    rid for rid in memory.relationship_ids if rid not in relationship_ids
                ]

        logger.info(
            "Cleared %s memories and %s relationships for user %s",
            len(memory_ids),
            len(relationship_ids),
            user_id,
        )
        return {
            "memories": len(memory_ids),
            "relationships": len(relationship_ids),
            "memory_ids": memory_ids,
        }


# Global instance
_graph_store = None


def get_graph_store() -> GraphStore:
    """Get singleton graph store instance"""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store

