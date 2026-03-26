"""
NER Extraction Module

Named Entity Recognition and information extraction utilities.
Supports custom NER models and integrates with Azure Language / Pakman NLP.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None


class EntityType(Enum):
    """Standard entity types"""
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    DATE_TIME = "DATE_TIME"
    QUANTITY = "QUANTITY"
    URL = "URL"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    IP_ADDRESS = "IP_ADDRESS"
    CUSTOM = "CUSTOM"


@dataclass
class Entity:
    """Represents a recognized entity"""
    text: str
    entity_type: str
    subtype: Optional[str] = None
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class ExtractionResult:
    """Result from entity extraction"""
    text: str
    entities: List[Entity]
    full_response: Optional[Dict] = None


class NERExtractor:
    """
    Base NER extractor interface.
    
    Usage:
        extractor = NERExtractor()
        
        # Extract entities
        result = extractor.extract("Microsoft was founded by Bill Gates in 1975.")
        for entity in result.entities:
            print(f"{entity.text} -> {entity.entity_type}")
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self._model = None
    
    def extract(self, text: str) -> ExtractionResult:
        """
        Extract entities from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            ExtractionResult with recognized entities
        """
        raise NotImplementedError("Subclass must implement extract()")
    
    def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        """Extract entities from multiple texts."""
        return [self.extract(text) for text in texts]
    
    def _create_entity(self, text: str, entity_type: str, 
                       subtype: str = None, confidence: float = 1.0,
                       start: int = 0, end: int = 0) -> Entity:
        """Helper to create Entity objects"""
        return Entity(
            text=text,
            entity_type=entity_type,
            subtype=subtype,
            confidence=confidence,
            start_pos=start,
            end_pos=end
        )


class RegexNERExtractor(NERExtractor):
    """
    Rule-based NER using regex patterns.
    Fast but limited coverage.
    """
    
    def __init__(self):
        super().__init__()
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for common entity types"""
        import re
        
        self.patterns = {
            EntityType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            EntityType.URL: re.compile(
                r'https?://[^\s]+'
            ),
            EntityType.PHONE: re.compile(
                r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
            ),
            EntityType.IP_ADDRESS: re.compile(
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ),
            EntityType.DATE_TIME: re.compile(
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
            ),
        }
    
    def extract(self, text: str) -> ExtractionResult:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entity = self._create_entity(
                    text=match.group(),
                    entity_type=entity_type.value,
                    confidence=1.0,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)
        
        return ExtractionResult(text=text, entities=entities)


class SimpleNLPNERExtractor(NERExtractor):
    """
    Simple NLP-based NER using spaCy or similar.
    Requires spaCy to be installed.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        super().__init__()
        self._load_model(model_name)
    
    def _load_model(self, model_name: str):
        """Load spaCy model"""
        try:
            import spacy
            self._nlp = spacy.load(model_name)
        except (ImportError, OSError):
            print("spaCy not available, falling back to RegexNERExtractor")
            self._nlp = None
    
    def extract(self, text: str) -> ExtractionResult:
        """Extract entities using spaCy"""
        if self._nlp is None:
            return RegexNERExtractor().extract(text)
        
        doc = self._nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity = self._create_entity(
                text=ent.text,
                entity_type=ent.label_,
                confidence=1.0,
                start=ent.start_char,
                end=ent.end_char
            )
            entities.append(entity)
        
        return ExtractionResult(text=text, entities=entities)
    
    def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        """Extract entities using spaCy pipe for efficiency"""
        if self._nlp is None:
            return [RegexNERExtractor().extract(text) for text in texts]
        
        results = []
        for doc in self._nlp.pipe(texts):
            entities = [
                self._create_entity(
                    text=ent.text,
                    entity_type=ent.label_,
                    confidence=1.0,
                    start=ent.start_char,
                    end=ent.end_char
                )
                for ent in doc.ents
            ]
            results.append(ExtractionResult(text=doc.text, entities=entities))
        
        return results


class AzureLanguageNERExtractor(NERExtractor):
    """
    Azure Language NER integration.
    Requires azure-ai-textanalytics package.
    
    Usage:
        from azure.core.credentials import AzureKeyCredential
        from azure.ai.textanalytics import TextAnalyticsClient
        
        credential = AzureKeyCredential(key)
        client = TextAnalyticsClient(endpoint=endpoint, credential=credential)
        
        extractor = AzureLanguageNERExtractor(client)
        result = extractor.extract("Bill Gates works at Microsoft.")
    """
    
    def __init__(self, client):
        logger.info("Initializing Azure NER extractor")
        super().__init__()
        self._client = client
    
    def extract(self, text: str) -> ExtractionResult:
        """Extract entities using Azure Language"""
        try:
            from azure.ai.textanalytics import recognize_entities
        except ImportError:
            return ExtractionResult(text=text, entities=[])
        
        response = self._client.recognize_entities(text)[0]
        entities = []
        
        for entity in response.entities:
            ent = self._create_entity(
                text=entity.text,
                entity_type=entity.category,
                subtype=entity.subcategory or None,
                confidence=entity.confidence_score,
                start=entity.offset,
                end=entity.offset + len(entity.text)
            )
            entities.append(ent)
        
        return ExtractionResult(text=text, entities=entities, full_response=response.as_dict())


class PakmanNERExtractor(NERExtractor):
    """
    Pakman NLP integration for NER.
    Wrapper around pakman.nlp.ner.
    """
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        super().__init__()
        self._api_base = api_base.rstrip('/')
    
    def extract(self, text: str) -> ExtractionResult:
        """Extract entities using Pakman NER API"""
        try:
            import requests
            
            response = requests.post(
                f"{self._api_base}/ner",
                json={"text": text},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                entities = []
                
                for ent in data.get("entities", []):
                    entity = self._create_entity(
                        text=ent.get("text", ""),
                        entity_type=ent.get("type", "CUSTOM"),
                        subtype=ent.get("subtype"),
                        confidence=ent.get("confidence", 1.0)
                    )
                    entities.append(entity)
                
                logger.info(f"Pakman NER extracted {len(entities)} entities")
                return ExtractionResult(text=text, entities=entities, full_response=data)
            
            logger.warning("Pakman NER returned no entities")
            return ExtractionResult(text=text, entities=[])
            
        except Exception as e:
            logger.error(f"Pakman NER error: {e}")
            return ExtractionResult(text=text, entities=[])


class NERPipeline:
    """
    Pipeline that chains multiple NER extractors.
    Results are merged with deduplication.
    """
    
    def __init__(self, extractors: List[NERExtractor] = None):
        self.extractors = extractors or [RegexNERExtractor()]
    
    def add_extractor(self, extractor: NERExtractor):
        """Add an extractor to the pipeline"""
        self.extractors.append(extractor)
    
    def extract(self, text: str) -> ExtractionResult:
        """Extract entities using all extractors and merge results"""
        all_entities = []
        seen = set()
        
        for extractor in self.extractors:
            result = extractor.extract(text)
            
            for entity in result.entities:
                # Deduplicate by text and type
                key = (entity.text.lower(), entity.entity_type)
                
                if key not in seen:
                    seen.add(key)
                    all_entities.append(entity)
        
        return ExtractionResult(text=text, entities=all_entities)
    
    def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        """Process multiple texts through pipeline"""
        return [self.extract(text) for text in texts]


# Entity linking utilities
class EntityLinker:
    """
    Link extracted entities to knowledge bases (e.g., Wikipedia).
    """
    
    def __init__(self, knowledge_base: str = "wikipedia"):
        self.knowledge_base = knowledge_base
    
    def link(self, entity: Entity) -> Optional[Dict[str, str]]:
        """
        Link entity to knowledge base.
        
        Returns:
            Dict with 'id', 'name', 'url' if linked, None otherwise
        """
        if self.knowledge_base == "wikipedia":
            return self._link_wikipedia(entity)
        return None
    
    def _link_wikipedia(self, entity: Entity) -> Optional[Dict[str, str]]:
        """Link entity to Wikipedia"""
        # In production, use Wikipedia API
        # This is a simplified placeholder
        search_term = entity.text.replace(" ", "+")
        url = f"https://en.wikipedia.org/wiki/{search_term}"
        
        return {
            "id": search_term,
            "name": entity.text,
            "url": url
        }


# Convenience factory function
def create_ner_extractor(extractor_type: str = "spacy", **kwargs) -> NERExtractor:
    """
    Factory function to create NER extractors.
    
    Args:
        extractor_type: One of 'regex', 'spacy', 'azure', 'pakman'
        **kwargs: Additional arguments for the extractor
    
    Returns:
        NERExtractor instance
    """
    extractors = {
        "regex": RegexNERExtractor,
        "spacy": SimpleNLPNERExtractor,
        "azure": AzureLanguageNERExtractor,
        "pakman": PakmanNERExtractor,
    }
    
    extractor_class = extractors.get(extractor_type.lower())
    
    if not extractor_class:
        raise ValueError(f"Unknown extractor type: {extractor_type}")
    
    return extractor_class(**kwargs)
