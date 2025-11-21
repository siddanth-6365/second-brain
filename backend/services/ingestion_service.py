"""Ingestion service for processing documents into memories"""

from typing import List, Optional
from datetime import datetime
import re
from fastapi import UploadFile
from backend.models import Document, Memory, MemoryRelationship, RelationshipType, DocumentStatus
from backend.services.embedding_service import get_embedding_service
from backend.services.vector_store import get_vector_store
from backend.services.graph_store import get_graph_store
from backend.services.memory_tiering import get_memory_tiering
from backend.services.entity_service import get_entity_service
from backend.services.content_loader import get_content_loader
from backend.config import settings
from backend.services.summarization_service import (
    get_summarization_service,
    SummarizationError,
)
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents and creating memories"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.graph_store = get_graph_store()
        self.memory_tiering = get_memory_tiering()
        self.entity_service = get_entity_service()
        self.content_loader = get_content_loader()
        self.summarizer = get_summarization_service()
    
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
        logger.info(f"Processing document: {document.id} for user {document.user_id}")
        
        try:
            # Update status: EXTRACTING
            document.status = DocumentStatus.EXTRACTING
            # In a real app, this is where we'd extract text from PDFs, images, etc.
            content = document.content
            
            # Update status: CHUNKING
            document.status = DocumentStatus.CHUNKING
            
            # For link summaries, skip chunking - they're already concise
            # Chunking would split coherent information unnecessarily
            if document.document_type == "link" and "link_summary" in document.metadata:
                chunks = [content]  # Single chunk = full summary
                logger.info(f"Skipping chunking for link summary (keeping as single memory)")
            else:
                chunks = self.chunk_text(content)
                logger.info(f"Created {len(chunks)} chunks from document")
            
            # Update status: EMBEDDING
            document.status = DocumentStatus.EMBEDDING
            embeddings = self.embedding_service.embed_batch(chunks)
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            
            # Create memories
            memories = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Extract entities from chunk
                entities_dict = self.entity_service.extract_entities(chunk)
                entities_list = []
                for entity_type, entity_set in entities_dict.items():
                    entities_list.extend(entity_set)
                
                memory = Memory(
                    user_id=document.user_id,
                    content=chunk,
                    document_id=document.id,
                    chunk_index=idx,
                    embedding=embedding,
                    embedding_model=settings.embedding_model,
                    keywords=self.extract_keywords(chunk),
                    entities=entities_list,
                    metadata={
                        "source": document.source,
                        "document_type": document.document_type,
                        "title": document.title,
                        "entities_by_type": {k: list(v) for k, v in entities_dict.items()}
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
            
            # Classify memories into hot/cold tiers
            for memory in memories:
                tier = self.memory_tiering.classify_memory(memory)
                if tier == 'hot':
                    self.memory_tiering.add_to_hot(memory)
                else:
                    self.memory_tiering.add_to_cold(memory)
            
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
        
        user_id = new_memories[0].user_id if new_memories else None
        existing_memories = self.graph_store.get_all_memories(user_id=user_id)
        
        for new_memory in new_memories:
            # Search for similar existing memories
            if not new_memory.embedding:
                continue
            
            similar_results = self.vector_store.search(
                query_vector=new_memory.embedding,
                limit=5,
                score_threshold=0.55,  # Only consider somewhat similar memories
                user_id=new_memory.user_id,
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
    
    def _clamp_confidence(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return max(0.0, min(1.0, float(value)))

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
                    user_id=new_memory.user_id,
                    from_memory_id=new_memory.id,
                    to_memory_id=existing_memory.id,
                    relationship_type=RelationshipType.UPDATES,
                    confidence=self._clamp_confidence(similarity_score),
                    similarity_score=similarity_score,
                    reason=f"New information updates/contradicts existing (similarity: {similarity_score:.2f})"
                )
            else:
                # Very similar but not contradictory = similar reference
                return MemoryRelationship(
                    user_id=new_memory.user_id,
                    from_memory_id=new_memory.id,
                    to_memory_id=existing_memory.id,
                    relationship_type=RelationshipType.SIMILAR,
                    confidence=self._clamp_confidence(similarity_score),
                    similarity_score=similarity_score,
                    reason=f"Highly similar content (similarity: {similarity_score:.2f})"
                )
        
        # Medium similarity = likely extends or adds context
        elif similarity_score >= settings.similarity_threshold_extend:
            # Check if it's actually an extension or just related
            # If new memory is much longer, it might be an extension
            if len(new_memory.content) > len(existing_memory.content) * 1.5:
                 return MemoryRelationship(
                    user_id=new_memory.user_id,
                    from_memory_id=new_memory.id,
                    to_memory_id=existing_memory.id,
                    relationship_type=RelationshipType.EXTENDS,
                    confidence=self._clamp_confidence(similarity_score),
                    similarity_score=similarity_score,
                    reason=f"Expands on previous information (similarity: {similarity_score:.2f})"
                )
            
            return MemoryRelationship(
                user_id=new_memory.user_id,
                from_memory_id=new_memory.id,
                to_memory_id=existing_memory.id,
                relationship_type=RelationshipType.SIMILAR,
                confidence=self._clamp_confidence(similarity_score),
                similarity_score=similarity_score,
                reason=f"Related content (similarity: {similarity_score:.2f})"
            )
        
        # Lower similarity but still relevant = similar/related
        else:
            return MemoryRelationship(
                user_id=new_memory.user_id,
                from_memory_id=new_memory.id,
                to_memory_id=existing_memory.id,
                relationship_type=RelationshipType.SIMILAR,
                confidence=self._clamp_confidence(similarity_score),
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
        Detect DERIVES relationships using entity-based analysis.
        
        DERIVES relationships are created when:
        1. Shared entities (persons, organizations, locations) exist
        2. Keyword overlap is significant (>= 0.3)
        3. Memories are not already related by UPDATES/EXTENDS
        
        This is more accurate than keyword-only matching.
        """
        user_id = new_memories[0].user_id if new_memories else None
        all_memories = self.graph_store.get_all_memories(user_id=user_id)
        
        for new_memory in new_memories:
            # Extract entities from new memory
            new_entities = self.entity_service.extract_entities(new_memory.content)
            new_keywords = set(new_memory.keywords)
            
            for existing_memory in all_memories:
                if existing_memory.id == new_memory.id:
                    continue
                
                # Check if already related
                existing_relationships = self.graph_store.get_relationships(
                    new_memory.id,
                    direction="both",
                    user_id=user_id,
                )
                already_related = any(
                    rel.to_memory_id == existing_memory.id or rel.from_memory_id == existing_memory.id
                    for rel in existing_relationships
                )
                
                if already_related:
                    continue
                
                # Extract entities from existing memory
                existing_entities = self.entity_service.extract_entities(existing_memory.content)
                existing_keywords = set(existing_memory.keywords)
                
                # Calculate entity-based similarity
                entity_similarity = self.entity_service.calculate_entity_similarity(
                    new_entities, existing_entities
                )
                
                # Get shared entities for reasoning
                shared_entities = self.entity_service.get_shared_entities(
                    new_entities, existing_entities
                )
                
                # Calculate keyword overlap
                common_keywords = new_keywords.intersection(existing_keywords)
                keyword_overlap = (
                    len(common_keywords) / max(len(new_keywords), len(existing_keywords))
                    if max(len(new_keywords), len(existing_keywords)) > 0 else 0.0
                )
                
                # DERIVES criteria:
                # - Entity similarity > 0.2 (shared entities)
                # - OR keyword overlap >= 0.2
                should_derive = entity_similarity > 0.2 or keyword_overlap >= 0.2
                
                if should_derive:
                    # Combined confidence: weight entity similarity higher
                    confidence = (entity_similarity * 0.6) + (keyword_overlap * 0.4)
                    
                    # Build reason with entity information
                    reason_parts = []
                    if entity_similarity > 0.2:
                        # Collect non-empty entity types
                        entity_types_shared = [
                            entity_type for entity_type, entities in shared_entities.items()
                            if entities
                        ]
                        if entity_types_shared:
                            reason_parts.append(f"Shared entities: {', '.join(entity_types_shared)}")
                    
                    if keyword_overlap >= 0.3:
                        reason_parts.append(f"Keyword overlap: {keyword_overlap:.2f}")
                    
                    reason = "; ".join(reason_parts) if reason_parts else "Entity-based derivation"
                    
                    relationship = MemoryRelationship(
                        user_id=new_memory.user_id,
                        from_memory_id=new_memory.id,
                        to_memory_id=existing_memory.id,
                        relationship_type=RelationshipType.DERIVES,
                        confidence=self._clamp_confidence(confidence),
                        similarity_score=None,
                        reason=reason
                    )
                    
                    self.graph_store.add_relationship(relationship)
                    logger.debug(
                        f"Created DERIVES relationship: {new_memory.id} -> {existing_memory.id} "
                        f"(entity_sim: {entity_similarity:.2f}, keyword_overlap: {keyword_overlap:.2f})"
                    )
    
    async def ingest_entry(
        self,
        *,
        user_id: str,
        entry_type: str,
        title: Optional[str],
        description: Optional[str],
        note_content: Optional[str],
        link_url: Optional[str],
        upload_file: Optional[UploadFile],
        explicit_source: Optional[str] = None,
    ) -> Document:
        """Normalize note/link/file submissions into a document."""
        entry_type = (entry_type or "note").lower()
        metadata = {
            "ingest_type": entry_type,
            "description": description or "",
        }

        summary_text: Optional[str] = None
        summary_warning: Optional[str] = None
        original_text: Optional[str] = None

        if entry_type == "note":
            if not note_content or not note_content.strip():
                raise ValueError("Content is required when type=note")
            text = note_content.strip()
            original_text = text
            source = explicit_source or "user_note"
        elif entry_type == "link":
            if not link_url:
                raise ValueError("URL is required when type=link")
            text, link_metadata = await self.content_loader.fetch_link(link_url)
            metadata.update(link_metadata)
            original_text = text
            source = explicit_source or link_url
            if self.summarizer:
                try:
                    summary_text = await self.summarizer.summarize(text)
                except SummarizationError as exc:
                    summary_warning = str(exc)
        elif entry_type in {"file", "upload"}:
            if upload_file is None:
                raise ValueError("File is required when type=file")
            text, file_metadata = await self.content_loader.extract_file(upload_file)
            metadata.update(file_metadata)
            original_text = text
            source = explicit_source or file_metadata.get("file_name")
            entry_type = "file"
        else:
            raise ValueError(f"Unsupported ingest type '{entry_type}'")

        original_text = original_text or text
        if summary_text:
            metadata["link_summary"] = summary_text
            metadata["original_excerpt"] = (original_text or "")[:1500]
            text = summary_text.strip()
        elif summary_warning:
            metadata["summary_warning"] = summary_warning

        text = (text or "").strip()
        if entry_type == "link" and len(text) < 10:
            text = (original_text or "")[:1000] or f"Link reference: {link_url}"
        
        # Prepend URL to content for link types so it's included in embeddings
        if entry_type == "link" and link_url:
            text = f"Source URL: {link_url}\n\n{text}"
        if len(text) < 10:
            raise ValueError("Content too short. Please provide at least 10 characters.")
        if len(text) > 1_000_000:
            raise ValueError("Content too large. Maximum size is 1MB of text.")

        document = Document(
            user_id=user_id,
            content=text,
            title=title,
            description=summary_text or description or summary_warning,
            source=source,
            document_type=entry_type,
            metadata=metadata,
        )

        await self.process_document(document)
        return document

    async def ingest_text(
        self,
        text: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Document:
        """Convenience wrapper for ingesting raw text."""
        if not user_id:
            raise ValueError("user_id is required to ingest documents")
        return await self.ingest_entry(
            user_id=user_id,
            entry_type="note",
            title=title,
            description=None,
            note_content=text,
            link_url=None,
            upload_file=None,
            explicit_source=source,
        )


# Global instance
_ingestion_service = None


def get_ingestion_service() -> IngestionService:
    """Get singleton ingestion service instance"""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service

