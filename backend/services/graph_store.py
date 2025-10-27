"""Graph store for managing memory relationships"""

from typing import List, Dict, Any, Optional, Set
import networkx as nx
from backend.models import Memory, MemoryRelationship, RelationshipType
import logging
import json

logger = logging.getLogger(__name__)


class GraphStore:
    """Manages the knowledge graph of memory relationships"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.memories: Dict[str, Memory] = {}  # In-memory storage of memories
        self.relationships: Dict[str, MemoryRelationship] = {}  # Relationships by ID
    
    def add_memory(self, memory: Memory):
        """
        Add a memory node to the graph.
        
        Args:
            memory: Memory object
        """
        self.memories[memory.id] = memory
        self.graph.add_node(
            memory.id,
            content=memory.content[:100],  # Store truncated content
            is_latest=memory.is_latest,
            is_active=memory.is_active,
            created_at=memory.created_at.isoformat()
        )
        logger.debug(f"Added memory node to graph: {memory.id}")
    
    def add_relationship(self, relationship: MemoryRelationship):
        """
        Add a relationship edge between memories.
        
        Args:
            relationship: MemoryRelationship object
        """
        self.relationships[relationship.id] = relationship
        
        self.graph.add_edge(
            relationship.from_memory_id,
            relationship.to_memory_id,
            key=relationship.id,
            type=relationship.relationship_type.value,
            confidence=relationship.confidence,
            similarity_score=relationship.similarity_score,
            reason=relationship.reason,
            created_at=relationship.created_at.isoformat()
        )
        
        # Update the memory's relationship IDs (avoid circular references)
        if relationship.from_memory_id in self.memories:
            memory = self.memories[relationship.from_memory_id]
            if relationship.id not in memory.relationship_ids:
                memory.relationship_ids.append(relationship.id)
        
        logger.debug(
            f"Added relationship: {relationship.from_memory_id} "
            f"-[{relationship.relationship_type.value}]-> "
            f"{relationship.to_memory_id}"
        )
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID"""
        return self.memories.get(memory_id)
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories"""
        return list(self.memories.values())
    
    def get_relationships(
        self,
        memory_id: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "outgoing"  # "outgoing", "incoming", or "both"
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
        relationships = []
        
        if direction in ["outgoing", "both"]:
            # Get outgoing edges
            if memory_id in self.graph:
                for _, target, key, data in self.graph.out_edges(memory_id, keys=True, data=True):
                    rel = self.relationships.get(key)
                    if rel and (not relationship_type or rel.relationship_type == relationship_type):
                        relationships.append(rel)
        
        if direction in ["incoming", "both"]:
            # Get incoming edges
            if memory_id in self.graph:
                for source, _, key, data in self.graph.in_edges(memory_id, keys=True, data=True):
                    rel = self.relationships.get(key)
                    if rel and (not relationship_type or rel.relationship_type == relationship_type):
                        relationships.append(rel)
        
        return relationships
    
    def get_related_memories(
        self,
        memory_id: str,
        relationship_type: Optional[RelationshipType] = None,
        max_depth: int = 1
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
        if memory_id not in self.graph:
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
                if neighbor not in visited:
                    # Check relationship type if specified
                    edges = self.graph.get_edge_data(current_id, neighbor)
                    for key, edge_data in edges.items():
                        if not relationship_type or edge_data.get('type') == relationship_type.value:
                            related_ids.add(neighbor)
                            visited.add(neighbor)
                            queue.append((neighbor, depth + 1))
                            break
            
            for neighbor in self.graph.predecessors(current_id):
                if neighbor not in visited:
                    edges = self.graph.get_edge_data(neighbor, current_id)
                    for key, edge_data in edges.items():
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
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return {
            "total_memories": len(self.memories),
            "total_relationships": len(self.relationships),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "relationship_types": {
                rt.value: sum(
                    1 for r in self.relationships.values()
                    if r.relationship_type == rt
                )
                for rt in RelationshipType
            }
        }
    
    def export_graph(self) -> Dict[str, Any]:
        """Export the graph for visualization"""
        nodes = []
        edges = []
        
        for node_id, node_data in self.graph.nodes(data=True):
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
            "stats": self.get_graph_stats()
        }


# Global instance
_graph_store = None


def get_graph_store() -> GraphStore:
    """Get singleton graph store instance"""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store

