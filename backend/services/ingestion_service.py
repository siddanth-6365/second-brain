"""Ingestion service for processing documents into memories"""

from typing import List, Optional
from datetime import datetime
import re
from backend.models import Document, Memory, MemoryRelationship, RelationshipType, DocumentStatus
from backend.services.embedding_service import get_embedding_service
from backend.services.vector_store import get_vector_store
from backend.services.graph_store import get_graph_store
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents and creating memories"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.graph_store = get_graph_store()
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Input text
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        # Clean text
        text = text.strip()
        
        # Split into sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Keep overlap sentences for next chunk
                overlap_text = ' '.join(current_chunk)
                if len(overlap_text) > overlap:
                    # Start next chunk with part of previous chunk
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk = current_chunk[-1:] + [sentence] if current_chunk else [sentence]
                    current_length = len(' '.join(current_chunk))
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text (simple implementation).
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - remove common words and get unique words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'as', 'by', 'from'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and get unique words
        keywords = []
        seen = set()
        for word in words:
            if word not in stop_words and word not in seen:
                keywords.append(word)
                seen.add(word)
                if len(keywords) >= max_keywords:
                    break
        
        return keywords
    
    async def process_document(self, document: Document) -> List[Memory]:
        """
        Process a document into memories.
        
        Pipeline: Extract → Chunk → Embed → Detect Relationships → Index
        
        Args:
            document: Document to process
            
        Returns:
            List of created memories
        """
        logger.info(f"Processing document: {document.id}")
        
        try:
            # Update status: EXTRACTING
            document.status = DocumentStatus.EXTRACTING
            # In a real app, this is where we'd extract text from PDFs, images, etc.
            content = document.content
            
            # Update status: CHUNKING
            document.status = DocumentStatus.CHUNKING
            chunks = self.chunk_text(content)
            logger.info(f"Created {len(chunks)} chunks from document")
            
            # Update status: EMBEDDING
            document.status = DocumentStatus.EMBEDDING
            embeddings = self.embedding_service.embed_batch(chunks)
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            
            # Create memories
            memories = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                memory = Memory(
                    content=chunk,
                    document_id=document.id,
                    chunk_index=idx,
                    embedding=embedding,
                    embedding_model=settings.embedding_model,
                    keywords=self.extract_keywords(chunk),
                    metadata={
                        "source": document.source,
                        "document_type": document.document_type,
                        "title": document.title
                    }
                )
                memories.append(memory)
                document.memory_ids.append(memory.id)
            
            # Update status: INDEXING
            document.status = DocumentStatus.INDEXING
            
            # Add to graph store first (so they exist for relationship detection)
            for memory in memories:
                self.graph_store.add_memory(memory)
            
            # Add to vector store (so they're searchable)
            self.vector_store.add_memories_batch(memories)
            
            # Detect relationships with existing memories (now that new memories are in vector store)
            await self._detect_relationships(memories)
            
            # Update status: DONE
            document.status = DocumentStatus.DONE
            document.processed_at = datetime.utcnow()
            
            logger.info(f"Successfully processed document {document.id} into {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            raise
    
    async def _detect_relationships(self, new_memories: List[Memory]):
        """
        Detect relationships between new memories and existing ones.
        
        Relationship types:
        - UPDATES: High similarity (> 0.85) - new info contradicts/updates old
        - EXTENDS: Medium similarity (0.70-0.85) - new info adds to existing
        - DERIVES: Inferred connections based on patterns
        
        Args:
            new_memories: Newly created memories
        """
        logger.info(f"Detecting relationships for {len(new_memories)} new memories")
        
        existing_memories = self.graph_store.get_all_memories()
        
        for new_memory in new_memories:
            # Search for similar existing memories
            if not new_memory.embedding:
                continue
            
            similar_results = self.vector_store.search(
                query_vector=new_memory.embedding,
                limit=5,
                score_threshold=0.65  # Only consider somewhat similar memories
            )
            
            for result in similar_results:
                existing_memory_id = result["id"]
                similarity_score = result["score"]
                
                # Skip self-matches and memories from same document
                if existing_memory_id == new_memory.id:
                    continue
                
                existing_memory = self.graph_store.get_memory(existing_memory_id)
                if not existing_memory or existing_memory.document_id == new_memory.document_id:
                    continue
                
                # Determine relationship type using intelligent detection
                relationship = self._classify_relationship(
                    new_memory, existing_memory, similarity_score
                )
                
                if relationship:
                    self.graph_store.add_relationship(relationship)
                    logger.debug(
                        f"Created {relationship.relationship_type.value} relationship: "
                        f"{new_memory.id} -> {existing_memory_id} (score: {similarity_score:.2f})"
                    )
        
        # Implement basic DERIVES relationships using pattern detection
        await self._detect_derives_relationships(new_memories)
    
    def _classify_relationship(
        self, 
        new_memory: Memory, 
        existing_memory: Memory, 
        similarity_score: float
    ) -> Optional[MemoryRelationship]:
        """
        Intelligently classify the relationship between two memories.
        
        Uses multiple signals:
        - Similarity score
        - Content analysis (contradiction vs addition)
        - Temporal ordering
        - Keyword overlap
        """
        # High similarity = likely an update or very similar content
        if similarity_score >= settings.similarity_threshold_update:
            # Check if content contradicts or updates
            if self._has_contradictory_info(new_memory.content, existing_memory.content):
                # Mark existing as outdated
                self.graph_store.mark_memory_outdated(existing_memory.id)
                
                return MemoryRelationship(
                    from_memory_id=new_memory.id,
                    to_memory_id=existing_memory.id,
                    relationship_type=RelationshipType.UPDATES,
                    confidence=similarity_score,
                    similarity_score=similarity_score,
                    reason=f"New information updates/contradicts existing (similarity: {similarity_score:.2f})"
                )
            else:
                # Very similar but not contradictory = similar reference
                return MemoryRelationship(
                    from_memory_id=new_memory.id,
                    to_memory_id=existing_memory.id,
                    relationship_type=RelationshipType.SIMILAR,
                    confidence=similarity_score,
                    similarity_score=similarity_score,
                    reason=f"Highly similar content (similarity: {similarity_score:.2f})"
                )
        
        # Medium similarity = likely extends or adds context
        elif similarity_score >= settings.similarity_threshold_extend:
            return MemoryRelationship(
                from_memory_id=new_memory.id,
                to_memory_id=existing_memory.id,
                relationship_type=RelationshipType.EXTENDS,
                confidence=similarity_score,
                similarity_score=similarity_score,
                reason=f"Additional context for related topic (similarity: {similarity_score:.2f})"
            )
        
        # Lower similarity but still relevant = similar/related
        else:
            return MemoryRelationship(
                from_memory_id=new_memory.id,
                to_memory_id=existing_memory.id,
                relationship_type=RelationshipType.SIMILAR,
                confidence=similarity_score,
                similarity_score=similarity_score,
                reason=f"Related content (similarity: {similarity_score:.2f})"
            )
    
    def _has_contradictory_info(self, new_content: str, existing_content: str) -> bool:
        """
        Detect if new content contradicts existing content.
        Simple heuristic: look for update keywords and changed numbers/facts.
        """
        update_keywords = [
            'now', 'updated', 'changed', 'instead', 'no longer',
            'switched', 'currently', 'revised', 'modified'
        ]
        
        new_lower = new_content.lower()
        
        # Check for explicit update language
        for keyword in update_keywords:
            if keyword in new_lower:
                return True
        
        # If contents are very different in numbers, might be an update
        import re
        new_numbers = set(re.findall(r'\d+', new_content))
        existing_numbers = set(re.findall(r'\d+', existing_content))
        
        if new_numbers and existing_numbers and new_numbers != existing_numbers:
            # Different numbers might indicate an update
            return True
        
        return False
    
    async def _detect_derives_relationships(self, new_memories: List[Memory]):
        """
        Detect DERIVES relationships by analyzing patterns across memories.
        This is a basic implementation that looks for common themes and connections.
        """
        all_memories = self.graph_store.get_all_memories()
        
        for new_memory in new_memories:
            # Look for patterns that might suggest derived relationships
            new_keywords = set(new_memory.keywords)
            
            for existing_memory in all_memories:
                if existing_memory.id == new_memory.id:
                    continue
                    
                existing_keywords = set(existing_memory.keywords)
                
                # Find common keywords
                common_keywords = new_keywords.intersection(existing_keywords)
                
                # If they share significant keywords but aren't too similar, might be DERIVES
                if len(common_keywords) >= 2:  # At least 2 common keywords
                    # Check if they're not already related
                    existing_relationships = self.graph_store.get_relationships(new_memory.id, direction="both")
                    already_related = any(
                        rel.to_memory_id == existing_memory.id or rel.from_memory_id == existing_memory.id
                        for rel in existing_relationships
                    )
                    
                    if not already_related:
                        # Calculate a derived confidence based on keyword overlap
                        keyword_overlap = len(common_keywords) / max(len(new_keywords), len(existing_keywords))
                        
                        if keyword_overlap >= 0.3:  # 30% keyword overlap
                            relationship = MemoryRelationship(
                                from_memory_id=new_memory.id,
                                to_memory_id=existing_memory.id,
                                relationship_type=RelationshipType.DERIVES,
                                confidence=keyword_overlap,
                                similarity_score=None,
                                reason=f"Shared keywords: {', '.join(common_keywords)} (overlap: {keyword_overlap:.2f})"
                            )
                            
                            self.graph_store.add_relationship(relationship)
                            logger.debug(
                                f"Created DERIVES relationship: {new_memory.id} -> {existing_memory.id} "
                                f"(keywords: {common_keywords})"
                            )
    
    async def ingest_text(self, text: str, title: Optional[str] = None, source: Optional[str] = None) -> Document:
        """
        Convenience method to ingest text directly.
        
        Args:
            text: Text content
            title: Optional title
            source: Optional source identifier
            
        Returns:
            Processed document
        """
        document = Document(
            content=text,
            title=title,
            source=source,
            document_type="text"
        )
        
        await self.process_document(document)
        return document


# Global instance
_ingestion_service = None


def get_ingestion_service() -> IngestionService:
    """Get singleton ingestion service instance"""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service

