"""Entity extraction and NER service for relationship detection"""

from typing import List, Set, Dict, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class EntityService:
    """
    Extracts named entities from text for relationship detection.
    Uses pattern-based NER (simple but effective for most use cases).
    Can be extended with spaCy or transformers for advanced NER.
    """
    
    def __init__(self):
        """Initialize entity service with common patterns"""
        # Patterns for entity detection
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://[^\s]+',
            'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            'date': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
            'number': r'\b\d+(?:\.\d+)?\b',
        }
        
        # Common entity keywords (simple heuristic)
        self.person_indicators = {
            'mr', 'ms', 'mrs', 'dr', 'prof', 'ceo', 'cto', 'founder',
            'author', 'engineer', 'manager', 'director', 'president'
        }
        
        self.org_indicators = {
            'inc', 'corp', 'ltd', 'llc', 'company', 'organization',
            'university', 'institute', 'bank', 'hospital', 'agency'
        }
        
        self.location_indicators = {
            'city', 'town', 'state', 'country', 'region', 'province',
            'district', 'avenue', 'street', 'road', 'boulevard'
        }

        self.product_indicators = {
            'mouse', 'keyboard', 'laptop', 'headset', 'monitor', 'screen',
            'sensor', 'dpi', 'wireless', 'bluetooth', 'usb', 'ergonomic',
            'gaming', 'productivity', 'device', 'hardware'
        }
    
    def extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with entity types as keys and sets of entities as values
        """
        entities = {
            'emails': set(),
            'urls': set(),
            'phones': set(),
            'dates': set(),
            'numbers': set(),
            'persons': set(),
            'organizations': set(),
            'locations': set(),
            'products': set(),  # New category
            'keywords': set()
        }
        
        # Extract pattern-based entities
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if entity_type == 'email':
                entities['emails'].update(matches)
            elif entity_type == 'url':
                entities['urls'].update(matches)
            elif entity_type == 'phone':
                entities['phones'].update([m[0] + m[1] + m[2] if isinstance(m, tuple) else m for m in matches])
            elif entity_type == 'date':
                entities['dates'].update(matches)
            elif entity_type == 'number':
                entities['numbers'].update(matches)
        
        # Extract capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Classify capitalized words
        for word in capitalized:
            word_lower = word.lower()
            
            # Check for person indicators
            if any(indicator in word_lower for indicator in self.person_indicators):
                entities['persons'].add(word)
            # Check for organization indicators
            elif any(indicator in word_lower for indicator in self.org_indicators):
                entities['organizations'].add(word)
            # Check for location indicators
            elif any(indicator in word_lower for indicator in self.location_indicators):
                entities['locations'].add(word)
            # Check for product indicators
            elif any(indicator in word_lower for indicator in self.product_indicators):
                entities['products'].add(word)
            # Generic proper noun
            else:
                entities['keywords'].add(word)
        
        # Also scan for product keywords in lowercase text to catch things like "mouse"
        text_lower = text.lower()
        for indicator in self.product_indicators:
            if indicator in text_lower:
                entities['products'].add(indicator)
        
        return entities
    
    def get_entity_overlap(
        self,
        entities1: Dict[str, Set[str]],
        entities2: Dict[str, Set[str]]
    ) -> Dict[str, Tuple[Set[str], float]]:
        """
        Calculate entity overlap between two entity dictionaries.
        
        Args:
            entities1: First entity dictionary
            entities2: Second entity dictionary
            
        Returns:
            Dictionary with entity types and their overlap info:
            {entity_type: (common_entities, overlap_score)}
        """
        overlap = {}
        
        for entity_type in entities1.keys():
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())
            
            if not set1 or not set2:
                overlap[entity_type] = (set(), 0.0)
                continue
            
            common = set1 & set2
            union = set1 | set2
            
            # Jaccard similarity
            similarity = len(common) / len(union) if union else 0.0
            overlap[entity_type] = (common, similarity)
        
        return overlap
    
    def calculate_entity_similarity(
        self,
        entities1: Dict[str, Set[str]],
        entities2: Dict[str, Set[str]]
    ) -> float:
        """
        Calculate overall entity similarity between two texts.
        Weights: persons=0.3, organizations=0.3, locations=0.2, others=0.2
        
        Args:
            entities1: First entity dictionary
            entities2: Second entity dictionary
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        weights = {
            'persons': 0.25,
            'organizations': 0.25,
            'locations': 0.15,
            'products': 0.25,  # High weight for products
            'emails': 0.05,
            'urls': 0.05,
            'phones': 0.05,
            'dates': 0.0,
            'numbers': 0.0,
            'keywords': 0.1
        }
        
        overlap = self.get_entity_overlap(entities1, entities2)
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for entity_type, (common, similarity) in overlap.items():
            weight = weights.get(entity_type, 0.0)
            if weight > 0:
                weighted_score += similarity * weight
                total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def get_shared_entities(
        self,
        entities1: Dict[str, Set[str]],
        entities2: Dict[str, Set[str]]
    ) -> Dict[str, Set[str]]:
        """
        Get all shared entities between two entity dictionaries.
        
        Args:
            entities1: First entity dictionary
            entities2: Second entity dictionary
            
        Returns:
            Dictionary with shared entities by type
        """
        shared = {}
        
        for entity_type in entities1.keys():
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())
            shared[entity_type] = set1 & set2
        
        return shared


# Global instance
_entity_service = None


def get_entity_service() -> EntityService:
    """Get singleton entity service instance"""
    global _entity_service
    if _entity_service is None:
        _entity_service = EntityService()
    return _entity_service
